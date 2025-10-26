#!/usr/bin/env python3
"""
Setup script for Alpha Vantage integration
This script helps install and configure Alpha Vantage for the stocks application
"""

import subprocess
import sys
import os

def install_alpha_vantage():
    """Install the alpha_vantage package"""
    print("=== INSTALLING ALPHA VANTAGE PACKAGE ===")
    
    try:
        # Check if already installed
        import alpha_vantage
        print("✓ Alpha Vantage is already installed")
        return True
    except ImportError:
        print("Alpha Vantage not found. Installing...")
        
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'alpha_vantage==2.3.1'])
            print("✓ Alpha Vantage installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Alpha Vantage: {e}")
            return False

def check_api_key():
    """Check if Alpha Vantage API key is configured"""
    print("\n=== CHECKING API KEY CONFIGURATION ===")
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key or api_key == 'YOUR_API_KEY_HERE':
        print("❌ No Alpha Vantage API key found")
        print("\n📝 TO SET UP YOUR API KEY:")
        print("1. Go to: https://www.alphavantage.co/support/#api-key")
        print("2. Sign up for a free account (no credit card required)")
        print("3. Copy your API key")
        print("4. Set it as environment variable:")
        
        if os.name == 'nt':  # Windows
            print("   Windows: set ALPHA_VANTAGE_API_KEY=your_api_key_here")
        else:  # Unix/Linux/Mac
            print("   Unix/Linux/Mac: export ALPHA_VANTAGE_API_KEY=your_api_key_here")
        
        print("5. Or create a .env file in the app directory with:")
        print("   ALPHA_VANTAGE_API_KEY=your_api_key_here")
        
        return False
    else:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else api_key
        print(f"✓ API key found: {masked_key}")
        return True

def test_alpha_vantage_connection():
    """Test connection to Alpha Vantage API"""
    print("\n=== TESTING ALPHA VANTAGE CONNECTION ===")
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key or api_key == 'YOUR_API_KEY_HERE':
        print("⚠️  Skipping connection test - no API key configured")
        return False
    
    try:
        from alpha_vantage.fundamentaldata import FundamentalData
        
        print("Testing connection with a simple API call...")
        fd = FundamentalData(key=api_key, output_format='dict')
        
        # Test with a well-known stock (Apple)
        overview, _ = fd.get_company_overview('AAPL')
        
        if overview and 'Symbol' in overview:
            company_name = overview.get('Name', 'Unknown')
            print(f"✓ Connection successful! Retrieved data for: {company_name}")
            return True
        else:
            print("❌ Connection test failed - no data received")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        
        if "Invalid API call" in str(e) or "API key" in str(e):
            print("   This might be an invalid API key issue")
        elif "rate limit" in str(e).lower():
            print("   This might be a rate limit issue - try again in a minute")
        
        return False

def update_requirements():
    """Add alpha_vantage to requirements.txt if not present"""
    print("\n=== UPDATING REQUIREMENTS.TXT ===")
    
    requirements_file = 'requirements.txt'
    alpha_vantage_line = 'alpha_vantage==2.3.1'
    
    try:
        with open(requirements_file, 'r') as f:
            content = f.read()
        
        if 'alpha_vantage' in content:
            print("✓ alpha_vantage already in requirements.txt")
        else:
            with open(requirements_file, 'a') as f:
                f.write(f'\n{alpha_vantage_line}\n')
            print("✓ Added alpha_vantage to requirements.txt")
        
        return True
        
    except FileNotFoundError:
        print("⚠️  requirements.txt not found - creating new one")
        with open(requirements_file, 'w') as f:
            f.write(f'{alpha_vantage_line}\n')
        print("✓ Created requirements.txt with alpha_vantage")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update requirements.txt: {e}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n=== NEXT STEPS ===")
    print("1. Set your Alpha Vantage API key (if not done already)")
    print("2. Test the new implementation with: python test_lly.py")
    print("3. Run your Flask application and try adding stocks")
    print("4. Alpha Vantage provides more reliable data than Yahoo Finance")
    print("\n📊 ALPHA VANTAGE ADVANTAGES:")
    print("• More reliable and consistent data")
    print("• Professional financial API")
    print("• Better uptime and support")
    print("• Comprehensive fundamental data")
    print("• Rate limiting built-in for stability")

def main():
    """Main setup function"""
    print("🚀 ALPHA VANTAGE SETUP FOR STOCKS APPLICATION")
    print("=" * 50)
    
    success_count = 0
    total_steps = 4
    
    # Step 1: Install package
    if install_alpha_vantage():
        success_count += 1
    
    # Step 2: Update requirements
    if update_requirements():
        success_count += 1
    
    # Step 3: Check API key
    if check_api_key():
        success_count += 1
        
        # Step 4: Test connection (only if API key is set)
        if test_alpha_vantage_connection():
            success_count += 1
    else:
        print("⚠️  Skipping connection test - API key needed first")
    
    print(f"\n=== SETUP RESULTS ===")
    print(f"Completed: {success_count}/{total_steps} steps")
    
    if success_count == total_steps:
        print("🎉 All setup steps completed successfully!")
        print("✓ Alpha Vantage is ready to use")
    elif success_count >= 2:
        print("⚠️  Partial setup completed")
        print("   You may need to configure the API key to use all features")
    else:
        print("❌ Setup encountered issues")
        print("   Please check the error messages above")
    
    show_next_steps()

if __name__ == "__main__":
    main() 