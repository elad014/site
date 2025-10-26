from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import yfinance as yf  
from alpha_vantage.timeseries import TimeSeries  
from alpha_vantage.fundamentaldata import FundamentalData  
import os
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from db.db import DB_Config, DB_Manager
from utils.utils import Logger

logger = Logger.setup_logger(__name__)

stocks_bp = Blueprint('stocks', __name__, template_folder='templates')

# Alpha Vantage API Configuration
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'YOUR_API_KEY_HERE')  # Set your API key
RATE_LIMIT_DELAY = 12  # Alpha Vantage free tier: 5 requests per minute

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
    print(f"=== DEBUG: PICK STOCK ATTEMPT FOR {ticker} ===")
    print(f"DEBUG: Raw form ticker: {request.form.get('ticker')}")
    print(f"DEBUG: Processed ticker: {ticker}")
    
    if not ticker:
        print("DEBUG: No ticker provided")
        flash('Please enter a stock ticker.', 'error')
        return redirect(url_for('stocks.stocks'))

    print("DEBUG: Creating AlphaVantageProvider...")
    data_provider = AlphaVantageProvider()
    
    # Step 1: Validate the stock ticker first
    print(f"DEBUG: Validating ticker {ticker}...")
    is_valid = data_provider.is_valid_ticker(ticker)
    print(f"DEBUG: Validation result: {is_valid}")
    
    if not is_valid:
        print(f"DEBUG: Ticker {ticker} failed validation")
        flash(f'Invalid or unrecognized stock ticker: {ticker}', 'error')
        return redirect(url_for('stocks.stocks'))
        
    print(f"DEBUG: Ticker {ticker} passed validation, proceeding...")
    try:
        print("DEBUG: Getting database cursor...")
        cursor = DB_Config.get_cursor()
        db_manager = DB_Manager(cursor)
        
        # Step 2: Check if the stock exists in the main 'stocks' table
        print(f"DEBUG: Checking if {ticker} exists in database...")
        cursor.execute("SELECT id FROM stocks WHERE name = %s", (ticker,))
        stock_row = cursor.fetchone()
        print(f"DEBUG: Existing stock row: {stock_row}")
        
        stock_id = None
        if not stock_row:
            print(f"DEBUG: Stock {ticker} not in database, adding it...")
            # Stock is not in our database, so add it.
            # We know it's valid, so we can now fetch its full info.
            stock_adder = Stock(ticker, data_provider, db_manager)
            stock_adder.add_stock() # Re-using the original add_stock method
            print(f"DEBUG: Stock {ticker} added to database")
            
            # Get the new ID
            cursor.execute("SELECT id FROM stocks WHERE name = %s", (ticker,))
            new_stock_row = cursor.fetchone()
            if new_stock_row:
                stock_id = new_stock_row[0]
                print(f"DEBUG: New stock ID: {stock_id}")
        else:
            # Stock already exists, just get its ID
            stock_id = stock_row[0]
            print(f"DEBUG: Using existing stock ID: {stock_id}")

        if not stock_id:
            print(f"DEBUG ERROR: Failed to get stock_id for {ticker}")
            raise Exception("Failed to find or create a stock_id.")

        user_id = current_user.id
        print(f"DEBUG: Current user ID: {user_id}")
        
        # Step 3: Add the stock to the user's personal watchlist
        print(f"DEBUG: Checking if {ticker} already in user's watchlist...")
        cursor.execute(
            "SELECT * FROM user_stocks_watchlist WHERE user_id = %s AND stock_id = %s",
            (user_id, stock_id)
        )
        existing_watchlist = cursor.fetchone()
        print(f"DEBUG: Existing watchlist entry: {existing_watchlist}")
        
        if existing_watchlist:
            print(f"DEBUG: Stock {ticker} already in watchlist")
            flash(f'Stock {ticker} is already in your watchlist.', 'info')
        else:
            print(f"DEBUG: Adding {ticker} to user's watchlist...")
            cursor.execute(
                "INSERT INTO user_stocks_watchlist (user_id, stock_id) VALUES (%s, %s)",
                (user_id, stock_id)
            )
            print(f"DEBUG: Successfully added {ticker} to watchlist")
            flash(f'Successfully added {ticker} to your watchlist!', 'success')
            
        cursor.connection.commit()
        print(f"DEBUG: Transaction committed for {ticker}")
        
    except Exception as e:
        print(f"DEBUG ERROR: Exception processing {ticker}: {e}")
        import traceback
        print(f"DEBUG ERROR: Traceback: {traceback.format_exc()}")
        logger.error(f"Error processing stock {ticker} for user {current_user.id}: {e}")
        if 'cursor' in locals() and cursor:
            cursor.connection.rollback()
            print("DEBUG: Transaction rolled back")
        flash(f'An error occurred while processing the stock. Please try again.', 'error')
        
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
            print("DEBUG: Database cursor closed")
    
    print(f"=== END DEBUG PICK STOCK FOR {ticker} ===")        
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

class AlphaVantageProvider(StockDataProvider):
    """Alpha Vantage implementation of stock data provider - More reliable than Yahoo Finance"""
    
    def __init__(self):
        self.ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
        self.fd = FundamentalData(key=ALPHA_VANTAGE_API_KEY, output_format='json')
        self.request_count = 0
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting for Alpha Vantage API (5 requests per minute for free tier)"""
        current_time = time.time()
        if current_time - self.last_request_time < RATE_LIMIT_DELAY:
            sleep_time = RATE_LIMIT_DELAY - (current_time - self.last_request_time)
            print(f"DEBUG: Rate limiting - sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
        self.request_count += 1

    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """Get comprehensive stock information from Alpha Vantage"""
        print(f"=== DEBUG: GETTING ALPHA VANTAGE INFO FOR {ticker} ===")
        try:
            self._rate_limit()
            
            # Get company overview (most comprehensive data)
            print(f"DEBUG: Fetching company overview for {ticker}")
            overview, _ = self.fd.get_company_overview(ticker)
            
            if not overview or 'Symbol' not in overview:
                print(f"DEBUG: No overview data found for {ticker}")
                return {}
            
            print(f"DEBUG: Overview data keys: {list(overview.keys())}")
            
            # Map Alpha Vantage fields to our expected format
            mapped_info = {
                'symbol': overview.get('Symbol'),
                'shortName': overview.get('Name'),
                'longName': overview.get('Name'),
                'currentPrice': self._safe_float(overview.get('Price')),
                'marketCap': self._safe_float(overview.get('MarketCapitalization')),
                'sector': overview.get('Sector'),
                'industry': overview.get('Industry'),
                'description': overview.get('Description'),
                'exchange': overview.get('Exchange'),
                'currency': overview.get('Currency'),
                'country': overview.get('Country'),
                # Calculate volume from market data if available
                'volume': 0,  # Will try to get from intraday data
                'averageVolume': 0,  # Will calculate from historical data
            }
            
            # Try to get current price and volume from intraday data
            try:
                print(f"DEBUG: Fetching intraday data for current price and volume")
                self._rate_limit()
                intraday_data, _ = self.ts.get_intraday(ticker, interval='1min', outputsize='compact')
                
                if not intraday_data.empty:
                    latest_data = intraday_data.iloc[-1]
                    mapped_info['currentPrice'] = float(latest_data['4. close'])
                    mapped_info['volume'] = int(float(latest_data['5. volume']))
                    print(f"DEBUG: Got current price from intraday: {mapped_info['currentPrice']}")
                    print(f"DEBUG: Got volume from intraday: {mapped_info['volume']}")
                
            except Exception as e:
                print(f"DEBUG: Could not get intraday data: {e}")
                # Fallback to daily data for price
                try:
                    print(f"DEBUG: Trying daily data as fallback")
                    self._rate_limit()
                    daily_data, _ = self.ts.get_daily(ticker, outputsize='compact')
                    
                    if not daily_data.empty:
                        latest_daily = daily_data.iloc[-1]
                        if not mapped_info['currentPrice']:
                            mapped_info['currentPrice'] = float(latest_daily['4. close'])
                        mapped_info['volume'] = int(float(latest_daily['5. volume']))
                        
                        # Calculate average volume from last 20 days
                        if len(daily_data) >= 20:
                            avg_vol = daily_data['5. volume'].astype(float).tail(20).mean()
                            mapped_info['averageVolume'] = int(avg_vol)
                        
                        print(f"DEBUG: Got price from daily data: {mapped_info['currentPrice']}")
                        print(f"DEBUG: Got average volume: {mapped_info['averageVolume']}")
                        
                except Exception as e2:
                    print(f"DEBUG: Could not get daily data either: {e2}")
            
            # Remove None values and clean data
            cleaned_info = {k: v for k, v in mapped_info.items() if v is not None and v != ''}
            
            print(f"DEBUG: Final mapped info: {cleaned_info}")
            return cleaned_info
            
        except Exception as e:
            print(f"DEBUG ERROR: Alpha Vantage API error for {ticker}: {e}")
            import traceback
            print(f"DEBUG ERROR: Traceback: {traceback.format_exc()}")
            return {}

    def _safe_float(self, value) -> Optional[float]:
        """Safely convert string to float"""
        if value is None or value == '' or value == 'None':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def is_valid_ticker(self, ticker: str) -> bool:
        """Validate ticker using Alpha Vantage company overview"""
        print(f"=== DEBUG: VALIDATING TICKER {ticker} WITH ALPHA VANTAGE ===")
        if not ticker:
            print("DEBUG: Empty ticker")
            return False
            
        try:
            self._rate_limit()
            print(f"DEBUG: Fetching company overview for validation")
            overview, _ = self.fd.get_company_overview(ticker)
            
            print(f"DEBUG: Overview response type: {type(overview)}")
            print(f"DEBUG: Overview keys: {list(overview.keys()) if isinstance(overview, dict) else 'Not a dict'}")
            
            # Check if we got valid company data
            if overview and isinstance(overview, dict):
                symbol = overview.get('Symbol')
                name = overview.get('Name')
                
                print(f"DEBUG: Symbol: {symbol}")
                print(f"DEBUG: Name: {name}")
                
                # Valid if we have both symbol and name
                if symbol and name and symbol.upper() == ticker.upper():
                    print(f"DEBUG: ✓ Valid ticker - Symbol: {symbol}, Name: {name}")
                    return True
                elif symbol and symbol.upper() == ticker.upper():
                    print(f"DEBUG: ✓ Valid ticker - Has symbol match: {symbol}")
                    return True
            
            print(f"DEBUG: ✗ Invalid ticker - No valid data returned")
            return False
            
        except Exception as e:
            print(f"DEBUG ERROR: Alpha Vantage validation error for {ticker}: {e}")
            import traceback
            print(f"DEBUG ERROR: Traceback: {traceback.format_exc()}")
            return False

class Stock:
    """Class for managing individual stock operations"""
    
    def __init__(self, ticker: str, data_provider: StockDataProvider, db_manager: DB_Manager):
        self.ticker = ticker
        self.data_provider = data_provider
        self.db_manager = db_manager
        
    def add_stock(self) -> None:
        """Add stock to database with current market data"""
        print(f"=== DEBUG: ADDING STOCK {self.ticker} ===")
        try:
            print(f"DEBUG: Fetching info for {self.ticker}")
            info = self.data_provider.get_stock_info(self.ticker)
            print(f"DEBUG: Info received - keys: {list(info.keys()) if info else 'None'}")
            
            # Alpha Vantage field mappings (updated from Yahoo Finance)
            required_fields = {
                'shortName': 'company',        # Company name from Alpha Vantage
                'currentPrice': 'price',       # Current stock price
                'volume': 'trading_volume',    # Daily trading volume
                'averageVolume': 'avg_trading_volume'  # Average trading volume
            }
            
            print(f"DEBUG: Extracting required fields...")
            data = {field: info.get(key) for key, field in required_fields.items()}
            data['name'] = self.ticker
            
            print(f"DEBUG: Extracted data:")
            for key, value in data.items():
                print(f"DEBUG:   {key}: {value}")
            
            # Check for required fields
            missing_fields = []
            if not data.get('company'):
                missing_fields.append('company (shortName)')
            if not data.get('price'):
                missing_fields.append('price (currentPrice)')
                
            if missing_fields:
                print(f"DEBUG: Missing required fields: {missing_fields}")
                
                # Try alternative fields (Alpha Vantage specific)
                print(f"DEBUG: Trying alternative fields...")
                if not data.get('company'):
                    alt_company = (info.get('longName') or 
                                 info.get('symbol') or 
                                 self.ticker)
                    data['company'] = alt_company
                    print(f"DEBUG: Using alternative company name: {alt_company}")
                
                if not data.get('price'):
                    # Try different Alpha Vantage price fields
                    alt_price = (info.get('currentPrice') or 
                               info.get('Price') or  # Direct from company overview
                               0.0)  # Default if no price available
                    if alt_price and alt_price != 0.0:
                        data['price'] = float(alt_price)
                        print(f"DEBUG: Using alternative price: {alt_price}")
                    else:
                        # Set a placeholder price if none available
                        data['price'] = 1.0
                        print(f"DEBUG: No price available, using placeholder: 1.0")
            
            # Set defaults for optional fields
            if data.get('trading_volume') is None:
                data['trading_volume'] = 0
                print(f"DEBUG: Set trading_volume default: 0")
            if data.get('avg_trading_volume') is None:
                data['avg_trading_volume'] = 0.0
                print(f"DEBUG: Set avg_trading_volume default: 0.0")
            
            # Final validation
            if not data.get('company') or not data.get('price'):
                available_info = {k: v for k, v in info.items() if v is not None}
                print(f"DEBUG: Available info fields: {list(available_info.keys())}")
                raise StockDataError(f"Missing required data for {self.ticker}. Available: company={data.get('company')}, price={data.get('price')}")

            print(f"DEBUG: Final data to insert:")
            for key, value in data.items():
                print(f"DEBUG:   {key}: {value}")

            print(f"DEBUG: Inserting into database...")
            with self.db_manager.transaction():
                self.db_manager.insert_record('stocks', data)
            print(f"DEBUG: Stock {self.ticker} inserted successfully")
            logger.info(f"Stock {self.ticker} added successfully.")
            
        except (StockDataError, Exception) as e:
            print(f"DEBUG ERROR: Failed to add stock {self.ticker}: {e}")
            import traceback
            print(f"DEBUG ERROR: Traceback: {traceback.format_exc()}")
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
            
