#!/usr/bin/env python3
"""
Configuration management for Flask Stock API
Loads settings from environment variables with fallback defaults
"""
import os
from dotenv import load_dotenv

class Config:
    """Configuration class that loads from environment variables"""
    
    def __init__(self):
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        # API Configuration
        self.ALPHAVANTAGE_API_KEY = os.getenv('ALPHAVANTAGE_API_KEY')
        if not self.ALPHAVANTAGE_API_KEY:
            raise ValueError("ALPHAVANTAGE_API_KEY environment variable is required!")
        self.ALPHAVANTAGE_BASE_URL = os.getenv('ALPHAVANTAGE_BASE_URL', 'https://www.alphavantage.co/query')
        
        # Server Configuration
        self.HOST = os.getenv('HOST', '0.0.0.0')
        self.PORT = int(os.getenv('PORT', '5001'))
        self.DEBUG = self._get_bool_env('DEBUG', False)
        
        # API Settings
        self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', '10'))
        
        # Print loaded configuration (without sensitive data)
        self._print_config()
    
    def _get_bool_env(self, key, default=False):
        """Convert environment variable to boolean"""
        value = os.getenv(key, '').lower()
        if value in ('true', '1', 'yes', 'on'):
            return True
        elif value in ('false', '0', 'no', 'off'):
            return False
        return default
    
    def _print_config(self):
        """Print configuration (hide sensitive data)"""
        print("📋 Configuration loaded:")
        print(f"   🔑 API Key: {'✓ Set' if self.ALPHAVANTAGE_API_KEY else '✗ Missing'}")
        print(f"   🌐 Host: {self.HOST}:{self.PORT}")
        print(f"   🐛 Debug: {self.DEBUG}")
        print(f"   ⏱️  Timeout: {self.API_TIMEOUT}s")

# Create global config instance
config = Config()

# For backward compatibility, expose as module-level variables
ALPHAVANTAGE_API_KEY = config.ALPHAVANTAGE_API_KEY
ALPHAVANTAGE_BASE_URL = config.ALPHAVANTAGE_BASE_URL
HOST = config.HOST
PORT = config.PORT
DEBUG = config.DEBUG
API_TIMEOUT = config.API_TIMEOUT
