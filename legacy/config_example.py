"""
Configuration example for Stock Application
Copy this file to config.py and update with your actual values
"""

# Alpha Vantage API Configuration
# Get your free API key from: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY = "YOUR_API_KEY_HERE"

# Rate limiting settings
ALPHA_VANTAGE_RATE_LIMIT_DELAY = 12  # seconds between requests (5 requests per minute for free tier)

# Database settings (if using environment variables)
DATABASE_URL = "postgresql://username:password@host:port/database"

# Flask settings
FLASK_ENV = "development"
FLASK_DEBUG = True

# Instructions:
# 1. Copy this file to config.py
# 2. Sign up for free Alpha Vantage API key at: https://www.alphavantage.co/support/#api-key
# 3. Replace YOUR_API_KEY_HERE with your actual API key
# 4. Set ALPHA_VANTAGE_API_KEY environment variable or update the key directly in config.py

# Example usage in your app:
# import os
# from config import ALPHA_VANTAGE_API_KEY
# 
# # Or use environment variable (recommended):
# api_key = os.getenv('ALPHA_VANTAGE_API_KEY', ALPHA_VANTAGE_API_KEY) 