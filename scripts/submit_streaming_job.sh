#!/bin/bash

# Submit Spark Structured Streaming Job
# This script submits the streaming consumer to the Spark cluster

SPARK_HOME="/opt/bitnami/spark"
SPARK_MASTER="spark://spark-master:7077"
APP_PATH="/opt/spark-apps/consumer/streaming_consumer.py"

echo "Submitting Spark Streaming Job..."
echo "Spark Master: $SPARK_MASTER"
echo "Application: $APP_PATH"

$SPARK_HOME/bin/spark-submit \
  --master $SPARK_MASTER \
  --deploy-mode client \
  --driver-memory 2g \
  --executor-memory 2g \
  --executor-cores 2 \
  --num-executors 1 \
  --conf spark.streaming.kafka.consumer.poll.ms=1000 \
  --conf spark.streaming.backpressure.enabled=true \
  --conf spark.streaming.backpressure.initialRate=1000 \
  --conf spark.sql.streaming.checkpointLocation=/opt/spark-checkpoints \
  --conf spark.sql.streaming.stateStore.providerClass=org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider \
  --conf spark.sql.adaptive.enabled=true \
  --conf spark.sql.adaptive.coalescePartitions.enabled=true \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  $APP_PATH
