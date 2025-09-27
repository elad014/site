import logging
import os
import sys
from datetime import datetime
import requests
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

# Set up paths and logging
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from db import DB_Config
except ImportError as e:
    logging.error(f"Error importing DB_Config: {e}")
    sys.exit(1)

load_dotenv()

# The web service is running on 'web' at port 5000 inside the Docker network
WEB_SERVICE_URL = "http://127.0.0.1:8000"

def get_stock_symbols_from_db():
    """Fetches all stock symbols from the database."""
    conn = None
    try:
        print(f"DEBUG: Getting database connection...")
        conn = DB_Config.get_db_connection()
        print(f"DEBUG: Database connection: {conn}")
        if conn:
            # Print the table structure to identify the correct column name
            DB_Config.print_table_content('stocks')
            
            query = f"SELECT * FROM stocks"
            df = pd.read_sql(query, conn)
            print(f"DEBUG: Stock symbols: {df}")
            logging.info(f"Successfully fetched {len(df)} stock symbols from the database.")
            print(f"DEBUG: Stock symbols: {df['name'].tolist()}")
            return df['name'].tolist()
    except Exception as e:
        logging.error(f"An error occurred while fetching stock data from DB: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_stock_data_from_service(symbol: str) -> dict:
    """Gets stock data for a symbol by calling the web service."""
    try:
        url = f"{WEB_SERVICE_URL}/stock/{symbol}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        if "error" in data:
            logging.warning(f"API service returned an error for {symbol}: {data['error']}")
            return None
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get data for {symbol} from web service: {e}")
        return None

from typing import Dict, Any

def update_stock_in_db(symbol: str, data: Dict[str, Any]) -> None:
    """
    Updates a single stock's data in the database.
    The data dict is expected to have keys matching the columns in the stocks table.
    """
    conn = None
    cursor = None
    try:
        conn = DB_Config.get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Map incoming data to the correct columns in the stocks table
            # Adjust these keys to match your actual table columns
            query = """
                UPDATE stocks
                SET
                    price = %s,
                    trading_volume = %s,
                WHERE name = %s
            """

            last_updated = datetime.now()

            # Map the incoming data to the correct columns
            # Adjust the keys below to match your table's column names
            values = (
                data.get('price'),            # maps to 'price' column
                data.get('volume'),           # maps to 'trading_volume' column
                symbol                        # WHERE name = symbol
            )
            cursor.execute(query, values)
            conn.commit()
            logging.info(f"Successfully updated stock data for {symbol} from service.")
    except Exception as e:
        logging.error(f"Error updating stock {symbol} in DB: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_all_stocks() -> None:
    """
    Fetches stock symbols from DB, gets updated data by calling the web service,
    and updates the database.
    """
    logging.info("Starting scheduled stock update job via web service.")
    stocks_to_update = get_stock_symbols_from_db()
    print(f"DEBUG: Stocks to update: {stocks_to_update}")
    if not stocks_to_update:
        logging.warning("No stocks found in DB to update.")
        return

    for symbol in stocks_to_update:
        logging.info(f"Processing symbol: {symbol}")
        stock_data = get_stock_data_from_service(symbol)
        print(f"DEBUG: Stock data: {stock_data}")
        if stock_data:
            update_stock_in_db(symbol, stock_data)
        else:
            logging.warning(f"No data received from service for symbol: {symbol}. Skipping update.")
    
    logging.info("Stock update job finished.")


if __name__ == "__main__":
    update_all_stocks()
    # scheduler = BlockingScheduler()
    # # Schedule the job to run every 12 hours
    # scheduler.add_job(update_all_stocks, 'interval', hours=12)
    
    # # Run the job immediately on startup as well
    # logging.info("Running initial stock update on startup.")
    # update_all_stocks()
    
    # logging.info("Scheduler started. Press Ctrl+C to exit.")
    # try:
    #     scheduler.start()
    # except (KeyboardInterrupt, SystemExit):
    #     pass 