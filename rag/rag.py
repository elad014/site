"""
RAG (Retrieval Augmented Generation) Service
Handles query processing, similarity search, and answer retrieval
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from typing import List, Dict, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import json
import logging
import os
import PyPDF2
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGRetriever:
    """Handles query processing and document retrieval using vector similarity"""
    
    def __init__(self, db_connection_string: str, embedding_model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the RAG retriever
        
        Args:
            db_connection_string: PostgreSQL connection string
            embedding_model_name: Name of the sentence-transformer model (must match indexing model)
        """
        self.db_connection_string = db_connection_string
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"RAG Retriever initialized with model: {embedding_model_name}")
    
    def get_db_connection(self) -> psycopg2.extensions.connection:
        """Create and return database connection"""
        return psycopg2.connect(self.db_connection_string)
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query
        
        Args:
            query: Query text string
            
        Returns:
            NumPy array of query embedding
        """
        logger.info(f"Generating embedding for query: {query[:100]}...")
        embedding = self.embedding_model.encode(query)
        return embedding
    
    def search_similar_chunks(
        self,
        query_embedding: np.ndarray,
        stock_id: int = None,
        doc_name: str = None,
        top_k: int = 3,
        pdf_storage_dir: str = "pdf_storage"
    ) -> List[Dict[str, any]]:
        """
        Search for most similar chunks using cosine similarity
        Returns metadata only (no text stored in DB)
        
        Args:
            query_embedding: Query embedding vector
            stock_id: Optional filter by stock ID
            doc_name: Optional filter by document name
            top_k: Number of top results to return (default: 3)
            pdf_storage_dir: Directory where PDFs are stored for text retrieval
            
        Returns:
            List of dictionaries containing matching metadata
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Convert numpy array to list for PostgreSQL
            query_embedding_list = query_embedding.tolist()
            
            # Build query with optional filters
            where_clauses = []
            filter_params = []
            
            if stock_id is not None:
                where_clauses.append("stock_id = %s")
                filter_params.append(stock_id)
            
            if doc_name is not None:
                where_clauses.append("doc_name = %s")
                filter_params.append(doc_name)
            
            where_clause = " AND " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Build params list in correct order for SQL query
            params = [query_embedding_list] + filter_params + [query_embedding_list, top_k]
            
            # Query using cosine similarity (NO CHUNK TEXT - only metadata)
            search_query = f"""
            SELECT 
                id,
                stock_id,
                doc_name,
                chunk_index,
                chunk_hash,
                metadata,
                1 - (embedding <=> %s::vector) AS similarity
            FROM document_embeddings
            WHERE 1=1{where_clause}
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """
            
            cursor.execute(search_query, params)
            results = cursor.fetchall()
            
            # Format results (metadata only, no text)
            matched_chunks = []
            for row in results:
                matched_chunks.append({
                    'id': row[0],
                    'stock_id': row[1],
                    'doc_name': row[2],
                    'chunk_index': row[3],
                    'chunk_hash': row[4],
                    'metadata': row[5],
                    'similarity': float(row[6]),
                    'note': 'Text not stored in DB - retrieve from PDF if needed'
                })
            
            logger.info(f"Found {len(matched_chunks)} matching chunks (metadata only)")
            return matched_chunks
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def retrieve_chunk_text_from_pdf(
        self,
        stock_id: int,
        doc_name: str,
        chunk_index: int,
        page_num: int,
        pdf_storage_dir: str = "pdf_storage"
    ) -> Optional[str]:
        """
        Retrieve actual text from stored PDF file
        
        Args:
            stock_id: Stock ID
            doc_name: Document name
            chunk_index: Index of the chunk
            page_num: Page number containing the chunk
            pdf_storage_dir: Directory where PDFs are stored
            
        Returns:
            Text content or None if not found
        """
        pdf_path = os.path.join(pdf_storage_dir, str(stock_id), doc_name)
        
        if not os.path.exists(pdf_path):
            logger.warning(f"PDF not found: {pdf_path}")
            return None
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if page_num < 1 or page_num > len(pdf_reader.pages):
                    logger.warning(f"Invalid page number: {page_num}")
                    return None
                
                # Extract text from the specific page
                page = pdf_reader.pages[page_num - 1]  # 0-indexed
                text = page.extract_text()
                
                # TODO: Could implement chunk extraction logic here
                # For now, return full page text
                return text
                
        except Exception as e:
            logger.error(f"Error retrieving text from PDF: {e}")
            return None
    
    def query(
        self,
        query_text: str,
        stock_id: int = None,
        doc_name: str = None,
        top_k: int = 3,
        retrieve_text: bool = False,
        pdf_storage_dir: str = "pdf_storage"
    ) -> Dict[str, any]:
        """
        Main query method: generate embedding and retrieve similar chunks
        
        Args:
            query_text: The query string
            stock_id: Optional filter by stock ID
            doc_name: Optional filter by document name
            top_k: Number of top results to return (default: 3)
            retrieve_text: Whether to retrieve actual text from PDFs
            pdf_storage_dir: Directory where PDFs are stored
            
        Returns:
            Dictionary with query results (metadata only by default)
        """
        logger.info(f"Processing query: '{query_text}' (stock_id: {stock_id}, top_k: {top_k})")
        
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query_text)
        
        # Search for similar chunks (returns metadata only)
        results = self.search_similar_chunks(
            query_embedding=query_embedding,
            stock_id=stock_id,
            doc_name=doc_name,
            top_k=top_k,
            pdf_storage_dir=pdf_storage_dir
        )
        
        # Optionally retrieve actual text from PDFs
        if retrieve_text:
            for result in results:
                page_num = result['metadata'].get('page', 1)
                text = self.retrieve_chunk_text_from_pdf(
                    stock_id=result['stock_id'],
                    doc_name=result['doc_name'],
                    chunk_index=result['chunk_index'],
                    page_num=page_num,
                    pdf_storage_dir=pdf_storage_dir
                )
                if text:
                    result['retrieved_text'] = text
                    result['note'] = 'Text retrieved from PDF'
        
        # Build response
        response = {
            'query': query_text,
            'stock_id': stock_id,
            'doc_name': doc_name,
            'top_k': top_k,
            'results_count': len(results),
            'results': results,
            'text_retrieved': retrieve_text
        }
        
        return response
    
    def get_context_for_llm(
        self,
        query_text: str,
        stock_id: int = None,
        doc_name: str = None,
        top_k: int = 3,
        pdf_storage_dir: str = "pdf_storage"
    ) -> Tuple[str, List[Dict]]:
        """
        Retrieve context chunks formatted for LLM prompting
        
        Args:
            query_text: The query string
            stock_id: Optional filter by stock ID
            doc_name: Optional filter by document name
            top_k: Number of top results to return (default: 3)
            pdf_storage_dir: Directory where PDFs are stored
            
        Returns:
            Tuple of (formatted_context_string, source_metadata_list)
        """
        # Query with text retrieval from PDFs
        query_results = self.query(
            query_text=query_text,
            stock_id=stock_id,
            doc_name=doc_name,
            top_k=top_k,
            retrieve_text=True,
            pdf_storage_dir=pdf_storage_dir
        )
        
        # Format context for LLM
        context_parts = []
        sources = []
        
        for i, result in enumerate(query_results['results'], 1):
            context_parts.append(f"[Document {i}: {result['doc_name']}]")
            context_parts.append(f"Page {result['metadata'].get('page', 'N/A')}")
            
            # Use retrieved_text if available, otherwise note that text is not available
            text_content = result.get('retrieved_text', '[Text not available - PDF not found]')
            context_parts.append(text_content)
            context_parts.append("")  # Empty line between chunks
            
            sources.append({
                'doc_name': result['doc_name'],
                'page': result['metadata'].get('page'),
                'chunk_index': result.get('chunk_index'),
                'similarity': result['similarity']
            })
        
        formatted_context = "\n".join(context_parts)
        
        return formatted_context, sources
    
    def generate_answer(
        self,
        query_text: str,
        stock_id: int = None,
        doc_name: str = None,
        top_k: int = 3,
        ollama_url: str = "http://localhost:11435",
        model_name: str = "llama3"
    ) -> Dict[str, any]:
        """
        Generate an answer using LLM with retrieved context
        
        Args:
            query_text: The query string
            stock_id: Optional filter by stock ID
            doc_name: Optional filter by document name
            top_k: Number of top results to return (default: 3)
            ollama_url: URL of Ollama service
            model_name: Name of the model to use
            
        Returns:
            Dictionary with LLM-generated answer and sources
        """
        context, sources = self.get_context_for_llm(query_text, stock_id, doc_name, top_k)
        
        # If no context found, return message
        if not sources:
            return {
                'query': query_text,
                'answer': 'No relevant documents found for this query.',
                'context': '',
                'sources': [],
                'message': 'No documents available'
            }
        
        # Build prompt that constrains LLM to answer ONLY from provided context
        prompt = f"""You are a financial document analyst. Answer the question based ONLY on the context provided below. 

IMPORTANT RULES:
- Answer ONLY using information from the provided context
- If the context doesn't contain the answer, say "The provided documents do not contain information about this."
- Do not use external knowledge or make assumptions
- Cite which document and page you're referencing when possible

CONTEXT FROM DOCUMENTS:
{context}

QUESTION: {query_text}

ANSWER (based only on the context above):"""
        
        # Call Ollama directly
        try:
            ollama_endpoint = f"{ollama_url}/api/generate"
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(ollama_endpoint, json=payload, timeout=320)
            response.raise_for_status()
            llm_response = response.json()
            
            llm_answer = llm_response.get('response', 'Error generating answer')
            
            answer = {
                'query': query_text,
                'answer': llm_answer,
                'context': context,
                'sources': sources,
                'message': 'Answer generated from documents only'
            }
            
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            # Fallback: return context without LLM answer
            answer = {
                'query': query_text,
                'answer': f'[LLM Error: {str(e)}] Context retrieved but could not generate answer.',
                'context': context,
                'sources': sources,
                'message': 'LLM unavailable, returning context only'
            }
        
        return answer


class RAGStats:
    """Utility class for RAG system statistics and monitoring"""
    
    def __init__(self, db_connection_string: str):
        """Initialize stats collector"""
        self.db_connection_string = db_connection_string
    
    def get_db_connection(self) -> psycopg2.extensions.connection:
        """Create and return database connection"""
        return psycopg2.connect(self.db_connection_string)
    
    def get_total_stats(self) -> Dict[str, any]:
        """Get overall statistics for the RAG system"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Total chunks
            cursor.execute("SELECT COUNT(*) FROM document_embeddings;")
            total_chunks = cursor.fetchone()[0]
            
            # Total documents
            cursor.execute("SELECT COUNT(DISTINCT doc_name) FROM document_embeddings;")
            total_documents = cursor.fetchone()[0]
            
            # Total stocks with documents
            cursor.execute("SELECT COUNT(DISTINCT stock_id) FROM document_embeddings;")
            total_stocks = cursor.fetchone()[0]
            
            # Average chunks per document
            cursor.execute("""
                SELECT AVG(chunk_count) 
                FROM (
                    SELECT COUNT(*) as chunk_count 
                    FROM document_embeddings 
                    GROUP BY doc_name
                ) as doc_chunks;
            """)
            avg_chunks_per_doc = cursor.fetchone()[0]
            
            stats = {
                'total_chunks': total_chunks,
                'total_documents': total_documents,
                'total_stocks_with_docs': total_stocks,
                'avg_chunks_per_document': float(avg_chunks_per_doc) if avg_chunks_per_doc else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_stock_stats(self, stock_id: int) -> Dict[str, any]:
        """Get statistics for a specific stock"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Documents for this stock
            cursor.execute("""
                SELECT doc_name, COUNT(*) as chunk_count, MIN(created_at) as uploaded_at
                FROM document_embeddings
                WHERE stock_id = %s
                GROUP BY doc_name
                ORDER BY uploaded_at DESC;
            """, (stock_id,))
            
            documents = []
            for row in cursor.fetchall():
                documents.append({
                    'doc_name': row[0],
                    'chunk_count': row[1],
                    'uploaded_at': row[2].isoformat() if row[2] else None
                })
            
            # Total chunks for this stock
            cursor.execute("""
                SELECT COUNT(*) FROM document_embeddings WHERE stock_id = %s;
            """, (stock_id,))
            total_chunks = cursor.fetchone()[0]
            
            stats = {
                'stock_id': stock_id,
                'total_documents': len(documents),
                'total_chunks': total_chunks,
                'documents': documents
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stock stats: {e}")
            raise
        finally:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    # Example usage
    DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_MYw2ejoqv3BX@ep-green-wind-a2yx94w5-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"
    
    # Initialize retriever
    retriever = RAGRetriever(DB_CONNECTION_STRING)
    
    # Example query
    # results = retriever.query(
    #     query_text="What is Tesla's revenue growth?",
    #     stock_id=29,
    #     top_k=3
    # )
    # 
    # print("\n=== Query Results ===")
    # for i, result in enumerate(results['results'], 1):
    #     print(f"\nResult {i}:")
    #     print(f"Document: {result['doc_name']}")
    #     print(f"Page: {result['metadata'].get('page')}")
    #     print(f"Similarity: {result['similarity']:.4f}")
    #     print(f"Text: {result['chunk'][:200]}...")
    
    # Get statistics
    stats = RAGStats(DB_CONNECTION_STRING)
    total_stats = stats.get_total_stats()
    print(f"\n=== RAG System Stats ===")
    print(f"Total chunks: {total_stats['total_chunks']}")
    print(f"Total documents: {total_stats['total_documents']}")
    print(f"Total stocks: {total_stats['total_stocks_with_docs']}")
    print(f"Avg chunks/doc: {total_stats['avg_chunks_per_document']:.2f}")

