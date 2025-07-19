from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import yfinance as yf
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from db import DB_Config, DB_Manager
from utils import Logger

logger = Logger.setup_logger(__name__)

stocks_bp = Blueprint('stocks', __name__, template_folder='templates')

@stocks_bp.route('/', methods=['GET', 'POST'])
@login_required
def stocks():
    try:
        cursor = DB_Config.get_cursor()
        
        # SQL query to get stocks for the current user from their watchlist
        query = """
            SELECT s.name, s.company, s.price, s.trading_volume, s.avg_trading_volume
            FROM stocks s
            JOIN user_stocks_watchlist w ON s.id = w.stock_id
            WHERE w.user_id = %s
            ORDER BY s.price DESC;
        """
        
        cursor.execute(query, (current_user.id,))
        
        stocks_data = []
        columns = [desc[0] for desc in cursor.description]
        for stock in cursor.fetchall():
            stocks_data.append(dict(zip(columns, stock)))
            
        cursor.close()
        return render_template("stocks.html", stocks=stocks_data)
        
    except Exception as e:
        logger.error(f"Error fetching user's stocks: {e}")
        return render_template("stocks.html", stocks=[], error="Could not load your watchlist.")

@stocks_bp.route('/pick', methods=['POST'])
@login_required
def pick_stock():
    ticker = request.form.get('ticker', '').upper()
    
    if not ticker:
        flash('Please enter a stock ticker.', 'error')
        return redirect(url_for('stocks.stocks'))

    data_provider = YFinanceProvider()
    
    # Step 1: Validate the stock ticker first
    if not data_provider.is_valid_ticker(ticker):
        flash(f'Invalid or unrecognized stock ticker: {ticker}', 'error')
        return redirect(url_for('stocks.stocks'))
        
    try:
        cursor = DB_Config.get_cursor()
        db_manager = DB_Manager(cursor)
        
        # Step 2: Check if the stock exists in the main 'stocks' table
        cursor.execute("SELECT id FROM stocks WHERE name = %s", (ticker,))
        stock_row = cursor.fetchone()
        
        stock_id = None
        if not stock_row:
            # Stock is not in our database, so add it.
            # We know it's valid, so we can now fetch its full info.
            stock_adder = Stock(ticker, data_provider, db_manager)
            stock_adder.add_stock() # Re-using the original add_stock method
            
            # Get the new ID
            cursor.execute("SELECT id FROM stocks WHERE name = %s", (ticker,))
            new_stock_row = cursor.fetchone()
            if new_stock_row:
                stock_id = new_stock_row[0]
        else:
            # Stock already exists, just get its ID
            stock_id = stock_row[0]

        if not stock_id:
            raise Exception("Failed to find or create a stock_id.")

        user_id = current_user.id
        
        # Step 3: Add the stock to the user's personal watchlist
        cursor.execute(
            "SELECT * FROM user_stocks_watchlist WHERE user_id = %s AND stock_id = %s",
            (user_id, stock_id)
        )
        if cursor.fetchone():
            flash(f'Stock {ticker} is already in your watchlist.', 'info')
        else:
            cursor.execute(
                "INSERT INTO user_stocks_watchlist (user_id, stock_id) VALUES (%s, %s)",
                (user_id, stock_id)
            )
            flash(f'Successfully added {ticker} to your watchlist!', 'success')
            
        cursor.connection.commit()
        
    except Exception as e:
        logger.error(f"Error processing stock {ticker} for user {current_user.id}: {e}")
        if 'cursor' in locals() and cursor:
            cursor.connection.rollback()
        flash(f'An error occurred while processing the stock. Please try again.', 'error')
        
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
            
    return redirect(url_for('stocks.stocks'))

@dataclass
class StockData:
    """Data class to hold stock information"""
    company: str
    name: str 
    price: float
    trading_volume: int
    avg_trading_volume: float

class StockDataError(Exception):
    """Custom exception for stock data related errors"""
    pass

class StockDataProvider(ABC):
    """Abstract base class for stock data providers"""
    
    @abstractmethod
    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def is_valid_ticker(self, ticker: str) -> bool:
        """Validate if ticker exists and has required data"""
        pass

class YFinanceProvider(StockDataProvider):
    """YFinance implementation of stock data provider"""
    
    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            return stock.info
        except Exception:
            return {}

    def is_valid_ticker(self, ticker: str) -> bool:
        """
        Validates a ticker by fetching its info and checking for a key field.
        An empty history or lack of a 'shortName' often indicates an invalid ticker.
        """
        if not ticker:
            return False
        try:
            stock = yf.Ticker(ticker)
            # A valid ticker from yfinance will have a non-empty info dictionary
            # and usually a 'shortName' for actual companies.
            if stock.info and stock.info.get('shortName'):
                return True
            # Check for history as a fallback for some assets
            if not stock.history(period="5d").empty:
                return True
            return False
        except Exception:
            return False

class Stock:
    """Class for managing individual stock operations"""
    
    def __init__(self, ticker: str, data_provider: StockDataProvider, db_manager: DB_Manager):
        self.ticker = ticker
        self.data_provider = data_provider
        self.db_manager = db_manager
        
    def add_stock(self) -> None:
        """Add stock to database with current market data"""
        try:
            info = self.data_provider.get_stock_info(self.ticker)
            
            required_fields = {
                'shortName': 'company',
                'currentPrice': 'price', 
                'volume': 'trading_volume',
                'averageVolume': 'avg_trading_volume'
            }
            
            data = {field: info.get(key) for key, field in required_fields.items()}
            data['name'] = self.ticker
            
            if not all(data.get(key) is not None for key in ['company', 'price']):
                raise StockDataError(f"Missing required data for {self.ticker}")

            with self.db_manager.transaction():
                self.db_manager.insert_record('stocks', data)
            logger.info(f"Stock {self.ticker} added successfully.")
            
        except (StockDataError, Exception) as e:
            logger.error(f"Error inserting {self.ticker}: {e}")
            raise
    
    def remove_stock(self) -> None:
        """Remove stock from database"""
        try:
            with self.db_manager.transaction():
                self.db_manager.delete_record('stocks', {'name': self.ticker})
            logger.info(f"Stock {self.ticker} removed successfully.")
        except Exception as e:
            logger.error(f"Error removing {self.ticker}: {e}")
            raise

    def update_stock(self) -> None:
        try:
            info = self.data_provider.get_stock_info(self.ticker)
            update_data = {
                'price': info.get('currentPrice'),
                'trading_volume': info.get('volume'),
                'avg_trading_volume': info.get('averageVolume')
            }
            with self.db_manager.transaction():
                self.db_manager.update_record('stocks', update_data, {'name': self.ticker})
            logger.info(f"Stock {self.ticker} updated successfully.")
        except Exception as e:
            logger.error(f"Error updating {self.ticker}: {e}")
            raise    
            
