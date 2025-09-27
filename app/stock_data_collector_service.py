#!/usr/bin/env python3
"""
Minimal Flask Stock API
Simple stock data service with Alpha Vantage
"""
import requests
from flask import Flask, jsonify, Response
from datetime import datetime
import json
import config

app = Flask(__name__)

def get_stock_data(symbol):
    """Get stock data from Alpha Vantage API"""
    try:
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol.upper(),
            'apikey': config.ALPHAVANTAGE_API_KEY,
            'datatype': 'json'
        }
        
        response = requests.get(
            config.ALPHAVANTAGE_BASE_URL, 
            params=params, 
            timeout=config.API_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API errors
        if "Error Message" in data:
            return {"error": f"API Error: {data['Error Message']}"}
        
        if "Note" in data:
            return {"error": f"API Limit: {data['Note']}"}
        
        # Extract quote data
        quote = data.get('Global Quote', {})
        if not quote:
            return {"error": "No quote data found"}
        
        # Parse the data safely
        def safe_float(value, default=0.0):
            try:
                return float(value) if value else default
            except (ValueError, TypeError):
                return default
        
        def safe_int(value, default=0):
            try:
                return int(float(value)) if value else default
            except (ValueError, TypeError):
                return default
        
        # Create result with desired order
        result = {}
        result["symbol"] = quote.get('01. symbol', symbol.upper())
        result["price"] = safe_float(quote.get('05. price'))
        result["change"] = safe_float(quote.get('09. change'))
        result["change_percent"] = safe_float(quote.get('10. change percent', '0%').rstrip('%'))
        result["volume"] = safe_int(quote.get('06. volume'))
        result["last_trading_day"] = quote.get('07. latest trading day', '')
        result["timestamp"] = datetime.utcnow().isoformat() + 'Z'
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "service": "Flask Stock API",
        "status": "healthy",
        "version": "1.0.0",
        "usage": "/stock/<SYMBOL>",
        "example": "/stock/AAPL"
    })

@app.route('/stock/<symbol>')
def stock(symbol):
    """Get stock data for a symbol"""
    if not symbol or len(symbol) > 10:
        return Response(
            json.dumps({"error": "Invalid symbol"}, ensure_ascii=False),
            mimetype='application/json'
        ), 400
    
    data = get_stock_data(symbol)
    
    if "error" in data:
        return Response(
            json.dumps(data, ensure_ascii=False),
            mimetype='application/json'
        ), 404
    
    # Return ordered JSON
    return Response(
        json.dumps(data, ensure_ascii=False),
        mimetype='application/json'
    )

@app.route('/health')
def health():
    """Health check"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
       
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )