# Real-Time Streaming Pipeline

A real-time data pipeline using Kafka and Spark Structured Streaming for processing e-commerce events. Built this to learn more about distributed stream processing and get hands-on with production data engineering patterns.

## What It Does

Simulates a high-volume e-commerce platform processing user events (logins, purchases, page views) in real-time. The pipeline handles about 65K events per hour with proper fault tolerance and monitoring.

**Tech Stack**: Kafka, Spark, Docker, Prometheus, Grafana, Python

## Why I Built This

Wanted to understand how companies like Uber and Netflix handle real-time data at scale. This project helped me learn:
- How Kafka handles message streaming and guarantees delivery
- Spark Structured Streaming for real-time aggregations
- Building fault-tolerant systems with checkpointing
- Monitoring production data pipelines
- Docker orchestration for complex systems

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Event     │────▶│    Kafka    │────▶│ Spark Structured │────▶│   Data      │
│ Generator   │     │   Broker    │     │   Streaming      │     │ Warehouse   │
└─────────────┘     └─────────────┘     └──────────────────┘     └─────────────┘
                           │                      │
                           ▼                      ▼
                    ┌─────────────┐        ┌─────────────┐
                    │ Prometheus  │◀───────│  Metrics    │
                    └─────────────┘        │ Exporter    │
                           │               └─────────────┘
                           ▼
                    ┌─────────────┐
                    │   Grafana   │
                    └─────────────┘
```

## Project Structure

```
.
├── docker-compose.yml          # Docker services configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── config/                     # Configuration files
│   ├── prometheus.yml         # Prometheus configuration
│   └── grafana/               # Grafana dashboards and datasources
├── docker/                     # Docker build files
│   ├── kafka/                 # Kafka-related Dockerfiles
│   └── spark/                 # Spark Dockerfile
├── src/                        # Source code
│   ├── producer/              # Kafka event generator
│   ├── consumer/              # Spark streaming consumer
│   ├── monitoring/            # Monitoring utilities
│   └── utils/                 # Shared utilities
├── scripts/                    # Operational scripts
├── data/                       # Data storage (git-ignored)
└── tests/                      # Test files
```

## Getting Started

You'll need Docker installed with at least 8GB RAM available.

1. Clone and start:
```bash
git clone https://github.com/Mohaghafari/real-time-streaming-pipeline.git
cd real-time-streaming-pipeline
```

2. Start everything:
```bash
docker-compose up -d
```

3. Check it's working:
```bash
# See events flowing through Kafka
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic streaming-events \
  --max-messages 5
```

4. Access the UIs:
- Kafka UI: http://localhost:8080
- Spark UI: http://localhost:8081
- Grafana: http://localhost:3000 (admin/admin)

To stop: `docker-compose down`

## Event Types

The producer generates these event types:

```json
{
  "event_id": "uuid",
  "event_type": "user_login|page_view|item_click|purchase|cart_add|search",
  "user_id": "string",
  "timestamp": "ISO-8601",
  "device": "mobile|desktop|tablet",
  "location": "country_code",
  "session_id": "string",
  // Additional fields based on event_type
}
```

## Key Features

**Fault Tolerance**
- Spark checkpointing for recovery
- Kafka replication and acks
- At-least-once delivery semantics

**Handling Late Data**
- 5-minute watermark for late arrivals
- Event-time processing (not processing-time)

**Monitoring**
- Prometheus metrics from producer and consumer
- Grafana dashboards for visualization
- Real-time throughput and latency tracking

## Performance

Currently processing around 18 events/second (~65K/hour). Main metrics tracked:
- Total events produced/processed
- Processing latency
- Batch sizes
- Error rates

Grafana dashboards show these in real-time.

## Testing

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Troubleshooting

If things aren't working:
- Check Docker has enough memory (8GB+)
- Make sure ports aren't already in use: 3000, 8080, 8081, 9090, 9092
- Look at logs: `docker-compose logs -f`
- Kafka takes ~30 seconds to start up properly

## What I Learned

- Kafka's guarantee mechanisms and how they trade off with performance
- Spark Structured Streaming's micro-batch model vs true streaming
- Why checkpointing is critical (learned this the hard way)
- Watermarking for handling late data
- Docker networking can be tricky with Kafka
- Prometheus + Grafana are powerful once you get them configured

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Future Improvements

Some things I'd like to add:
- Exactly-once semantics (currently at-least-once)
- More complex aggregations (sessionization, funnel analysis)
- Schema evolution handling
- Better error handling and dead letter queues
- Kubernetes deployment configs

## License

MIT

## Contact

Mohammad Ghafari - [mmqaffari@gmail.com](mailto:mmqaffari@gmail.com)

[LinkedIn](https://www.linkedin.com/in/mohaghafari/) | [GitHub](https://github.com/Mohaghafari)
