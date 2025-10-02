#!/usr/bin/env python3
"""
Spark Structured Streaming Consumer
Processes events from Kafka with checkpointing and watermarking
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
    """Spark Structured Streaming consumer for real-time event processing"""
    
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
        """Define the schema for incoming events"""
        return StructType([
            StructField("event_id", StringType(), False),
            StructField("event_type", StringType(), False),
            StructField("user_id", StringType(), False),
            StructField("timestamp", StringType(), False),
            StructField("device", StringType(), True),
            StructField("location", StringType(), True),
            StructField("session_id", StringType(), True),
            # Event-specific fields (nullable)
            StructField("login_method", StringType(), True),
            StructField("success", BooleanType(), True),
            StructField("page", StringType(), True),
            StructField("referrer", StringType(), True),
            StructField("duration_seconds", IntegerType(), True),
            StructField("item_id", StringType(), True),
            StructField("category", StringType(), True),
            StructField("position", IntegerType(), True),
            StructField("order_id", StringType(), True),
            StructField("items", ArrayType(StringType()), True),
            StructField("quantities", ArrayType(IntegerType()), True),
            StructField("total_amount", DoubleType(), True),
            StructField("currency", StringType(), True),
            StructField("payment_method", StringType(), True),
            StructField("quantity", IntegerType(), True),
            StructField("price", DoubleType(), True),
            StructField("search_query", StringType(), True),
            StructField("results_count", IntegerType(), True),
            StructField("clicked_position", IntegerType(), True)
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
        """Calculate various aggregations on the event stream"""
        # Apply watermarking for late data handling (5 minutes)
        watermarked_df = df.withWatermark("event_time", "5 minutes")
        
        aggregations = {}
        
        # 1. Event counts by type (1-minute tumbling windows)
        aggregations['event_counts'] = watermarked_df \
            .groupBy(
                window(col("event_time"), "1 minute"),
                col("event_type")
            ) \
            .agg(
                count("*").alias("count"),
                approx_count_distinct("user_id").alias("unique_users")
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("event_type"),
                col("count"),
                col("unique_users")
            )
        
        # 2. User activity metrics (5-minute sliding windows)
        aggregations['user_activity'] = watermarked_df \
            .groupBy(
                window(col("event_time"), "5 minutes", "1 minute"),
                col("user_id")
            ) \
            .agg(
                count("*").alias("event_count"),
                collect_list("event_type").alias("event_types"),
                spark_min("event_time").alias("first_event"),
                spark_max("event_time").alias("last_event")
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("user_id"),
                col("event_count"),
                col("event_types"),
                col("first_event"),
                col("last_event")
            )
        
        # 3. Purchase analytics (for purchase events)
        purchase_df = watermarked_df.filter(col("event_type") == "purchase")
        if purchase_df:
            aggregations['purchase_metrics'] = purchase_df \
                .groupBy(window(col("event_time"), "10 minutes")) \
                .agg(
                    count("*").alias("total_orders"),
                    spark_sum("total_amount").alias("total_revenue"),
                    avg("total_amount").alias("avg_order_value"),
                    spark_max("total_amount").alias("max_order_value"),
                    spark_min("total_amount").alias("min_order_value"),
                    approx_count_distinct("user_id").alias("unique_buyers")
                ) \
                .select(
                    col("window.start").alias("window_start"),
                    col("window.end").alias("window_end"),
                    col("total_orders"),
                    col("total_revenue"),
                    col("avg_order_value"),
                    col("max_order_value"),
                    col("min_order_value"),
                    col("unique_buyers")
                )
        
        # 4. Real-time session analytics
        aggregations['session_metrics'] = watermarked_df \
            .groupBy(
                window(col("event_time"), "5 minutes"),
                col("session_id")
            ) \
            .agg(
                count("*").alias("events_in_session"),
                collect_list("event_type").alias("session_events"),
                spark_min("event_time").alias("session_start"),
                spark_max("event_time").alias("session_end")
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("session_id"),
                col("events_in_session"),
                col("session_events"),
                col("session_start"),
                col("session_end"),
                (col("session_end").cast("long") - col("session_start").cast("long")).alias("session_duration_seconds")
            )
        
        # 5. Device and location statistics
        aggregations['device_stats'] = watermarked_df \
            .groupBy(
                window(col("event_time"), "10 minutes"),
                col("device"),
                col("location")
            ) \
            .agg(
                count("*").alias("event_count"),
                approx_count_distinct("user_id").alias("unique_users"),
                approx_count_distinct("session_id").alias("unique_sessions")
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
