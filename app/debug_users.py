#!/usr/bin/env python3
"""
Debug script to check users table, stocks table, and watchlist table with database connection
"""

from db import DB_Config
import sys

def debug_table(table_name, cursor):
    """Generic function to debug any table"""
    print(f"\n=== DEBUGGING {table_name.upper()} TABLE ===")
    
    try:
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (table_name,))
        table_exists = cursor.fetchone()[0]
        print(f"   {table_name} table exists: {table_exists}")
        
        if table_exists:
            # Get table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = cursor.fetchall()
            print(f"   {table_name} table structure:")
            for col in columns:
                print(f"     - {col[0]} ({col[1]}) Nullable: {col[2]} Default: {col[3]}")
            
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   Total records in {table_name}: {count}")
            
            if count > 0:
                # Show first few records
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                records = cursor.fetchall()
                colnames = [desc[0] for desc in cursor.description]
                print(f"   First 5 records from {table_name}:")
                print(f"     Columns: {colnames}")
                for i, record in enumerate(records):
                    print(f"     Record {i+1}: {record}")
        else:
            print(f"   {table_name} table does not exist!")
            if table_name == 'users':
                create_query = """
                CREATE TABLE IF NOT EXISTS users (
                    user_id VARCHAR(50) PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone_number VARCHAR(20),
                    country VARCHAR(50),
                    user_type INTEGER DEFAULT 0
                );
                """
                print(f"   Suggested {table_name} creation query:")
                print(f"   {create_query}")
            elif table_name == 'stocks':
                create_query = """
                CREATE TABLE IF NOT EXISTS stocks (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(10) UNIQUE NOT NULL,
                    company VARCHAR(200) NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    trading_volume BIGINT DEFAULT 0,
                    avg_trading_volume DECIMAL(15,2) DEFAULT 0
                );
                """
                print(f"   Suggested {table_name} creation query:")
                print(f"   {create_query}")
            elif table_name == 'user_stocks_watchlist':
                create_query = """
                CREATE TABLE IF NOT EXISTS user_stocks_watchlist (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
                    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, stock_id)
                );
                """
                print(f"   Suggested {table_name} creation query:")
                print(f"   {create_query}")
        
        return table_exists
        
    except Exception as e:
        print(f"   ERROR debugging {table_name}: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def debug_watchlist_details(cursor):
    """Debug watchlist with joined user and stock information"""
    print(f"\n=== DEBUGGING WATCHLIST WITH DETAILS ===")
    
    try:
        # Check if all required tables exist
        cursor.execute("""
            SELECT 
                (SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')) as users_exists,
                (SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'stocks')) as stocks_exists,
                (SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_stocks_watchlist')) as watchlist_exists
        """)
        
        exists_check = cursor.fetchone()
        users_exists, stocks_exists, watchlist_exists = exists_check
        
        print(f"   Required tables status:")
        print(f"     users: {'✓' if users_exists else '❌'}")
        print(f"     stocks: {'✓' if stocks_exists else '❌'}")
        print(f"     user_stocks_watchlist: {'✓' if watchlist_exists else '❌'}")
        
        if all([users_exists, stocks_exists, watchlist_exists]):
            # Get detailed watchlist information
            cursor.execute("""
                SELECT 
                    u.user_id,
                    u.full_name,
                    u.email,
                    s.name as stock_ticker,
                    s.company,
                    s.price,
                    w.added_date
                FROM user_stocks_watchlist w
                JOIN users u ON w.user_id = u.user_id
                JOIN stocks s ON w.stock_id = s.id
                ORDER BY u.user_id, w.added_date DESC;
            """)
            
            watchlist_details = cursor.fetchall()
            
            if watchlist_details:
                print(f"   Detailed watchlist ({len(watchlist_details)} entries):")
                current_user = None
                for detail in watchlist_details:
                    user_id, full_name, email, ticker, company, price, added_date = detail
                    
                    if current_user != user_id:
                        print(f"\n     👤 User: {user_id} ({full_name}) - {email}")
                        current_user = user_id
                    
                    print(f"        📈 {ticker}: {company} - ${price} (Added: {added_date})")
            else:
                print(f"   No watchlist entries found")
                
                # Check individual table counts
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM stocks") 
                stock_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM user_stocks_watchlist")
                watchlist_count = cursor.fetchone()[0]
                
                print(f"   Table counts: users={user_count}, stocks={stock_count}, watchlist={watchlist_count}")
        else:
            print(f"   Cannot show detailed watchlist - missing required tables")
        
    except Exception as e:
        print(f"   ERROR debugging watchlist details: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

def main():
    print("=== COMPREHENSIVE DATABASE DEBUG SCRIPT ===")
    
    try:
        print("1. Testing database connection...")
        conn = DB_Config.get_db_connection()
        print("   ✓ Database connection successful")
        conn.close()
        
        print("2. Getting cursor...")
        cursor = DB_Config.get_cursor()
        print("   ✓ Cursor obtained successfully")
        
        # Debug all tables
        tables_to_debug = ['users', 'stocks', 'user_stocks_watchlist']
        existing_tables = []
        
        for table in tables_to_debug:
            if debug_table(table, cursor):
                existing_tables.append(table)
        
        # Show detailed watchlist if possible
        debug_watchlist_details(cursor)
        
        # Summary
        print(f"\n=== SUMMARY ===")
        print(f"Tables found: {len(existing_tables)}/{len(tables_to_debug)}")
        for table in tables_to_debug:
            status = "✓ EXISTS" if table in existing_tables else "❌ MISSING"
            print(f"  {table}: {status}")
        
        cursor.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return 1
    
    print("=== DEBUG COMPLETE ===")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 