import requests
import json
from typing import Dict, Any


def send_chat_request(prompt: str, model: str = "llama3") -> Dict[str, Any]:
    """
    Send a chat request to the Flask Llama API.
    
    Args:
        prompt: The message to send
        model: The model to use (default: llama3:text)
    
    Returns:
        Dict containing the response from the API
    """
    url = "http://localhost:5001/api/chat"

    payload = {
        "model": model,
        "prompt": prompt
    }
    
    print(f"Sending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json()
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to Flask service.")
        print("Make sure the service is running: docker-compose up")
        return {"error": "Connection failed"}
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
        return {"error": "Timeout"}
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {"error": str(e)}


def check_health() -> Dict[str, Any]:
    """Check if the Flask service is healthy."""
    url = "http://localhost:5001/health"
    
    try:
        response = requests.get(url, timeout=5)
        print("Health Check:")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    # First check if service is healthy
    print("=" * 50)
    print("Checking service health...")
    print("=" * 50)
    check_health()
    
    print("\n" + "=" * 50)
    print("Sending 'hi' message to Flask Llama")
    print("=" * 50)
    
    # Send "hi" message
    result = send_chat_request("how old the universe is? short answer")
    
    print("\n" + "=" * 50)
    print("Done!")
    print("=" * 50)

