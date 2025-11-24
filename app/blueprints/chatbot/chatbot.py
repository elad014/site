import sys
import os
from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from psycopg2 import OperationalError
import logging
import requests

chatbot_bp = Blueprint('chatbot', __name__)

# RAG Service configuration
RAG_SERVICE_URL = os.getenv('RAG_SERVICE_URL', 'http://rag_service:5002')


@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint that forwards messages to RAG service with user context
    """
    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Get user information from session
        user_id = None
        user_name = None
        
        if current_user.is_authenticated:
            user_id = str(current_user.id)
            user_name = current_user.full_name
        
        # Prepare request payload for RAG service
        payload = {
            'query': message,
            'user_id': user_id,
            'user_name': user_name
        }
        
        # Call RAG service API
        response = requests.post(
            f'{RAG_SERVICE_URL}/api/answer',
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            if result_data.get('status') == 'success':
                answer_text = result_data.get('data', {}).get('answer', 'Sorry, I could not generate an answer.')
                return jsonify({'response': answer_text})
            else:
                error_msg = result_data.get('message', 'Unknown error from RAG service')
                return jsonify({'error': error_msg}), 500
        else:
            logging.error(f"RAG service returned status {response.status_code}")
            return jsonify({'error': 'Failed to get response from RAG service'}), 500

    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to RAG service: {e}")
        return jsonify({'error': 'Could not connect to RAG service'}), 500
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500
