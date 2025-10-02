# ⚡ Quick Start Guide

Get your Real-Time Streaming Pipeline running in under 5 minutes!

---

## 🚀 One-Command Start

```bash
# Clone, start, and verify
git clone https://github.com/Mohaghafari/real-time-streaming-pipeline.git
cd real-time-streaming-pipeline
chmod +x scripts/*.sh
docker-compose up -d
```

**Done!** Your pipeline is now running. 🎉

---

## 🌐 Access the Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Kafka UI** | http://localhost:8080 | View messages & topics |
| **Spark UI** | http://localhost:8081 | Monitor Spark jobs |
| **Grafana** | http://localhost:3000 | Dashboards & metrics |
| **Prometheus** | http://localhost:9090 | Raw metrics |

**Grafana Login**: `admin` / `admin`

---

## 👀 Watch Data Flow

### Option 1: Live Monitor (Recommended)
```bash
./scripts/live_monitor.sh
```
Shows real-time events with icons and stats!

### Option 2: Peek at Messages
```bash
# See 5 recent events
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic streaming-events \
  --max-messages 5
```

### Option 3: Use Kafka UI
Open http://localhost:8080 → Topics → streaming-events → Messages

---

## 📊 Check Performance

```bash
# Total events produced
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic streaming-events --time -1

# Expected: Growing by ~18 events/second (~65K/hour)
```

---

## 🧪 Submit Spark Job (Process Data)

```bash
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  /opt/spark-apps/consumer/streaming_consumer.py
```

Then view the job at http://localhost:8081

---

## 🛑 Stop Everything

```bash
docker-compose down
```

Or use the script:
```bash
./scripts/stop_pipeline.sh
```

---

## 🔍 Troubleshooting

### Services won't start?
```bash
# Check Docker is running
docker ps

# View logs
docker-compose logs -f
```

### Port conflicts?
```bash
# See what's using the ports
lsof -i :8080  # Kafka UI
lsof -i :8081  # Spark
lsof -i :9092  # Kafka
```

### Need a fresh start?
```bash
# Stop and remove everything
docker-compose down -v
rm -rf data/*
docker-compose up -d
```

---

## 📚 Learn More

- **Full README**: [README.md](README.md)
- **Learning Guide**: [LEARNING_GUIDE.md](LEARNING_GUIDE.md)
- **Performance Report**: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md)
- **Deploy to GitHub**: [GITHUB_DEPLOYMENT_GUIDE.md](GITHUB_DEPLOYMENT_GUIDE.md)

---

## 🎯 What's Happening?

```
Producer (Python) → Kafka (Queue) → Spark (Processor) → Analytics
     18/sec           ~9K msgs         Real-time          Results
```

1. **Producer** generates fake e-commerce events
2. **Kafka** stores them reliably
3. **Spark** processes them in real-time
4. **You** watch everything via web UIs!

---

## ⚡ Quick Commands Reference

```bash
# Start pipeline
docker-compose up -d

# Watch events
./scripts/live_monitor.sh

# Check status
docker-compose ps

# View logs
docker logs -f kafka-producer

# Stop pipeline
docker-compose down

# Run tests
pytest tests/ -v

# Prepare for GitHub
./scripts/prepare_for_github.sh
```

---

## 🎓 Portfolio Tips

This project demonstrates:
- ✅ Distributed systems (Kafka)
- ✅ Stream processing (Spark)
- ✅ Containerization (Docker)
- ✅ Monitoring (Prometheus/Grafana)
- ✅ Clean code & documentation
- ✅ Real performance metrics

Perfect for data engineering interviews! 🚀

---

**Need Help?** Check [LEARNING_GUIDE.md](LEARNING_GUIDE.md) for detailed explanations!


