from flask import Blueprint, request, jsonify
import os
import sys

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

# Now you can import from ollama_services
from ollama_services.ollama_manager import OllamaManager

chatbot_bp = Blueprint('chatbot', __name__)

ollama_manager = OllamaManager()

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        response = ollama_manager.ask_question(message)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
