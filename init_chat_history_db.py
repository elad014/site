"""
Database initialization script for chat_history table
Run this once to create the chat_history table in your PostgreSQL database
"""
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection string (same as used in RAG service)
DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_MYw2ejoqv3BX@ep-green-wind-a2yx94w5-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"


def create_chat_history_table() -> None:
    """Create chat_history table with indexes"""
    
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
        logger.info("Connecting to PostgreSQL database...")
        connection = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = connection.cursor()
        
        logger.info("Creating chat_history table...")
        cursor.execute(create_table_query)
        connection.commit()
        
        logger.info("✓ Chat history table created successfully!")
        logger.info("✓ Indexes created successfully!")
        
        # Verify table was created
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'chat_history'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        logger.info(f"✓ Table has {len(columns)} columns:")
        for col_name, col_type in columns:
            logger.info(f"  - {col_name}: {col_type}")
        
        cursor.close()
        connection.close()
        logger.info("✓ Database connection closed")
        
    except Exception as e:
        logger.error(f"✗ Error creating chat_history table: {e}")
        raise


if __name__ == '__main__':
    create_chat_history_table()

