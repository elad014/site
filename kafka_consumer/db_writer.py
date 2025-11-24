import psycopg2
from psycopg2.extras import Json
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ChatHistoryWriter:
    """Writes chat history to PostgreSQL database"""
    
    def __init__(self, db_connection_string: str):
        """
        Initialize the database writer
        
        Args:
            db_connection_string: PostgreSQL connection string
        """
        self.db_connection_string = db_connection_string
        self.connection: Optional[psycopg2.extensions.connection] = None
        self.connect()
        self.create_table_if_not_exists()
    
    def connect(self) -> None:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(self.db_connection_string)
            logger.info("Successfully connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def create_table_if_not_exists(self) -> None:
        """Create chat_history table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255),
            user_name VARCHAR(255),
            query TEXT NOT NULL,
            detected_ticker VARCHAR(10),
            answer TEXT NOT NULL,
            context_used JSONB,
            model_name VARCHAR(50),
            response_time_ms INTEGER,
            timestamp TIMESTAMP DEFAULT NOW(),
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp);
        CREATE INDEX IF NOT EXISTS idx_chat_history_ticker ON chat_history(detected_ticker);
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_query)
                self.connection.commit()
                logger.info("Chat history table created/verified successfully")
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            self.connection.rollback()
            raise
    
    def write_chat_message(self, message_data: Dict) -> bool:
        """
        Write a chat message to the database
        
        Args:
            message_data: Dictionary containing chat message data
            
        Returns:
            bool: True if successful, False otherwise
        """
        insert_query = """
        INSERT INTO chat_history (
            user_id,
            user_name,
            query,
            detected_ticker,
            answer,
            context_used,
            model_name,
            response_time_ms,
            timestamp
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(insert_query, (
                    message_data.get('user_id'),
                    message_data.get('user_name'),
                    message_data.get('query'),
                    message_data.get('detected_ticker'),
                    message_data.get('answer'),
                    Json(message_data.get('context_used', {})),
                    message_data.get('model_name'),
                    message_data.get('response_time_ms'),
                    message_data.get('timestamp', datetime.now())
                ))
                self.connection.commit()
                logger.info(f"Successfully wrote chat message for user: {message_data.get('user_name', 'unknown')}")
                return True
        except Exception as e:
            logger.error(f"Failed to write chat message: {e}")
            self.connection.rollback()
            # Try to reconnect if connection was lost
            try:
                self.connect()
            except:
                pass
            return False
    
    def close(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

