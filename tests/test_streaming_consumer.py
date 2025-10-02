"""
Tests for the Streaming Consumer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from consumer.streaming_consumer import StreamingConsumer


class TestStreamingConsumer:
    """Test cases for StreamingConsumer class"""
    
    @pytest.fixture
    def consumer(self):
        """Create a StreamingConsumer instance for testing"""
        return StreamingConsumer(
            app_name="TestStreamingPipeline",
            kafka_servers="localhost:9092",
            topic="test-events",
            checkpoint_location="/tmp/test-checkpoints",
            output_path="/tmp/test-output"
        )
    
    def test_init(self, consumer):
        """Test StreamingConsumer initialization"""
        assert consumer.app_name == "TestStreamingPipeline"
        assert consumer.kafka_servers == "localhost:9092"
        assert consumer.topic == "test-events"
        assert consumer.checkpoint_location == "/tmp/test-checkpoints"
        assert consumer.output_path == "/tmp/test-output"
        assert consumer.spark is None
    
    def test_get_event_schema(self, consumer):
        """Test event schema definition"""
        schema = consumer.get_event_schema()
        
        # Check that it's a StructType
        assert isinstance(schema, StructType)
        
        # Check required fields
        field_names = [field.name for field in schema.fields]
        required_fields = ['event_id', 'event_type', 'user_id', 'timestamp']
        for field in required_fields:
            assert field in field_names
        
        # Check field types
        field_dict = {field.name: field for field in schema.fields}
        assert isinstance(field_dict['event_id'].dataType, StringType)
        assert field_dict['event_id'].nullable is False
        assert field_dict['event_type'].nullable is False
        assert field_dict['user_id'].nullable is False
    
    @patch('pyspark.sql.SparkSession.builder')
    def test_create_spark_session(self, mock_builder, consumer):
        """Test Spark session creation"""
        # Setup mock
        mock_spark = Mock(spec=SparkSession)
        mock_spark.sparkContext = Mock()
        mock_builder_chain = Mock()
        mock_builder_chain.appName.return_value = mock_builder_chain
        mock_builder_chain.config.return_value = mock_builder_chain
        mock_builder_chain.getOrCreate.return_value = mock_spark
        mock_builder.return_value = mock_builder_chain
        
        # Create session
        spark = consumer.create_spark_session()
        
        # Verify
        assert spark == mock_spark
        mock_builder_chain.appName.assert_called_with("TestStreamingPipeline")
        
        # Check some important configs were set
        config_calls = mock_builder_chain.config.call_args_list
        config_dict = {call[0][0]: call[0][1] for call in config_calls}
        
        assert config_dict.get("spark.sql.adaptive.enabled") == "true"
        assert config_dict.get("spark.streaming.backpressure.enabled") == "true"
        assert "spark.sql.streaming.checkpointLocation" in config_dict
    
    @patch('pyspark.sql.SparkSession')
    def test_read_kafka_stream(self, mock_spark_session, consumer):
        """Test reading from Kafka stream"""
        # Setup mock
        mock_spark = Mock()
        mock_readstream = Mock()
        mock_format = Mock()
        mock_option = Mock()
        mock_load = Mock()
        
        # Chain the calls
        mock_spark.readStream = mock_readstream
        mock_readstream.format.return_value = mock_format
        mock_format.option.return_value = mock_option
        mock_option.option.return_value = mock_option
        mock_option.load.return_value = mock_load
        
        consumer.spark = mock_spark
        
        # Read stream
        result = consumer.read_kafka_stream()
        
        # Verify
        mock_readstream.format.assert_called_with("kafka")
        
        # Check options were set
        option_calls = mock_option.option.call_args_list
        option_dict = {}
        for i in range(0, len(option_calls), 2):
            if i + 1 < len(option_calls):
                key = option_calls[i][0][0]
                value = option_calls[i + 1][0][1]
                option_dict[key] = value
        
        assert mock_load.called
    
    @patch('pyspark.sql.DataFrame')
    def test_parse_events(self, mock_df_class, consumer):
        """Test parsing JSON events"""
        # Setup mock DataFrames
        mock_input_df = Mock()
        mock_select_df = Mock()
        mock_parsed_df = Mock()
        mock_with_time_df = Mock()
        mock_final_df = Mock()
        
        # Chain the transformations
        mock_input_df.selectExpr.return_value = mock_select_df
        mock_select_df.select.return_value = mock_parsed_df
        mock_parsed_df.select.return_value = mock_with_time_df
        mock_with_time_df.withColumn.return_value = mock_final_df
        mock_final_df.withColumn.return_value = mock_final_df
        
        consumer.spark = Mock()
        
        # Parse events
        result = consumer.parse_events(mock_input_df)
        
        # Verify transformations
        mock_input_df.selectExpr.assert_called_once()
        assert "CAST(key AS STRING)" in mock_input_df.selectExpr.call_args[0]
        assert "CAST(value AS STRING)" in mock_input_df.selectExpr.call_args[0]
    
    def test_monitor_queries(self, consumer):
        """Test query monitoring"""
        # Create mock queries
        mock_query1 = Mock()
        mock_query1.isActive = True
        mock_query1.name = "test_query"
        mock_query1.lastProgress = {
            "batchId": 1,
            "numInputRows": 100,
            "durationMs": {"triggerExecution": 500}
        }
        mock_query1.exception.return_value = None
        
        # Create a counter to stop the loop
        call_count = [0]
        
        def check_active():
            call_count[0] += 1
            return call_count[0] < 2
        
        mock_query1.isActive = property(lambda self: check_active())
        
        # Monitor queries (will run once then stop)
        with patch('time.sleep'):
            consumer.monitor_queries([mock_query1])
        
        # Verify monitoring happened
        assert mock_query1.exception.called


class TestStreamingConsumerIntegration:
    """Integration tests for StreamingConsumer"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get('RUN_INTEGRATION_TESTS'),
        reason="Integration tests require Spark environment"
    )
    def test_full_pipeline(self):
        """Test the full streaming pipeline with test data"""
        # This would require a full Spark environment
        # Typically run in a Docker container or CI environment
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
