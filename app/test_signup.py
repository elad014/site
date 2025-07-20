#!/usr/bin/env python3
"""
Test script for signup functionality
"""

from db import DB_Config, DB_Manager
from werkzeug.security import generate_password_hash
import sys
import traceback

def test_database_connection():
    """Test basic database connection"""
    print("=== TESTING DATABASE CONNECTION ===")
    
    try:
        print("1. Testing connection...")
        conn = DB_Config.get_db_connection()
        print("   ✓ Connection successful")
        
        print("2. Testing cursor...")
        cursor = DB_Config.get_cursor()
        print("   ✓ Cursor created")
        
        print("3. Testing simple query...")
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"   PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_users_table():
    """Test users table existence and structure"""
    print("\n=== TESTING USERS TABLE ===")
    
    try:
        cursor = DB_Config.get_cursor()
        
        print("1. Checking if users table exists...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        exists = cursor.fetchone()[0]
        print(f"   Users table exists: {exists}")
        
        if exists:
            print("2. Getting table structure...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            print("   Table structure:")
            for col in columns:
                print(f"     {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
            
            print("3. Getting constraints...")
            cursor.execute("""
                SELECT conname, contype, pg_get_constraintdef(oid) 
                FROM pg_constraint 
                WHERE conrelid = 'users'::regclass;
            """)
            constraints = cursor.fetchall()
            if constraints:
                print("   Constraints:")
                for const in constraints:
                    print(f"     {const[0]} ({const[1]}): {const[2]}")
            else:
                print("   No constraints found")
                
        else:
            print("2. Table doesn't exist. Here's a suggested CREATE statement:")
            create_sql = """
            CREATE TABLE users (
                user_id VARCHAR(50) PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone_number VARCHAR(20),
                country VARCHAR(50),
                user_type INTEGER DEFAULT 0
            );
            """
            print(create_sql)
        
        cursor.close()
        return exists
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_signup_simulation():
    """Simulate the signup process"""
    print("\n=== SIMULATING SIGNUP PROCESS ===")
    
    # Test data
    test_data = {
        'user_id': 'test_user_123',
        'email': 'test@example.com',
        'full_name': 'Test User',
        'phone_number': '+1234567890',
        'password': generate_password_hash('testpassword123'),
        'country': 'Test Country',
        'user_type': 0
    }
    
    try:
        print("1. Getting database cursor...")
        cursor = DB_Config.get_cursor()
        db_manager = DB_Manager(cursor)
        print("   ✓ Database connection successful")
        
        print("2. Test data to insert:")
        for key, value in test_data.items():
            if key == 'password':
                print(f"   {key}: [HASHED PASSWORD]")
            else:
                print(f"   {key}: {value}")
        
        print("3. Checking for existing user with same user_id...")
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (test_data['user_id'],))
        existing = cursor.fetchone()
        if existing:
            print(f"   Found existing user: {existing[0]}")
            print("   Deleting test user first...")
            cursor.execute("DELETE FROM users WHERE user_id = %s", (test_data['user_id'],))
            cursor.connection.commit()
        
        print("4. Checking for existing user with same email...")
        cursor.execute("SELECT email FROM users WHERE email = %s", (test_data['email'],))
        existing_email = cursor.fetchone()
        if existing_email:
            print(f"   Found existing email: {existing_email[0]}")
            print("   Deleting user with test email first...")
            cursor.execute("DELETE FROM users WHERE email = %s", (test_data['email'],))
            cursor.connection.commit()
        
        print("5. Attempting to insert new user...")
        db_manager.insert_record('users', test_data)
        cursor.connection.commit()
        print("   ✓ User inserted successfully")
        
        print("6. Verifying insertion...")
        cursor.execute("SELECT user_id, email, full_name FROM users WHERE user_id = %s", (test_data['user_id'],))
        inserted_user = cursor.fetchone()
        if inserted_user:
            print(f"   ✓ User found: ID={inserted_user[0]}, Email={inserted_user[1]}, Name={inserted_user[2]}")
        else:
            print("   ✗ User not found after insertion")
        
        print("7. Cleaning up test data...")
        cursor.execute("DELETE FROM users WHERE user_id = %s", (test_data['user_id'],))
        cursor.connection.commit()
        print("   ✓ Test data cleaned up")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"   ✗ Error during signup simulation: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("=== SIGNUP TEST SCRIPT ===")
    
    success = True
    success &= test_database_connection()
    success &= test_users_table()
    success &= test_signup_simulation()
    
    if success:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed!")
    
    print("=== TEST COMPLETE ===") 