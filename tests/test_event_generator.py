"""
Tests for the Event Generator
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from producer.event_generator import EventGenerator


class TestEventGenerator:
    """Test cases for EventGenerator class"""
    
    @pytest.fixture
    def generator(self):
        """Create an EventGenerator instance for testing"""
        return EventGenerator(
            bootstrap_servers='localhost:9092',
            topic='test-topic',
            events_per_second=10
        )
    
    def test_init(self, generator):
        """Test EventGenerator initialization"""
        assert generator.bootstrap_servers == 'localhost:9092'
        assert generator.topic == 'test-topic'
        assert generator.events_per_second == 10
        assert generator.producer is None
        assert len(generator.event_types) == 6
        assert len(generator.users) == 1000
        assert len(generator.items) == 500
    
    def test_generate_event_structure(self, generator):
        """Test that generated events have the correct structure"""
        event = generator.generate_event()
        
        # Check required fields
        assert 'event_id' in event
        assert 'event_type' in event
        assert 'user_id' in event
        assert 'timestamp' in event
        assert 'device' in event
        assert 'location' in event
        assert 'session_id' in event
        
        # Check field types
        assert isinstance(event['event_id'], str)
        assert event['event_type'] in generator.event_types
        assert event['user_id'] in generator.users
        assert event['device'] in generator.devices
        assert event['location'] in generator.locations
        
    def test_generate_event_types(self, generator):
        """Test that all event types can be generated"""
        event_types_generated = set()
        
        # Generate many events to ensure we get all types
        for _ in range(1000):
            event = generator.generate_event()
            event_types_generated.add(event['event_type'])
        
        # Check that we generated all event types
        assert event_types_generated == set(generator.event_types.keys())
    
    def test_user_login_event(self, generator):
        """Test user_login event specific fields"""
        # Mock random.choices to return user_login
        with patch('random.choices', return_value=['user_login']):
            event = generator.generate_event()
            
            assert event['event_type'] == 'user_login'
            assert 'login_method' in event
            assert event['login_method'] in ['email', 'social', 'sso']
            assert 'success' in event
            assert isinstance(event['success'], bool)
    
    def test_purchase_event(self, generator):
        """Test purchase event specific fields"""
        with patch('random.choices', return_value=['purchase']):
            event = generator.generate_event()
            
            assert event['event_type'] == 'purchase'
            assert 'order_id' in event
            assert 'items' in event
            assert 'quantities' in event
            assert 'total_amount' in event
            assert 'currency' in event
            assert 'payment_method' in event
            
            # Check data types
            assert isinstance(event['items'], list)
            assert isinstance(event['quantities'], list)
            assert len(event['items']) == len(event['quantities'])
            assert isinstance(event['total_amount'], float)
            assert event['currency'] == 'USD'
    
    @patch('kafka.KafkaProducer')
    def test_connect(self, mock_kafka_producer, generator):
        """Test connection to Kafka"""
        mock_producer_instance = Mock()
        mock_kafka_producer.return_value = mock_producer_instance
        
        generator.connect()
        
        # Check that KafkaProducer was created with correct parameters
        mock_kafka_producer.assert_called_once()
        call_args = mock_kafka_producer.call_args[1]
        assert call_args['bootstrap_servers'] == 'localhost:9092'
        assert call_args['acks'] == 'all'
        assert call_args['retries'] == 3
        assert call_args['compression_type'] == 'gzip'
        
        # Check that producer was assigned
        assert generator.producer == mock_producer_instance
    
    @patch('kafka.KafkaProducer')
    def test_produce_event(self, mock_kafka_producer, generator):
        """Test producing an event to Kafka"""
        # Setup mock producer
        mock_future = Mock()
        mock_future.get.return_value = None
        mock_producer_instance = Mock()
        mock_producer_instance.send.return_value = mock_future
        generator.producer = mock_producer_instance
        
        # Create and produce event
        event = generator.generate_event()
        generator.produce_event(event)
        
        # Check that send was called correctly
        mock_producer_instance.send.assert_called_once_with(
            'test-topic',
            key=event['user_id'],
            value=event
        )
        mock_future.get.assert_called_once_with(timeout=10)
    
    @patch('kafka.KafkaProducer')
    def test_produce_event_failure(self, mock_kafka_producer, generator):
        """Test handling of production failures"""
        from kafka.errors import KafkaError
        
        # Setup mock producer to raise error
        mock_producer_instance = Mock()
        mock_producer_instance.send.side_effect = KafkaError("Test error")
        generator.producer = mock_producer_instance
        
        # Create event and attempt to produce
        event = generator.generate_event()
        
        with pytest.raises(KafkaError):
            generator.produce_event(event)


class TestEventGeneratorIntegration:
    """Integration tests for EventGenerator"""
    
    @pytest.mark.integration
    @patch('time.sleep')  # Speed up test by mocking sleep
    @patch('kafka.KafkaProducer')
    def test_run_produces_events(self, mock_kafka_producer, mock_sleep):
        """Test that run() produces events at the correct rate"""
        # Setup
        generator = EventGenerator(events_per_second=100)
        
        # Mock producer
        mock_future = Mock()
        mock_future.get.return_value = None
        mock_producer_instance = Mock()
        mock_producer_instance.send.return_value = mock_future
        mock_kafka_producer.return_value = mock_producer_instance
        
        # Run for a short time then stop
        events_produced = []
        original_produce = generator.produce_event
        
        def track_produce(event):
            events_produced.append(event)
            original_produce(event)
            if len(events_produced) >= 10:
                raise KeyboardInterrupt()
        
        generator.produce_event = track_produce
        
        # Run
        generator.run()
        
        # Verify
        assert len(events_produced) >= 10
        assert mock_producer_instance.flush.called
        assert mock_producer_instance.close.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
