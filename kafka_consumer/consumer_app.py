import os
import json
import logging
import signal
import sys
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from db_writer import ChatHistoryWriter
from typing import Dict
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'chat_messages')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'chat_history_consumer')

# Database connection string (same as RAG service)
DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_MYw2ejoqv3BX@ep-green-wind-a2yx94w5-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"

# Global flag for graceful shutdown
running = True


def signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    running = False


def create_kafka_consumer() -> KafkaConsumer:
    """
    Create and configure Kafka consumer with retry logic
    
    Returns:
        KafkaConsumer: Configured Kafka consumer instance
    """
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                group_id=KAFKA_GROUP_ID,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=1000
            )
            logger.info(f"Successfully connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
            logger.info(f"Subscribed to topic: {KAFKA_TOPIC}")
            return consumer
        except KafkaError as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} - Failed to connect to Kafka: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Could not connect to Kafka.")
                raise


def process_message(message_data: Dict, db_writer: ChatHistoryWriter) -> None:
    """
    Process a single Kafka message and write to database
    
    Args:
        message_data: The deserialized message data
        db_writer: Database writer instance
    """
    try:
        logger.info(f"Processing message: user={message_data.get('user_name', 'unknown')}, "
                   f"query={message_data.get('query', '')[:50]}...")
        
        success = db_writer.write_chat_message(message_data)
        
        if success:
            logger.info("Message processed and written to database successfully")
        else:
            logger.error("Failed to write message to database")
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def main() -> None:
    """Main consumer loop"""
    global running
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Kafka Consumer for Chat History...")
    logger.info(f"Kafka Bootstrap Servers: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Topic: {KAFKA_TOPIC}")
    logger.info(f"Consumer Group: {KAFKA_GROUP_ID}")
    
    # Initialize database writer
    try:
        db_writer = ChatHistoryWriter(DB_CONNECTION_STRING)
        logger.info("Database writer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database writer: {e}")
        sys.exit(1)
    
    # Create Kafka consumer
    try:
        consumer = create_kafka_consumer()
    except Exception as e:
        logger.error(f"Failed to create Kafka consumer: {e}")
        sys.exit(1)
    
    # Main consumption loop
    logger.info("Starting to consume messages...")
    message_count = 0
    
    try:
        while running:
            try:
                # Poll for messages
                for message in consumer:
                    if not running:
                        break
                    
                    message_count += 1
                    logger.info(f"Received message #{message_count} from partition {message.partition}, "
                              f"offset {message.offset}")
                    
                    # Process the message
                    process_message(message.value, db_writer)
                    
            except StopIteration:
                # Consumer timeout, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in consumption loop: {e}")
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        # Cleanup
        logger.info("Cleaning up resources...")
        try:
            consumer.close()
            logger.info("Kafka consumer closed")
        except:
            pass
        
        try:
            db_writer.close()
            logger.info("Database connection closed")
        except:
            pass
        
        logger.info(f"Processed {message_count} messages total")
        logger.info("Kafka consumer shut down successfully")


if __name__ == '__main__':
    main()

