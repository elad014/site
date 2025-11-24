import os
import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
from typing import Dict, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class ChatMessageProducer:
    """Kafka producer for chat messages"""
    
    def __init__(self, bootstrap_servers: str = 'kafka:9092', topic: str = 'chat_messages'):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Kafka topic name
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer: Optional[KafkaProducer] = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to Kafka with retry logic"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers.split(','),
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',
                    retries=3,
                    max_in_flight_requests_per_connection=1
                )
                logger.info(f"Successfully connected to Kafka at {self.bootstrap_servers}")
                return
            except KafkaError as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} - Failed to connect to Kafka: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Could not connect to Kafka after max retries. Producer will be disabled.")
                    self.producer = None
    
    def publish_chat_message(
        self,
        user_id: Optional[str],
        user_name: Optional[str],
        query: str,
        answer: str,
        detected_ticker: Optional[str] = None,
        context_used: Optional[Dict] = None,
        model_name: str = 'llama3',
        response_time_ms: Optional[int] = None
    ) -> bool:
        """
        Publish a chat message to Kafka
        
        Args:
            user_id: User ID
            user_name: Username
            query: User's query
            answer: LLM's answer
            detected_ticker: Detected stock ticker
            context_used: RAG context chunks used
            model_name: Model name used
            response_time_ms: Response time in milliseconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.producer:
            logger.warning("Kafka producer not available. Message will not be published.")
            return False
        
        message = {
            'user_id': user_id,
            'user_name': user_name,
            'query': query,
            'detected_ticker': detected_ticker,
            'answer': answer,
            'context_used': context_used or {},
            'model_name': model_name,
            'response_time_ms': response_time_ms,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            future = self.producer.send(self.topic, value=message)
            # Wait for message to be sent (with timeout)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Message published to topic '{self.topic}' "
                       f"(partition: {record_metadata.partition}, offset: {record_metadata.offset})")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to publish message to Kafka: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing message: {e}")
            return False
    
    def close(self) -> None:
        """Close Kafka producer"""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")

