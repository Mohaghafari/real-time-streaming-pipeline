# 🚀 Real-Time Streaming Pipeline

[![Apache Kafka](https://img.shields.io/badge/Kafka-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white)](https://kafka.apache.org/)
[![Apache Spark](https://img.shields.io/badge/Spark-E25A1C?style=for-the-badge&logo=apache-spark&logoColor=white)](https://spark.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com/)

> A production-ready real-time data streaming pipeline built with Apache Kafka and Spark Structured Streaming, processing **50K+ events per hour** with at-least-once delivery guarantees.

**⚡ Live Demo**: Processing 65,000+ events/hour | **🎯 Portfolio Project** | **📚 Educational Resource**

---

## 📑 Table of Contents

- [Highlights](#-highlights)
- [Skills Demonstrated](#-skills-demonstrated)
- [Architecture](#-architecture)
- [Technology Stack](#️-technology-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Event Schema](#-event-schema)
- [Configuration](#-configuration)
- [Metrics & Monitoring](#-metrics--monitoring)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Production Deployment](#️-production-deployment)
- [Learning Resources](#-learning-resources)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## ✨ Highlights

- ⚡ **High-throughput Processing**: Handles 50,000+ events per hour (verified at 65K+)
- 🛡️ **At-least-once Delivery**: Ensures no data loss with proper acknowledgments
- 🔄 **Fault Tolerance**: Implements checkpointing and state management
- 📊 **Real-time Analytics**: Streaming aggregations with watermarking for late data
- 📈 **Monitoring & Observability**: Prometheus metrics and Grafana dashboards
- 🐳 **Dockerized Architecture**: Easy local development and deployment
- 📈 **Auto-scaling Ready**: Designed for horizontal scaling

## 🎓 Skills Demonstrated

This project showcases expertise in:

- **Distributed Systems**: Kafka cluster management, partitioning, replication
- **Stream Processing**: Spark Structured Streaming, micro-batch processing
- **Data Engineering**: ETL pipelines, schema management, data quality
- **DevOps**: Docker containerization, service orchestration, CI/CD ready
- **Monitoring**: Prometheus metrics, Grafana dashboards, alerting
- **Python Development**: Async programming, error handling, logging
- **System Design**: Fault tolerance, scalability, performance optimization

## 📊 Architecture

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

## 🛠️ Technology Stack

- **Apache Kafka**: Distributed streaming platform
- **Apache Spark**: Unified analytics engine with Structured Streaming
- **Docker & Docker Compose**: Containerization
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **Python**: Application development

## 📁 Project Structure

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

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM available for containers
- Port availability: 3000, 8080, 8081, 9090, 9092

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Mohaghafari/real-time-streaming-pipeline.git
cd real-time-streaming-pipeline
```

2. Start the pipeline:
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start all services
./scripts/start_pipeline.sh
```

3. Access the services:
- **Kafka UI**: http://localhost:8080
- **Spark UI**: http://localhost:8081
- **Grafana**: http://localhost:3000 (login: admin/admin)
- **Prometheus**: http://localhost:9090

4. Monitor the pipeline:
```bash
# View real-time metrics
docker exec -it spark-master python /opt/spark-apps/monitoring/pipeline_monitor.py

# View logs
docker-compose logs -f kafka-producer
docker-compose logs -f spark-master
```

5. Stop the pipeline:
```bash
./scripts/stop_pipeline.sh
```

## 📊 Event Schema

The pipeline processes various event types with the following base schema:

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

## 🔧 Configuration

### Adjusting Event Rate

Modify the `EVENTS_PER_SECOND` environment variable in `docker-compose.yml`:

```yaml
kafka-producer:
  environment:
    - EVENTS_PER_SECOND=14  # ~50K events/hour
```

### Spark Configuration

Key Spark settings in `src/consumer/streaming_consumer.py`:

```python
.config("spark.sql.shuffle.partitions", "10")
.config("spark.streaming.backpressure.enabled", "true")
.config("spark.sql.streaming.checkpointLocation", checkpoint_location)
```

### Kafka Configuration

Kafka settings in `docker-compose.yml`:

```yaml
KAFKA_LOG_RETENTION_HOURS: 24
KAFKA_COMPRESSION_TYPE: gzip
KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
```

## 📈 Metrics & Monitoring

### Available Metrics

- **Producer Metrics**:
  - `events_produced_total`: Total events generated
  - `events_failed_total`: Failed event productions
  - `event_production_latency_seconds`: Production latency

- **Consumer Metrics**:
  - `events_processed_total`: Total events processed
  - `stream_processing_delay_seconds`: Current processing delay
  - `batch_size_events`: Events per batch histogram

### Grafana Dashboard

The pre-configured dashboard includes:
- Real-time event processing rate
- Processing delay gauge
- Event distribution by type
- Batch size percentiles
- Success rate statistics

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v --cov=src
```

## 🔍 Troubleshooting

### Common Issues

1. **Kafka Connection Errors**:
   ```bash
   # Check Kafka is running
   docker-compose ps kafka
   
   # View Kafka logs
   docker-compose logs kafka
   ```

2. **Spark Job Failures**:
   ```bash
   # Check Spark logs
   docker-compose logs spark-master
   
   # Access Spark shell
   docker exec -it spark-master /opt/bitnami/spark/bin/spark-shell
   ```

3. **High Memory Usage**:
   - Adjust Spark worker memory in `docker-compose.yml`
   - Reduce batch size with `maxOffsetsPerTrigger`

### Performance Tuning

1. **Increase Throughput**:
   - Add more Kafka partitions
   - Scale Spark workers
   - Optimize batch intervals

2. **Reduce Latency**:
   - Decrease trigger intervals
   - Enable adaptive query execution
   - Use memory-optimized instances

## 🏗️ Production Deployment

### Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests (to be added).

### AWS Deployment

1. Use Amazon MSK for Kafka
2. Deploy Spark on EMR or EKS
3. Use S3 for checkpointing and data storage
4. Set up CloudWatch for monitoring

### Scaling Considerations

- **Kafka**: Increase partitions for parallel processing
- **Spark**: Add more executors and increase cores
- **Storage**: Use distributed file systems (HDFS/S3)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📚 Learning Resources

This project includes comprehensive documentation for learners:

- **[LEARNING_GUIDE.md](LEARNING_GUIDE.md)** - Complete tutorial on how the pipeline works
- **[VERIFICATION_REPORT.md](VERIFICATION_REPORT.md)** - Performance benchmarks and testing results
- **Inline Code Comments** - Detailed explanations throughout the codebase
- **[scripts/live_monitor.sh](scripts/live_monitor.sh)** - Real-time monitoring tool

### What Makes This Portfolio-Worthy?

✅ **Production-Grade Code**: Error handling, logging, monitoring  
✅ **Comprehensive Documentation**: README, guides, and inline comments  
✅ **Real Performance Metrics**: Verified 65K+ events/hour throughput  
✅ **Best Practices**: Design patterns, testing, containerization  
✅ **Scalable Architecture**: Ready for production deployment  

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Apache Kafka and Spark communities for excellent open-source tools
- Confluent for Kafka Docker images and documentation
- Apache Software Foundation for Spark Docker images

---

## 📧 Contact

**Mohammad Ghafari** - [mmqaffari@gmail.com](mailto:mmqaffari@gmail.com)

Project Link: [https://github.com/Mohaghafari/real-time-streaming-pipeline](https://github.com/Mohaghafari/real-time-streaming-pipeline)

LinkedIn: [Mohammad Ghafari](https://www.linkedin.com/in/mohaghafari/)

---

## ⭐ Star History

If you found this project helpful, please consider giving it a star!

[![Star History Chart](https://api.star-history.com/svg?repos=Mohaghafari/real-time-streaming-pipeline&type=Date)](https://star-history.com/#Mohaghafari/real-time-streaming-pipeline&Date)

---

<div align="center">

**Made with ❤️ for Data Engineering**

[⬆ Back to Top](#-real-time-streaming-pipeline)

</div>
