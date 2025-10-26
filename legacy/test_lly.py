#!/usr/bin/env python3
"""
Test script specifically for LLY stock ticker using Alpha Vantage
"""

import os
import sys
import traceback

# Set a demo API key for testing (replace with real key)
os.environ['ALPHA_VANTAGE_API_KEY'] = 'YOUR_API_KEY_HERE'

def test_lly_alpha_vantage_direct():
    """Basic test of LLY using Alpha Vantage directly"""
    print("=== TESTING LLY WITH ALPHA VANTAGE DIRECTLY ===")
    
    try:
        from alpha_vantage.timeseries import TimeSeries
        from alpha_vantage.fundamentaldata import FundamentalData
        
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if api_key == 'YOUR_API_KEY_HERE':
            print("   ⚠️  WARNING: Using demo API key. Please set a real Alpha Vantage API key.")
            print("   Get your free key from: https://www.alphavantage.co/support/#api-key")
            return False
        
        print("1. Creating Alpha Vantage clients...")
        ts = TimeSeries(key=api_key, output_format='pandas')
        fd = FundamentalData(key=api_key, output_format='dict')
        
        print("2. Fetching company overview for LLY...")
        overview, meta_data = fd.get_company_overview('LLY')
        
        print(f"   Overview type: {type(overview)}")
        if overview and isinstance(overview, dict):
            print("3. Key company information:")
            important_fields = ['Symbol', 'Name', 'Description', 'Sector', 'Industry', 
                              'MarketCapitalization', 'Price', 'Currency', 'Country']
            for field in important_fields:
                value = overview.get(field, 'N/A')
                if field == 'Description' and len(str(value)) > 100:
                    value = str(value)[:100] + "..."
                print(f"   {field}: {value}")
        
        print("4. Fetching daily data...")
        daily_data, daily_meta = ts.get_daily('LLY', outputsize='compact')
        if not daily_data.empty:
            print(f"   Daily data shape: {daily_data.shape}")
            latest_close = daily_data['4. close'].iloc[-1]
            latest_volume = daily_data['5. volume'].iloc[-1]
            print(f"   Latest close price: ${latest_close}")
            print(f"   Latest volume: {latest_volume:,}")
        
        return True
            
    except ImportError as e:
        print(f"   ❌ Alpha Vantage library not installed: {e}")
        print("   Install with: pip install alpha_vantage")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_lly_with_our_class():
    """Test LLY using our AlphaVantageProvider class"""
    print("\n=== TESTING LLY WITH OUR ALPHAVANTAGE PROVIDER CLASS ===")
    
    try:
        # Import our classes
        sys.path.append(os.path.dirname(__file__))
        from blueprints.stocks.stocks import AlphaVantageProvider
        
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if api_key == 'YOUR_API_KEY_HERE':
            print("   ⚠️  WARNING: Using demo API key. Skipping this test.")
            return False
        
        print("1. Creating AlphaVantageProvider...")
        provider = AlphaVantageProvider()
        
        print("2. Testing is_valid_ticker('LLY')...")
        is_valid = provider.is_valid_ticker('LLY')
        print(f"   Result: {is_valid}")
        
        if is_valid:
            print("3. Getting stock info...")
            info = provider.get_stock_info('LLY')
            print(f"   Info keys: {list(info.keys()) if info else 'None'}")
            
            # Check the specific fields we need
            required_fields = ['shortName', 'currentPrice', 'volume', 'averageVolume']
            
            print("4. Required fields check:")
            for field in required_fields:
                value = info.get(field)
                print(f"   {field}: {value}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_api_key_setup():
    """Test API key configuration"""
    print("\n=== TESTING API KEY SETUP ===")
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    print(f"1. Environment variable ALPHA_VANTAGE_API_KEY: {api_key}")
    
    if not api_key or api_key == 'YOUR_API_KEY_HERE':
        print("   ❌ No valid API key found!")
        print("   Instructions:")
        print("   1. Go to: https://www.alphavantage.co/support/#api-key")
        print("   2. Sign up for a free API key")
        print("   3. Set environment variable: set ALPHA_VANTAGE_API_KEY=your_key_here")
        print("   4. Or update the key in config_example.py and copy to config.py")
        return False
    else:
        print(f"   ✓ API key found: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else api_key}")
        return True

def compare_yahoo_vs_alphavantage():
    """Compare Yahoo Finance vs Alpha Vantage for LLY"""
    print("\n=== COMPARING YAHOO FINANCE VS ALPHA VANTAGE ===")
    
    # Test Yahoo Finance
    try:
        import yfinance as yf
        print("1. Yahoo Finance test:")
        stock = yf.Ticker('LLY')
        yf_info = stock.info
        yf_name = yf_info.get('shortName', 'N/A')
        yf_price = yf_info.get('currentPrice', 'N/A')
        print(f"   Name: {yf_name}")
        print(f"   Price: ${yf_price}")
        
    except Exception as e:
        print(f"   Yahoo Finance error: {e}")
    
    # Test Alpha Vantage
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if api_key and api_key != 'YOUR_API_KEY_HERE':
        try:
            from alpha_vantage.fundamentaldata import FundamentalData
            print("2. Alpha Vantage test:")
            fd = FundamentalData(key=api_key, output_format='dict')
            av_overview, _ = fd.get_company_overview('LLY')
            av_name = av_overview.get('Name', 'N/A')
            av_price = av_overview.get('Price', 'N/A')
            print(f"   Name: {av_name}")
            print(f"   Price: ${av_price}")
            
        except Exception as e:
            print(f"   Alpha Vantage error: {e}")
    else:
        print("2. Alpha Vantage test: Skipped (no API key)")

if __name__ == "__main__":
    print("=== ALPHA VANTAGE LLY TEST SCRIPT ===")
    
    # Run all tests
    api_ok = test_api_key_setup()
    av_direct_ok = test_lly_alpha_vantage_direct() if api_ok else False
    av_class_ok = test_lly_with_our_class() if api_ok else False
    
    compare_yahoo_vs_alphavantage()
    
    print(f"\n=== TEST RESULTS ===")
    print(f"API Key Setup: {'✓' if api_ok else '❌'}")
    print(f"Alpha Vantage Direct: {'✓' if av_direct_ok else '❌'}")
    print(f"Our Provider Class: {'✓' if av_class_ok else '❌'}")
    
    if not api_ok:
        print("\n📝 TO DO: Set up Alpha Vantage API key to run full tests")
    
    print("\n=== TEST COMPLETE ===") 