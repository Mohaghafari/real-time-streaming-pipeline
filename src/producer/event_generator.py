#!/usr/bin/env python3
"""
Crypto Price Stream Producer
Streams real-time cryptocurrency prices from Binance WebSocket API
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
import websocket
import threading

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
events_produced = Counter('events_produced_total', 'Total number of price updates produced')
events_failed = Counter('events_failed_total', 'Total number of failed events')
event_latency = Histogram('event_production_latency_seconds', 'Event production latency')


class CryptoPriceProducer:
    """Streams real-time cryptocurrency prices from Binance"""
    
    def __init__(self, 
                 bootstrap_servers: str = 'localhost:9092',
                 topic: str = 'streaming-events'):
        """
        Initialize the crypto price producer
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Kafka topic to produce to
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = None
        self.ws = None
        self.running = False
        
        # Popular trading pairs to stream
        self.symbols = [
            'btcusdt',    # Bitcoin
            'ethusdt',    # Ethereum
            'bnbusdt',    # Binance Coin
            'adausdt',    # Cardano
            'solusdt',    # Solana
            'xrpusdt',    # Ripple
            'dotusdt',    # Polkadot
            'dogeusdt',   # Dogecoin
            'maticusdt',  # Polygon
            'linkusdt',   # Chainlink
        ]
        
        # Binance WebSocket URL for real-time trades
        streams = '/'.join([f"{s}@trade" for s in self.symbols])
        self.ws_url = f"wss://stream.binance.com:9443/stream?streams={streams}"
        
    def connect_kafka(self):
        """Connect to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Ensure at-least-once delivery
                retries=3,
                max_in_flight_requests_per_connection=1,
                compression_type='gzip',
                batch_size=16384,
                linger_ms=10
            )
            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            # Binance sends wrapped messages
            if 'data' in data:
                trade_data = data['data']
                
                # Transform to our event format
                event = {
                    'event_id': str(uuid.uuid4()),
                    'event_type': 'trade',
                    'symbol': trade_data['s'],  # e.g., BTCUSDT
                    'price': float(trade_data['p']),
                    'quantity': float(trade_data['q']),
                    'trade_time': trade_data['T'],  # Trade timestamp
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'buyer_is_maker': trade_data['m'],  # True if buyer is maker
                    'trade_id': trade_data['t'],
                }
                
                # Send to Kafka
                self.produce_event(event)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            events_failed.inc()
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.running = False
    
    def on_open(self, ws):
        """Handle WebSocket open"""
        logger.info("WebSocket connection opened")
        logger.info(f"Streaming {len(self.symbols)} crypto pairs from Binance")
    
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
        """Run the crypto price stream"""
        logger.info("Starting real-time crypto price streaming from Binance")
        
        # Start Prometheus metrics server
        start_http_server(8000)
        logger.info("Prometheus metrics available at http://localhost:8000")
        
        # Connect to Kafka
        self.connect_kafka()
        
        # Start WebSocket connection
        self.running = True
        
        try:
            # Create WebSocket connection
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            # Run WebSocket in forever loop (will reconnect on disconnect)
            self.ws.run_forever()
                
        except KeyboardInterrupt:
            logger.info("Shutting down crypto price stream...")
        except Exception as e:
            logger.error(f"Error in price streaming: {e}")
            raise
        finally:
            self.running = False
            if self.ws:
                self.ws.close()
            if self.producer:
                self.producer.flush()
                self.producer.close()


def main():
    """Main entry point"""
    # Get configuration from environment variables
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    topic = os.getenv('TOPIC_NAME', 'streaming-events')
    
    # Create and run producer
    producer = CryptoPriceProducer(
        bootstrap_servers=bootstrap_servers,
        topic=topic
    )
    
    producer.run()


if __name__ == '__main__':
    main()
