#!/bin/bash

# Start the complete streaming pipeline

echo "Starting Real-Time Streaming Pipeline..."
echo "======================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/{kafka,zookeeper,spark-checkpoints,spark-warehouse,prometheus,grafana}

# Start all services
echo "Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to initialize..."
sleep 30

# Create Kafka topic
echo "Creating Kafka topic..."
docker exec -it kafka kafka-topics --create \
    --topic streaming-events \
    --bootstrap-server localhost:9092 \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=86400000 \
    --config compression.type=gzip \
    2>/dev/null || echo "Topic might already exist"

# Submit Spark streaming job
echo "Submitting Spark streaming job..."
docker exec -it spark-master /opt/spark-apps/scripts/submit_streaming_job.sh

echo "======================================="
echo "Pipeline started successfully!"
echo ""
echo "Access points:"
echo "  - Kafka UI: http://localhost:8080"
echo "  - Spark UI: http://localhost:8081"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f [service-name]"
echo ""
echo "To stop the pipeline:"
echo "  ./scripts/stop_pipeline.sh"
