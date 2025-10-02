#!/bin/bash

# Stop the streaming pipeline

echo "Stopping Real-Time Streaming Pipeline..."
echo "======================================="

# Stop all services
echo "Stopping Docker services..."
docker-compose down

# Optional: Remove volumes (uncomment if needed)
# echo "Removing data volumes..."
# docker-compose down -v

echo "======================================="
echo "Pipeline stopped successfully!"
