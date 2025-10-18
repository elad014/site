from flask import Flask, request, jsonify
import requests
import os
from typing import Dict, Any

app = Flask(__name__)

# Get Ollama host from environment variable
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')


@app.route('/api/chat', methods=['POST'])
def chat() -> Dict[str, Any]:
    """
    Endpoint to receive JSON, send to Ollama, and return JSON response.
    
    Expected JSON format:
    {
        "model": 'llama3'
        "prompt": "Your question here",
        "stream": false
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        if 'prompt' not in data:
            return jsonify({"error": "Missing 'prompt' field"}), 400
        
        # Set default model if not provided
        if 'model' not in data:
            data['model'] = 'llama3'
        
        # Ensure stream is false for JSON response
        data['stream'] = False
        
        # Send request to Ollama
        ollama_url = f"{OLLAMA_HOST}/api/generate"
        response = requests.post(ollama_url, json=data, timeout=120)
        
        # Check if request was successful
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({
                "error": "Ollama service error",
                "status_code": response.status_code,
                "message": response.text
            }), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 503
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


@app.route('/api/generate', methods=['POST'])
def generate() -> Dict[str, Any]:
    """
    Direct passthrough to Ollama's generate endpoint.
    Accepts any JSON format that Ollama supports.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Forward request directly to Ollama
        ollama_url = f"{OLLAMA_HOST}/api/generate"
        response = requests.post(ollama_url, json=data, timeout=120)
        
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({
                "error": "Ollama service error",
                "status_code": response.status_code,
                "message": response.text
            }), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 503
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


@app.route('/health', methods=['GET'])
def health() -> Dict[str, str]:
    """Health check endpoint."""
    try:
        # Check if Ollama is reachable
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        ollama_status = "unreachable"
    
    return jsonify({
        "status": "healthy",
        "ollama_host": OLLAMA_HOST,
        "ollama_status": ollama_status
    }), 200


@app.route('/', methods=['GET'])
def index() -> Dict[str, Any]:
    """Root endpoint with API documentation."""
    return jsonify({
        "message": "Flask Ollama API Service",
        "endpoints": {
            "/api/chat": {
                "method": "POST",
                "description": "Send a prompt to Ollama and get a response",
                "example": {
                    "model": "llama3",
                    "prompt": "What is Python?"
                }
            },
            "/api/generate": {
                "method": "POST",
                "description": "Direct passthrough to Ollama's generate endpoint"
            },
            "/health": {
                "method": "GET",
                "description": "Health check for the service and Ollama"
            }
        }
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

