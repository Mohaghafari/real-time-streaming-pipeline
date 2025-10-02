#!/usr/bin/env python3
"""
Spark Structured Streaming Consumer
Processes cryptocurrency trade data from Kafka with checkpointing and watermarking
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, from_json, window, count, avg, sum as spark_sum,
    max as spark_max, min as spark_min, stddev,
    current_timestamp, to_timestamp, expr, when, lit,
    approx_count_distinct, collect_list, struct
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, BooleanType, ArrayType, TimestampType
)
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
events_processed = Counter('events_processed_total', 'Total events processed')
events_errors = Counter('events_processing_errors_total', 'Total processing errors')
processing_delay = Gauge('stream_processing_delay_seconds', 'Current processing delay')
batch_size = Histogram('batch_size_events', 'Number of events per batch')


class StreamingConsumer:
    """Spark Structured Streaming consumer for real-time crypto trade processing"""
    
    def __init__(self,
                 app_name: str = "StreamingPipeline",
                 kafka_servers: str = "localhost:9092",
                 topic: str = "streaming-events",
                 checkpoint_location: str = "/opt/spark-checkpoints",
                 output_path: str = "/opt/spark-warehouse"):
        """
        Initialize the streaming consumer
        
        Args:
            app_name: Spark application name
            kafka_servers: Kafka bootstrap servers
            topic: Kafka topic to consume from
            checkpoint_location: Path for checkpointing
            output_path: Path for output data
        """
        self.app_name = app_name
        self.kafka_servers = kafka_servers
        self.topic = topic
        self.checkpoint_location = checkpoint_location
        self.output_path = output_path
        self.spark = None
        
    def create_spark_session(self) -> SparkSession:
        """Create and configure Spark session"""
        spark = SparkSession.builder \
            .appName(self.app_name) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.streaming.stateStore.providerClass", 
                    "org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider") \
            .config("spark.sql.streaming.checkpointLocation", self.checkpoint_location) \
            .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
            .config("spark.sql.streaming.stateStore.compression.codec", "lz4") \
            .config("spark.sql.shuffle.partitions", "10") \
            .config("spark.streaming.backpressure.enabled", "true") \
            .config("spark.sql.streaming.kafka.consumer.cache.enabled", "true") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        return spark
    
    def get_event_schema(self) -> StructType:
        """Define the schema for crypto trade events"""
        return StructType([
            StructField("event_id", StringType(), False),
            StructField("event_type", StringType(), False),
            StructField("symbol", StringType(), False),
            StructField("price", DoubleType(), False),
            StructField("quantity", DoubleType(), False),
            StructField("trade_time", IntegerType(), False),
            StructField("timestamp", StringType(), False),
            StructField("buyer_is_maker", BooleanType(), True),
            StructField("trade_id", IntegerType(), True)
        ])
    
    def read_kafka_stream(self) -> DataFrame:
        """Read streaming data from Kafka"""
        return self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_servers) \
            .option("subscribe", self.topic) \
            .option("startingOffsets", "latest") \
            .option("maxOffsetsPerTrigger", 10000) \
            .option("kafka.consumer.commit.groupid", "spark-streaming-consumer") \
            .option("failOnDataLoss", "false") \
            .load()
    
    def parse_events(self, df: DataFrame) -> DataFrame:
        """Parse JSON events from Kafka messages"""
        schema = self.get_event_schema()
        
        return df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)") \
            .select(
                col("key"),
                from_json(col("value"), schema).alias("data")
            ) \
            .select("key", "data.*") \
            .withColumn("event_time", to_timestamp(col("timestamp"))) \
            .withColumn("processing_time", current_timestamp())
    
    def calculate_aggregations(self, df: DataFrame) -> Dict[str, DataFrame]:
        """Calculate various aggregations on crypto trade stream"""
        # Apply watermarking for late data handling (1 minute for crypto)
        watermarked_df = df.withWatermark("event_time", "1 minute")
        
        aggregations = {}
        
        # 1. Trade counts and volume by symbol (1-minute windows)
        aggregations['trade_metrics'] = watermarked_df \
            .groupBy(
                window(col("event_time"), "1 minute"),
                col("symbol")
            ) \
            .agg(
                count("*").alias("trade_count"),
                spark_sum("quantity").alias("total_volume"),
                avg("price").alias("avg_price"),
                spark_min("price").alias("low_price"),
                spark_max("price").alias("high_price")
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("symbol"),
                col("trade_count"),
                col("total_volume"),
                col("avg_price"),
                col("low_price"),
                col("high_price")
            )
        
        # 2. Price changes (5-minute windows)
        aggregations['price_changes'] = watermarked_df \
            .groupBy(
                window(col("event_time"), "5 minutes"),
                col("symbol")
            ) \
            .agg(
                spark_min("price").alias("open_price"),
                spark_max("price").alias("high_price"),
                spark_min("price").alias("low_price"),
                avg("price").alias("close_price"),
                spark_sum("quantity").alias("volume"),
                count("*").alias("trade_count")
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("symbol"),
                col("open_price"),
                col("high_price"),
                col("low_price"),
                col("close_price"),
                col("volume"),
                col("trade_count")
            )
        
        # 3. Buy vs Sell pressure (1-minute windows)
        aggregations['buy_sell_pressure'] = watermarked_df \
            .groupBy(
                window(col("event_time"), "1 minute"),
                col("symbol"),
                col("buyer_is_maker")
            ) \
            .agg(
                count("*").alias("count"),
                spark_sum("quantity").alias("volume")
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("symbol"),
                col("buyer_is_maker"),
                col("count"),
                col("volume")
            )
        
        return aggregations
    
    def write_stream_output(self, df: DataFrame, query_name: str, output_mode: str = "append"):
        """Write streaming dataframe to output"""
        checkpoint_path = os.path.join(self.checkpoint_location, query_name)
        output_table = os.path.join(self.output_path, query_name)
        
        query = df.writeStream \
            .outputMode(output_mode) \
            .format("parquet") \
            .option("path", output_table) \
            .option("checkpointLocation", checkpoint_path) \
            .trigger(processingTime="30 seconds") \
            .queryName(query_name) \
            .start()
        
        return query
    
    def monitor_queries(self, queries: list):
        """Monitor streaming queries and update metrics"""
        while any(q.isActive for q in queries):
            for query in queries:
                if query.isActive:
                    progress = query.lastProgress
                    if progress:
                        # Update Prometheus metrics
                        batch_size.observe(progress.get("numInputRows", 0))
                        
                        # Calculate processing delay
                        if "durationMs" in progress:
                            for duration_type, duration_ms in progress["durationMs"].items():
                                if duration_type == "triggerExecution":
                                    processing_delay.set(duration_ms / 1000.0)
                        
                        # Log progress
                        logger.info(f"Query: {query.name}")
                        logger.info(f"  Batch ID: {progress.get('batchId', 'N/A')}")
                        logger.info(f"  Input Rows: {progress.get('numInputRows', 0)}")
                        logger.info(f"  Processing Time: {progress.get('durationMs', {}).get('triggerExecution', 0)}ms")
                    
                    # Check for exceptions
                    if query.exception():
                        logger.error(f"Query {query.name} failed: {query.exception()}")
                        events_errors.inc()
            
            # Sleep before next check
            import time
            time.sleep(10)
    
    def run(self):
        """Run the streaming consumer"""
        try:
            # Start Prometheus metrics server
            start_http_server(8001)
            logger.info("Prometheus metrics available at http://localhost:8001")
            
            # Create Spark session
            self.spark = self.create_spark_session()
            logger.info(f"Created Spark session: {self.app_name}")
            
            # Read from Kafka
            kafka_df = self.read_kafka_stream()
            
            # Parse events
            events_df = self.parse_events(kafka_df)
            
            # Calculate aggregations
            aggregations = self.calculate_aggregations(events_df)
            
            # Start all streaming queries
            queries = []
            
            # Write raw events (for replay and debugging)
            raw_query = self.write_stream_output(events_df, "raw_events")
            queries.append(raw_query)
            
            # Write aggregations
            for agg_name, agg_df in aggregations.items():
                query = self.write_stream_output(agg_df, agg_name, "append")
                queries.append(query)
            
            logger.info(f"Started {len(queries)} streaming queries")
            
            # Monitor queries
            self.monitor_queries(queries)
            
        except KeyboardInterrupt:
            logger.info("Shutting down streaming consumer...")
        except Exception as e:
            logger.error(f"Error in streaming consumer: {e}")
            raise
        finally:
            if self.spark:
                self.spark.stop()


def main():
    """Main entry point"""
    # Get configuration from environment
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    topic = os.getenv('TOPIC_NAME', 'streaming-events')
    checkpoint_location = os.getenv('CHECKPOINT_LOCATION', '/opt/spark-checkpoints')
    output_path = os.getenv('OUTPUT_PATH', '/opt/spark-warehouse')
    
    # Create and run consumer
    consumer = StreamingConsumer(
        kafka_servers=kafka_servers,
        topic=topic,
        checkpoint_location=checkpoint_location,
        output_path=output_path
    )
    
    consumer.run()


if __name__ == '__main__':
    main()
