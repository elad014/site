import requests
import json
from typing import Dict, Any


def check_available_models() -> None:
    """Check what models are available in Ollama."""
    url = "http://localhost:11435/api/tags"
    print("Checking available models in Ollama...")
    print("=" * 50)
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            if models:
                print(f"Found {len(models)} model(s):\n")
                for model in models:
                    name = model.get('name', 'unknown')
                    size = model.get('size', 0)
                    size_gb = size / (1024**3)
                    print(f"  - {name} ({size_gb:.2f} GB)")
            else:
                print("No models found!")
                print("\nTo pull a model, run:")
                print("  docker exec -it ollama ollama pull llama3.2")
                print("  or")
                print("  docker exec -it ollama ollama pull llama3.2:1b")
        else:
            print(f"Error: Status {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to Ollama service")
        print("Make sure Ollama is running: docker-compose up -d")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    print("=" * 50)


def pull_model(model_name: str = "llama3.2:1b") -> None:
    """
    Pull a model using Ollama API.
    
    Args:
        model_name: Name of the model to pull (default: llama3.2:1b - smallest)
    """
    url = "http://localhost:11435/api/pull"
    
    payload = {
        "name": model_name,
        "stream": False
    }
    
    print(f"Pulling model: {model_name}")
    print("This may take several minutes...")
    print("=" * 50)
    
    try:
        response = requests.post(url, json=payload, timeout=600)
        
        if response.status_code == 200:
            print(f"✓ Successfully pulled {model_name}")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: Status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    print("=" * 50)


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Ollama Model Manager")
    print("=" * 50 + "\n")
    
    # Check available models
    check_available_models()
    
    print("\n" + "=" * 50)
    print("Options:")
    print("=" * 50)
    print("To pull a model manually via Docker:")
    print("  docker exec -it ollama ollama pull llama3.2:1b")
    print("\nAvailable models:")
    print("  - llama3.2:1b (1.3 GB) - Fastest, smallest")
    print("  - llama3.2 (2 GB) - Good balance")
    print("  - llama3.1 (4.7 GB) - Larger, more capable")
    print("  - llama3.1:70b (40 GB) - Most capable")
    print("=" * 50)

