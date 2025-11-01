"""
PDF Document Indexing Service
Processes PDF documents, generates embeddings, and stores in PostgreSQL with pgvector
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from typing import List, Dict, Tuple, Optional
import PyPDF2
import numpy as np
from sentence_transformers import SentenceTransformer
import json
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Handles PDF document processing and indexing with vector embeddings"""
    
    def __init__(self, db_connection_string: str, embedding_model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the document indexer
        
        Args:
            db_connection_string: PostgreSQL connection string
            embedding_model_name: Name of the sentence-transformer model to use
        """
        self.db_connection_string = db_connection_string
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"Initialized with embedding model: {embedding_model_name} (dimension: {self.embedding_dimension})")
        
    def get_db_connection(self) -> psycopg2.extensions.connection:
        """Create and return database connection"""
        return psycopg2.connect(self.db_connection_string)
    
    def create_table_if_not_exists(self) -> None:
        """Create the document_embeddings table with pgvector extension"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Enable pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create table with vector column (NO TEXT STORAGE)
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id SERIAL PRIMARY KEY,
                stock_id INTEGER NOT NULL,
                doc_name VARCHAR(255) NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_hash VARCHAR(64),
                embedding VECTOR({self.embedding_dimension}),
                metadata JSONB DEFAULT '{{}}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_query)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_id ON document_embeddings(stock_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_name ON document_embeddings(doc_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_embedding_cosine ON document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);")
            
            conn.commit()
            logger.info("Table 'document_embeddings' created successfully with pgvector support")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating table: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Extract text from PDF file page by page
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing page text and metadata
        """
        pages_data = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                logger.info(f"Processing PDF: {pdf_path} ({total_pages} pages)")
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text.strip():  # Only include pages with text
                        pages_data.append({
                            'text': text.strip(),
                            'page': page_num + 1,
                            'total_pages': total_pages
                        })
                        
                logger.info(f"Extracted text from {len(pages_data)} pages")
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
            
        return pages_data
    
    def chunk_text(self, text: str, chunk_size: int = 250, overlap: int = 25) -> List[Dict[str, any]]:
        """
        Split text into overlapping chunks with character-level indexes.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of dictionaries, each containing 'text', 'start_char', 'end_char'
        """
        chunks = []
        start_index = 0
        while start_index < len(text):
            end_index = start_index + chunk_size
            if end_index > len(text):
                end_index = len(text)
            
            # Find the last space to avoid cutting words
            if end_index < len(text):
                last_space = text.rfind(' ', start_index, end_index)
                if last_space > start_index:
                    end_index = last_space
            
            chunks.append({
                'text': text[start_index:end_index],
                'start_char': start_index,
                'end_char': end_index
            })
            
            start_index += chunk_size - overlap
            if start_index >= end_index: # ensure progress
                start_index = end_index

        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings
            
        Returns:
            NumPy array of embeddings
        """
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings
    
    def _compute_chunk_hash(self, chunk: str) -> str:
        """Compute SHA-256 hash of text chunk for reference"""
        return hashlib.sha256(chunk.encode('utf-8')).hexdigest()
    
    def store_chunks_with_embeddings(
        self,
        stock_id: int,
        doc_name: str,
        chunks: List[str],
        embeddings: np.ndarray,
        metadata_list: List[Dict]
    ) -> int:
        """
        Store vector embeddings (WITHOUT TEXT) in the database
        
        Args:
            stock_id: ID of the stock this document belongs to
            doc_name: Name of the document
            chunks: List of text chunks (used for hash, not stored)
            embeddings: NumPy array of embeddings
            metadata_list: List of metadata dictionaries for each chunk
            
        Returns:
            Number of chunks inserted
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        inserted_count = 0
        
        try:
            insert_query = """
            INSERT INTO document_embeddings (stock_id, doc_name, chunk_index, chunk_hash, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            
            for i, (chunk, embedding, metadata) in enumerate(zip(chunks, embeddings, metadata_list)):
                # Convert numpy array to list for PostgreSQL
                embedding_list = embedding.tolist()
                
                # Compute hash of chunk (for verification, not storing text)
                chunk_hash = self._compute_chunk_hash(chunk)
                
                # Add chunk_index to metadata
                metadata['chunk_index'] = i
                metadata_json = json.dumps(metadata)
                
                cursor.execute(insert_query, (
                    stock_id,
                    doc_name,
                    i,  # chunk_index
                    chunk_hash,  # hash of chunk
                    embedding_list,
                    metadata_json
                ))
                inserted_count += 1
            
            conn.commit()
            logger.info(f"Successfully inserted {inserted_count} vector embeddings (no text stored)")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing embeddings: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
            
        return inserted_count
    
    def store_pdf_file(self, pdf_path: str, stock_id: int, doc_name: str, storage_dir: str = "pdf_storage") -> str:
        """
        Store original PDF file for on-demand text retrieval
        
        Args:
            pdf_path: Path to the PDF file
            stock_id: ID of the stock
            doc_name: Name of the document
            storage_dir: Directory to store PDFs
            
        Returns:
            Path to stored PDF
        """
        import shutil
        
        # Create storage directory structure
        stock_dir = os.path.join(storage_dir, str(stock_id))
        os.makedirs(stock_dir, exist_ok=True)
        
        # Copy PDF to storage
        dest_path = os.path.join(stock_dir, doc_name)
        shutil.copy2(pdf_path, dest_path)
        
        logger.info(f"Stored PDF at: {dest_path}")
        return dest_path
    
    def index_pdf_document(
        self, 
        pdf_path: str, 
        stock_id: int, 
        doc_name: str = None,
        report_date: Optional[str] = None,
        report_type: Optional[str] = None,
        keep_pdf: bool = True
    ) -> Dict[str, any]:
        """
        Complete pipeline: Extract PDF, chunk, generate embeddings, and store
        
        Args:
            pdf_path: Path to the PDF file
            stock_id: ID of the stock this document belongs to
            doc_name: Name of the document (defaults to filename)
            report_date: Optional date of the report
            report_type: Optional type of the report (e.g., '10-K', 'Q2 Report')
            keep_pdf: Whether to store the original PDF for text retrieval
            
        Returns:
            Dictionary with indexing statistics
        """
        if doc_name is None:
            doc_name = os.path.basename(pdf_path)
        
        logger.info(f"Starting indexing for document: {doc_name} (stock_id: {stock_id})")
        
        # Extract text from PDF
        pages_data = self.extract_text_from_pdf(pdf_path)
        
        # Process each page
        all_chunks = []
        all_metadata = []
        
        for page_data in pages_data:
            # Chunk the page text
            page_chunks_with_indices = self.chunk_text(page_data['text'])
            
            # Create metadata for each chunk
            for chunk_data in page_chunks_with_indices:
                all_chunks.append(chunk_data['text'])
                metadata = {
                    'page': page_data['page'],
                    'total_pages': page_data['total_pages'],
                    'start_char': chunk_data['start_char'],
                    'end_char': chunk_data['end_char'],
                    'doc_type': 'pdf'
                }
                if report_date:
                    metadata['report_date'] = report_date
                if report_type:
                    metadata['report_type'] = report_type
                all_metadata.append(metadata)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(pages_data)} pages")
        
        # Generate embeddings
        embeddings = self.generate_embeddings(all_chunks)
        
        # Store in database (vectors only, no text)
        inserted_count = self.store_chunks_with_embeddings(
            stock_id=stock_id,
            doc_name=doc_name,
            chunks=all_chunks,
            embeddings=embeddings,
            metadata_list=all_metadata
        )
        
        # Optionally store PDF file for on-demand text retrieval
        stored_pdf_path = None
        if keep_pdf:
            try:
                stored_pdf_path = self.store_pdf_file(pdf_path, stock_id, doc_name)
            except Exception as e:
                logger.warning(f"Failed to store PDF file: {e}")
        
        result = {
            'doc_name': doc_name,
            'stock_id': stock_id,
            'total_pages': len(pages_data),
            'total_chunks': inserted_count,
            'pdf_stored': stored_pdf_path is not None,
            'pdf_path': stored_pdf_path,
            'status': 'success'
        }
        
        logger.info(f"Indexing completed: {result}")
        return result
    
    def delete_document(self, stock_id: int, doc_name: str) -> int:
        """
        Delete all chunks for a specific document
        
        Args:
            stock_id: ID of the stock
            doc_name: Name of the document to delete
            
        Returns:
            Number of chunks deleted
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            delete_query = """
            DELETE FROM document_embeddings
            WHERE stock_id = %s AND doc_name = %s;
            """
            cursor.execute(delete_query, (stock_id, doc_name))
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Deleted {deleted_count} chunks for document: {doc_name}")
            return deleted_count
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting document: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def list_documents(self, stock_id: int) -> List[Dict[str, any]]:
        """
        List all documents for a given stock
        
        Args:
            stock_id: ID of the stock
            
        Returns:
            List of document information dictionaries
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = """
            SELECT doc_name, COUNT(*) as chunk_count, MIN(created_at) as uploaded_at
            FROM document_embeddings
            WHERE stock_id = %s
            GROUP BY doc_name
            ORDER BY uploaded_at DESC;
            """
            cursor.execute(query, (stock_id,))
            results = cursor.fetchall()
            
            documents = []
            for row in results:
                documents.append({
                    'doc_name': row[0],
                    'chunk_count': row[1],
                    'uploaded_at': row[2].isoformat() if row[2] else None
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise
        finally:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    # Example usage
    DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_MYw2ejoqv3BX@ep-green-wind-a2yx94w5-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"
    
    # Initialize indexer
    indexer = DocumentIndexer(DB_CONNECTION_STRING)
    
    # Create table
    indexer.create_table_if_not_exists()
    
    #Example: Index a PDF document
    stock_id_to_index = 29
    doc_name_to_index = "NASDAQ_AMZN_2024.pdf"
    pdf_source_path = f"../pdf_storage/{doc_name_to_index}"

    # IMPORTANT: First, delete any existing versions of this document to avoid duplicates
    print(f"Deleting existing entries for {doc_name_to_index}...")
    deleted_count = indexer.delete_document(stock_id=stock_id_to_index, doc_name=doc_name_to_index)
    print(f"Deleted {deleted_count} old entries.")
    
    # Make sure your PDF is in the 'source_documents' directory at the project root
    print(f"Indexing PDF from: {pdf_source_path}")
    result = indexer.index_pdf_document(
        pdf_path=pdf_source_path,
        stock_id=stock_id_to_index,
        doc_name=doc_name_to_index
    )
    print(f"Indexing result: {result}")

