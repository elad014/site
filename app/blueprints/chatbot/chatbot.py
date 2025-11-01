import sys
import os
from flask import Blueprint, render_template, request, jsonify
from psycopg2 import OperationalError
import logging

# Add the project root to the Python path to allow importing from 'rag'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rag.rag import RAGRetriever

chatbot_bp = Blueprint('chatbot', __name__)


@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message')
    DB_CONNECTION_STRING = os.getenv('DB_CONNECTION_STRING')
    if not DB_CONNECTION_STRING:
        return jsonify({'error': 'Database connection string not found'}), 500
    rag = RAGRetriever(DB_CONNECTION_STRING)

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # The generate_answer function returns a dictionary.
        # We need to extract the 'answer' text from it.
        result_dict = rag.generate_answer(query_text=message, stock_id=29) # Assuming stock_id 29 for now
        
        # Now, create the JSON response in the format the frontend expects.
        response_text = result_dict.get('answer', 'Sorry, I could not generate an answer.')
        return jsonify({'response': response_text})

    except Exception as e:
        # It's good practice to log the error to the console
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500
