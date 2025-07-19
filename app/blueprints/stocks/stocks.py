from flask import Blueprint, render_template, request, redirect, url_for
import yfinance as yf
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from db import DB_Config, DB_Manager
from utils import Logger

logger = Logger.setup_logger(__name__)

stocks_bp = Blueprint('stocks', __name__, template_folder='templates')

@stocks_bp.route('/', methods=['GET', 'POST'])
def stocks():
    try:
        cursor = DB_Config.get_cursor()
        cursor.execute("SELECT * FROM stocks ORDER BY price DESC")
        stocks = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        stocks_data = [dict(zip(columns, stock)) for stock in stocks]
        cursor.close()
        return render_template("stocks.html", stocks=stocks_data)
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        return render_template("stocks.html", stocks=[])

@stocks_bp.route('/pick', methods=['POST'])
def pick_stock():
    ticker = request.form.get('ticker', '').upper()
    
    if not ticker:
        return redirect(url_for('stocks.stocks', 
                              message='Please enter a stock ticker',
                              success='false'))
    
    data_provider = YFinanceProvider()
    if not data_provider.is_valid_ticker(ticker):
        return redirect(url_for('stocks.stocks',
                              message=f'Invalid stock ticker: {ticker}',
                              success='false'))
    
    try:
        cursor = DB_Config.get_cursor()
        stock = Stock(ticker, data_provider, DB_Manager(cursor))
        stock.add_stock()
        cursor.connection.commit()
        cursor.close()
        return redirect(url_for('stocks.stocks',
                              message=f'Successfully added stock: {ticker}',
                              success='true'))
    except Exception as e:
        logger.error(f"Error adding stock {ticker}: {e}")
        if cursor:
            cursor.connection.rollback()
            cursor.close()
        return redirect(url_for('stocks.stocks',
                              message=f'Error adding stock: {str(e)}',
                              success='false'))

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
        except Exception as e:
            raise StockDataError(f"Failed to fetch data for {ticker}: {e}")

    def is_valid_ticker(self, ticker: str) -> bool:
        """Validate if ticker exists and has required data"""
        try:
            stock = yf.Ticker(ticker)
            return 'shortName' in stock.info
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
            
            if not all(data.values()):
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
            
