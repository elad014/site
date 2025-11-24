"""
RAG Flask API Service
Provides REST API endpoints for document upload, indexing, and querying
curl -X POST http://localhost:11435/api/generate -H "Content-Type: application/json" -d "{\"model\": \"llama3\", \"prompt\": \"Explain quantum computing\", \"stream\": false}"

# Test Ollama Flask Server
curl -X POST http://localhost:5003/api/chat -H "Content-Type: application/json" -d "{\"model\": \"llama3\", \"prompt\": \"Explain quantum computing\"}"

# Test RAG Service
curl -X POST http://localhost:5002/api/answer -H "Content-Type: application/json" -d "{\"query\": \"Show me Amazon performance in Q3.\"}"
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import logging
from typing import Dict, List
import tempfile
import shutil
import re

from indexing import DocumentIndexer
from rag import RAGRetriever, RAGStats
from ticker_utils import extract_ticker_from_question
from kafka_producer import ChatMessageProducer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Database connection string
DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_MYw2ejoqv3BX@ep-green-wind-a2yx94w5-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"

# Ollama configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11435')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'chat_messages')

# Initialize services
indexer = DocumentIndexer(DB_CONNECTION_STRING)
retriever = RAGRetriever(DB_CONNECTION_STRING)
stats_collector = RAGStats(DB_CONNECTION_STRING)
kafka_producer = ChatMessageProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    topic=KAFKA_TOPIC
)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check() -> Dict:
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'RAG API',
        'version': '1.0.0'
    }), 200


@app.route('/api/setup', methods=['POST'])
def setup_database() -> Dict:
    """Initialize database tables and extensions"""
    try:
        indexer.create_table_if_not_exists()
        return jsonify({
            'status': 'success',
            'message': 'Database tables created successfully'
        }), 200
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/documents/upload', methods=['POST'])
def upload_document() -> Dict:
    """
    Upload and index a PDF document
    
    Expected form data:
        - file: PDF file
        - stock_id: ID of the stock (integer)
        - doc_name (optional): Custom document name
    """
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': 'Only PDF files are allowed'
            }), 400
        
        # Get stock_id
        stock_id = request.form.get('stock_id')
        if not stock_id:
            return jsonify({
                'status': 'error',
                'message': 'stock_id is required'
            }), 400
        
        try:
            stock_id = int(stock_id)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'stock_id must be an integer'
            }), 400
        
        # Get optional doc_name
        doc_name = request.form.get('doc_name', secure_filename(file.filename))
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        try:
            # Index the document
            logger.info(f"Indexing document: {doc_name} for stock_id: {stock_id}")
            result = indexer.index_pdf_document(
                pdf_path=temp_path,
                stock_id=stock_id,
                doc_name=doc_name
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Document indexed successfully',
                'data': result
            }), 200
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/documents/<int:stock_id>', methods=['GET'])
def list_documents(stock_id: int) -> Dict:
    """
    List all documents for a given stock
    
    Args:
        stock_id: ID of the stock
    """
    try:
        documents = indexer.list_documents(stock_id)
        
        return jsonify({
            'status': 'success',
            'stock_id': stock_id,
            'document_count': len(documents),
            'documents': documents
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/documents/delete', methods=['DELETE'])
def delete_document() -> Dict:
    """
    Delete a document and all its chunks
    
    Expected JSON body:
        - stock_id: ID of the stock (integer)
        - doc_name: Name of the document to delete
    """
    try:
        data = request.get_json()
        
        if not data or 'stock_id' not in data or 'doc_name' not in data:
            return jsonify({
                'status': 'error',
                'message': 'stock_id and doc_name are required'
            }), 400
        
        stock_id = data['stock_id']
        doc_name = data['doc_name']
        
        deleted_count = indexer.delete_document(stock_id, doc_name)
        
        return jsonify({
            'status': 'success',
            'message': f'Deleted {deleted_count} chunks',
            'deleted_chunks': deleted_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/query', methods=['POST'])
def query_documents() -> Dict:
    """
    Query documents and retrieve top matching chunks
    
    Expected JSON body:
        - query: Query text string
        - stock_id (optional): Filter by stock ID
        - doc_name (optional): Filter by document name
        - top_k (optional): Number of results to return (default: 3)
        - retrieve_text (optional): Whether to retrieve actual text from PDFs (default: false)
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'status': 'error',
                'message': 'query is required'
            }), 400
        
        query_text = data['query']
        stock_id = data.get('stock_id')
        doc_name = data.get('doc_name')
        top_k = data.get('top_k', 3)
        retrieve_text = data.get('retrieve_text', False)
        
        # Validate top_k
        try:
            top_k = int(top_k)
            if top_k < 1 or top_k > 10:
                top_k = 3
        except (ValueError, TypeError):
            top_k = 3
        
        # Execute query
        results = retriever.query(
            query_text=query_text,
            stock_id=stock_id,
            doc_name=doc_name,
            top_k=top_k,
            retrieve_text=retrieve_text
        )
        
        return jsonify({
            'status': 'success',
            'data': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error querying documents: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/answer', methods=['POST'])
def generate_answer() -> Dict:
    """
    Generate an answer with context from relevant documents
    
    Expected JSON body:
        - query: Query text string
        - user_id (optional): User ID from session
        - user_name (optional): Username from session
        - top_k (optional): Number of context chunks to retrieve
    This endpoint auto-detects the ticker from the question. If detected, searches for context related to that ticker.
    If no ticker is found, searches across all tickers/documents.
    """
    import time
    
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'status': 'error',
                'message': 'query is required'
            }), 400
        
        query_text = data['query']
        top_k = data.get('top_k', 3)  # optionally can accept top_k
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        
        # Validate top_k
        try:
            top_k = int(top_k)
            if top_k < 1 or top_k > 10:
                top_k = 3
        except (ValueError, TypeError):
            top_k = 3

        # Extract ticker from question (e.g., "What is Tesla's revenue?" -> "TSLA")
        detected_ticker = extract_ticker_from_question(query_text)

        # Track response time
        start_time = time.time()

        # Optionally: you can verify against your actual stocks table to ensure validity
        if detected_ticker:
            answer = retriever.generate_answer(
                query_text=query_text,
                stock_id=None,
                doc_name=detected_ticker,
                top_k=top_k,
                ollama_url=OLLAMA_URL,
                model_name=OLLAMA_MODEL
            )
        else:
            answer = retriever.generate_answer(
                query_text=query_text,
                stock_id=None,
                doc_name=None,
                top_k=top_k,
                ollama_url=OLLAMA_URL,
                model_name=OLLAMA_MODEL
            )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Publish to Kafka (non-blocking)
        try:
            kafka_producer.publish_chat_message(
                user_id=user_id,
                user_name=user_name,
                query=query_text,
                answer=answer.get('answer', ''),
                detected_ticker=detected_ticker,
                context_used=answer.get('context', {}),
                model_name=OLLAMA_MODEL,
                response_time_ms=response_time_ms
            )
        except Exception as kafka_error:
            logger.error(f"Failed to publish to Kafka (non-critical): {kafka_error}")
        
        return jsonify({
            'status': 'success',
            'data': answer
        }), 200

    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/retrieve-text', methods=['POST'])
def retrieve_text() -> Dict:
    """
    Retrieve actual text from PDF for specific chunks
    
    Expected JSON body:
        - stock_id: Stock ID (integer)
        - doc_name: Document name
        - chunk_index: Chunk index
        - page: Page number
    """
    try:
        data = request.get_json()
        
        required = ['stock_id', 'doc_name', 'page']
        if not all(k in data for k in required):
            return jsonify({
                'status': 'error',
                'message': f'Required fields: {required}'
            }), 400
        
        stock_id = data['stock_id']
        doc_name = data['doc_name']
        chunk_index = data.get('chunk_index', 0)
        page = data['page']
        
        # Retrieve text from PDF
        text = retriever.retrieve_chunk_text_from_pdf(
            stock_id=stock_id,
            doc_name=doc_name,
            chunk_index=chunk_index,
            page_num=page
        )
        
        if text:
            return jsonify({
                'status': 'success',
                'data': {
                    'stock_id': stock_id,
                    'doc_name': doc_name,
                    'page': page,
                    'text': text
                }
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'PDF file not found or text could not be retrieved'
            }), 404
        
    except Exception as e:
        logger.error(f"Error retrieving text: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats() -> Dict:
    """Get overall RAG system statistics"""
    try:
        stats = stats_collector.get_total_stats()
        
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/stats/<int:stock_id>', methods=['GET'])
def get_stock_stats(stock_id: int) -> Dict:
    """Get statistics for a specific stock"""
    try:
        stats = stats_collector.get_stock_stats(stock_id)
        
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stock stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error: Exception) -> Dict:
    """Handle file too large error"""
    return jsonify({
        'status': 'error',
        'message': 'File too large. Maximum size is 16MB'
    }), 413


@app.errorhandler(404)
def not_found(error: Exception) -> Dict:
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error: Exception) -> Dict:
    """Handle internal server errors"""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Initialize database on startup
    logger.info("Initializing RAG service...")
    try:
        indexer.create_table_if_not_exists()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Start Flask server
    port = int(os.getenv('RAG_PORT', 5002))
    logger.info(f"Starting RAG API service on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

