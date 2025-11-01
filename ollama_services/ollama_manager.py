import requests
import os

class OllamaManager:
    def __init__(self, host=None):
        self.host = host or os.environ.get('OLLAMA_HOST', 'http://localhost:11435')

    def ask_question(self, prompt: str, model: str = 'llama3') -> str:
        """
        Sends a question to the Ollama service and returns the response.
        """
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            ollama_url = f"{self.host}/api/generate"
            response = requests.post(ollama_url, json=data, timeout=120)
            
            response.raise_for_status()

            response_json = response.json()
            return response_json.get('response', 'No response field in JSON output.')

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama: {e}")
            return "Error: Could not connect to the Ollama service."
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "Error: An unexpected error occurred."
