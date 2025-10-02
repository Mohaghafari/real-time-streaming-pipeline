#!/usr/bin/env python3
"""
Event Generator for Real-Time Streaming Pipeline
Generates synthetic events at a configurable rate (default: 50K events/hour)
"""

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from kafka import KafkaProducer
from kafka.errors import KafkaError
from prometheus_client import Counter, Histogram, start_http_server
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
events_produced = Counter('events_produced_total', 'Total number of events produced')
events_failed = Counter('events_failed_total', 'Total number of failed events')
event_latency = Histogram('event_production_latency_seconds', 'Event production latency')


class EventGenerator:
    """Generates synthetic events for the streaming pipeline"""
    
    def __init__(self, 
                 bootstrap_servers: str = 'localhost:9092',
                 topic: str = 'streaming-events',
                 events_per_second: float = 14):  # ~50K events/hour
        """
        Initialize the event generator
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Kafka topic to produce to
            events_per_second: Target event production rate
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.events_per_second = events_per_second
        self.producer = None
        
        # Event types and their weights
        self.event_types = {
            'user_login': 0.25,
            'page_view': 0.30,
            'item_click': 0.20,
            'purchase': 0.10,
            'cart_add': 0.10,
            'search': 0.05
        }
        
        # Sample data for generating realistic events
        self.users = [f"user_{i:04d}" for i in range(1, 1001)]
        self.items = [f"item_{i:04d}" for i in range(1, 501)]
        self.categories = ['electronics', 'clothing', 'books', 'home', 'sports', 'toys']
        self.pages = ['home', 'product', 'category', 'search', 'cart', 'checkout']
        self.devices = ['mobile', 'desktop', 'tablet']
        self.locations = ['US', 'UK', 'CA', 'DE', 'FR', 'JP', 'AU', 'BR']
        
    def connect(self):
        """Connect to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Ensure at-least-once delivery
                retries=3,
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                compression_type='gzip',
                batch_size=16384,
                linger_ms=10
            )
            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def generate_event(self) -> Dict[str, Any]:
        """Generate a synthetic event"""
        event_type = random.choices(
            list(self.event_types.keys()),
            weights=list(self.event_types.values())
        )[0]
        
        user_id = random.choice(self.users)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        base_event = {
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'user_id': user_id,
            'timestamp': timestamp,
            'device': random.choice(self.devices),
            'location': random.choice(self.locations),
            'session_id': f"session_{user_id}_{random.randint(1000, 9999)}"
        }
        
        # Add event-specific fields
        if event_type == 'user_login':
            base_event.update({
                'login_method': random.choice(['email', 'social', 'sso']),
                'success': random.random() > 0.05  # 95% success rate
            })
        
        elif event_type == 'page_view':
            base_event.update({
                'page': random.choice(self.pages),
                'referrer': random.choice(['search', 'direct', 'social', 'email']),
                'duration_seconds': random.randint(5, 300)
            })
        
        elif event_type == 'item_click':
            base_event.update({
                'item_id': random.choice(self.items),
                'category': random.choice(self.categories),
                'position': random.randint(1, 20)
            })
        
        elif event_type == 'purchase':
            num_items = random.randint(1, 5)
            items = random.sample(self.items, num_items)
            base_event.update({
                'order_id': f"order_{uuid.uuid4().hex[:8]}",
                'items': items,
                'quantities': [random.randint(1, 3) for _ in items],
                'total_amount': round(random.uniform(10, 500), 2),
                'currency': 'USD',
                'payment_method': random.choice(['credit_card', 'paypal', 'apple_pay'])
            })
        
        elif event_type == 'cart_add':
            base_event.update({
                'item_id': random.choice(self.items),
                'quantity': random.randint(1, 3),
                'category': random.choice(self.categories),
                'price': round(random.uniform(5, 200), 2)
            })
        
        elif event_type == 'search':
            search_terms = ['laptop', 'shoes', 'book', 'phone', 'watch', 'bag']
            base_event.update({
                'search_query': random.choice(search_terms),
                'results_count': random.randint(0, 100),
                'clicked_position': random.randint(0, 10) if random.random() > 0.3 else None
            })
        
        return base_event
    
    def produce_event(self, event: Dict[str, Any]):
        """Produce event to Kafka"""
        try:
            with event_latency.time():
                key = event['user_id']
                future = self.producer.send(self.topic, key=key, value=event)
                # Block until sent (for guaranteed delivery)
                future.get(timeout=10)
            events_produced.inc()
            logger.debug(f"Produced event: {event['event_id']}")
        except KafkaError as e:
            events_failed.inc()
            logger.error(f"Failed to produce event: {e}")
            raise
    
    def run(self):
        """Run the event generator"""
        logger.info(f"Starting event generation at {self.events_per_second} events/second")
        
        # Start Prometheus metrics server
        start_http_server(8000)
        logger.info("Prometheus metrics available at http://localhost:8000")
        
        # Connect to Kafka
        self.connect()
        
        # Calculate sleep time between events
        sleep_time = 1.0 / self.events_per_second
        
        events_count = 0
        start_time = time.time()
        
        try:
            while True:
                # Generate and produce event
                event = self.generate_event()
                self.produce_event(event)
                
                events_count += 1
                
                # Log progress every 1000 events
                if events_count % 1000 == 0:
                    elapsed = time.time() - start_time
                    rate = events_count / elapsed
                    logger.info(f"Produced {events_count} events. Rate: {rate:.2f} events/second")
                
                # Sleep to maintain target rate
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Shutting down event generator...")
        except Exception as e:
            logger.error(f"Error in event generation: {e}")
            raise
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
            
            # Log final statistics
            elapsed = time.time() - start_time
            rate = events_count / elapsed if elapsed > 0 else 0
            logger.info(f"Total events produced: {events_count}")
            logger.info(f"Average rate: {rate:.2f} events/second")
            logger.info(f"Target rate: {self.events_per_second} events/second")


def main():
    """Main entry point"""
    # Get configuration from environment variables
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    topic = os.getenv('TOPIC_NAME', 'streaming-events')
    events_per_second = float(os.getenv('EVENTS_PER_SECOND', '14'))  # ~50K/hour
    
    # Create and run generator
    generator = EventGenerator(
        bootstrap_servers=bootstrap_servers,
        topic=topic,
        events_per_second=events_per_second
    )
    
    generator.run()


if __name__ == '__main__':
    main()
