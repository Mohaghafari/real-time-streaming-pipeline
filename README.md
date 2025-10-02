# Real-Time Crypto Price Streaming Pipeline

A real-time data pipeline that streams live cryptocurrency prices from Binance and processes them using Kafka and Spark Structured Streaming. Built to understand how financial platforms handle real-time market data at scale.

## What It Does

Streams live trade data for 10 major cryptocurrencies (BTC, ETH, SOL, etc.) from Binance WebSocket API, processes them in real-time with Spark, and tracks metrics with Prometheus/Grafana. Handles hundreds of price updates per second with proper fault tolerance.

**Tech Stack**: Kafka, Spark, Docker, Binance API, Prometheus, Grafana, Python

**Live Data**: Real cryptocurrency trades from Binance (BTC, ETH, BNB, ADA, SOL, XRP, DOT, DOGE, MATIC, LINK)

## Why I Built This

Wanted to work with real financial data and understand:
- How trading platforms handle real-time market data
- Kafka message streaming with actual live data (not synthetic)
- Spark Structured Streaming for financial analytics
- Building fault-tolerant systems with checkpointing
- Processing high-frequency data streams
- Docker orchestration for production systems

## Architecture

```
┌─────────────────┐
│  Binance API    │  (WebSocket)
│  Real-time      │
│  Trade Stream   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Price Stream   │────▶│    Kafka    │────▶│ Spark Structured │
│  Producer       │     │   Broker    │     │   Streaming      │
└─────────────────┘     └─────────────┘     └──────────────────┘
                               │                      │
                               ▼                      ▼
                        ┌─────────────┐        ┌─────────────┐
                        │ Prometheus  │◀───────│  Metrics    │
                        └─────────────┘        └─────────────┘
                               │
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

3. Watch live crypto trades:
```bash
# See real trades from Binance
./scripts/watch_crypto_stream.sh

# Or manually:
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

## Data Schema

Real-time crypto trade events from Binance:

```json
{
  "event_id": "uuid",
  "event_type": "trade",
  "symbol": "BTCUSDT",
  "price": 43250.50,
  "quantity": 0.025,
  "trade_time": 1696234567890,
  "timestamp": "2024-10-02T12:34:56Z",
  "buyer_is_maker": false,
  "trade_id": 12345678
}
```

**Tracked pairs**: BTC, ETH, BNB, ADA, SOL, XRP, DOT, DOGE, MATIC, LINK (all vs USDT)

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

Processing real-time trade data - volume varies with market activity (typically 100-500 trades/sec during active hours). Main metrics:
- Price updates per second by symbol
- Trade volume aggregations
- Price changes in time windows
- Processing latency

All visible in Grafana dashboards.

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

- Working with real financial data APIs (Binance WebSocket)
- Kafka's guarantee mechanisms with high-frequency data
- Spark Structured Streaming for financial time-series
- Why checkpointing is critical for stateful streaming
- Watermarking for handling out-of-order trades
- Docker networking between Kafka and WebSocket connections
- Processing variable-rate data streams (crypto markets are unpredictable!)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Future Improvements

Ideas for v2:
- Add more exchanges (Coinbase, Kraken) for price comparison
- Implement trading signals (moving averages, RSI)
- Exactly-once semantics (currently at-least-once)
- Price anomaly detection
- Historical data replay for backtesting
- Kubernetes deployment
- Add orderbook data (not just trades)

## License

MIT

## Contact

Mohammad Ghafari - [mmqaffari@gmail.com](mailto:mmqaffari@gmail.com)

[LinkedIn](https://www.linkedin.com/in/mohaghafari/) | [GitHub](https://github.com/Mohaghafari)
