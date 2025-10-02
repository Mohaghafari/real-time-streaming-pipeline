# Real-Time Crypto Streaming with Kafka & Spark

Streaming live cryptocurrency prices and processing them in real-time. Built this to learn how financial platforms handle high-frequency market data.

## What This Does

Connects to Binance WebSocket API and streams live crypto trades (BTC, ETH, SOL, etc.) into Kafka, then processes them with Spark Structured Streaming to calculate things like price changes, volume, and trading patterns.

Currently streaming ~200-500 trades per second depending on market activity.

## Tech Used

- **Kafka** - Message queue for the trade stream
- **Spark Structured Streaming** - Real-time processing
- **Binance API** - Live crypto data (free, no auth needed)
- **Docker** - Everything runs in containers
- **Prometheus + Grafana** - Monitoring

## Quick Start

Need Docker installed.

```bash
git clone https://github.com/Mohaghafari/real-time-streaming-pipeline.git
cd real-time-streaming-pipeline

# Start everything
docker-compose up -d

# See live trades (wait ~30 sec for Kafka to start)
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic streaming-events \
  --max-messages 10
```

You'll see actual Bitcoin/Ethereum trades with real prices.

## Architecture

```
Binance WebSocket
    ↓
Python Producer → Kafka → Spark → Parquet Files
    ↓
Prometheus ← metrics
    ↓
Grafana (dashboards)
```

## What Gets Tracked

Each trade has:
- Symbol (BTCUSDT, ETHUSDT, etc.)
- Price
- Quantity
- Timestamp  
- Buyer/seller info

Spark calculates:
- Price changes in 1-min and 5-min windows
- Trading volume per symbol
- Buy vs sell pressure
- OHLC candles

## Web UIs

After starting:
- Kafka UI: http://localhost:8080 (see topics/messages)
- Spark UI: http://localhost:8081 (job monitoring)
- Grafana: http://localhost:3000 (dashboards, login: admin/admin)

## Project Structure

```
├── docker-compose.yml       # All services
├── src/
│   ├── producer/           # Binance → Kafka
│   └── consumer/           # Kafka → Spark processing
├── docker/                 # Dockerfiles
└── scripts/                # Helper scripts
```

## How It Works

**Producer** (`src/producer/event_generator.py`):
- Connects to Binance WebSocket
- Subscribes to 10 trading pairs
- Pushes each trade to Kafka topic `streaming-events`
- Uses symbol as partition key

**Consumer** (`src/consumer/streaming_consumer.py`):
- Reads from Kafka with Spark
- Windows data by time (1min, 5min)
- Calculates aggregations
- Saves to Parquet with checkpointing

## Why Crypto Data?

Initially had fake e-commerce events but switched to real financial data because:
1. Way more impressive for portfolio
2. Actually useful analytics (price changes, volume patterns)
3. Variable throughput (teaches you to handle spikes)
4. Free API access from Binance

## Things I Learned

- WebSocket connections in Python aren't trivial
- Kafka's `acks=all` vs `acks=1` performance tradeoff
- Spark watermarking for late-arriving data
- Why checkpointing is critical (found out the hard way)
- Docker networking between containers
- Processing variable-rate streams (crypto markets are wild at 3am)

## Monitoring

Prometheus scrapes metrics from producer and consumer:
- Trades per second
- Processing lag
- Kafka offset tracking
- Error rates

Grafana has dashboards showing real-time throughput and price charts.

## Common Issues

**Kafka won't start**
- Needs 8GB RAM for Docker
- Takes ~30 seconds to fully initialize
- Check logs: `docker logs kafka`

**No trades showing up**
- Make sure producer connected to Binance
- Check: `docker logs kafka-producer`
- Should see "WebSocket connection opened"

**Spark errors**
- Schema mismatch usually
- Old data in checkpoints: `rm -rf data/spark-checkpoints/*`

## Performance

Getting ~200-500 trades/sec in active hours. BTC and ETH generate most volume. Weekends are quieter.

Kafka handles it fine with default settings. Spark processes in ~30 second microbatches.

## Future Ideas

- Add more exchanges (Coinbase, Kraken) for arbitrage detection
- Calculate moving averages and RSI
- Price anomaly alerts
- Historical data replay for backtesting
- Implement exactly-once semantics

## Files You Should Look At

- `src/producer/event_generator.py` - WebSocket → Kafka
- `src/consumer/streaming_consumer.py` - Kafka → Spark aggregations
- `docker-compose.yml` - Full stack setup
- `NOTES.md` - Random dev notes I took while building

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

(Tests are basic right now, mainly for producer connection logic)

## License

MIT

## Contact

Mohammad Ghafari  
[mmqaffari@gmail.com](mailto:mmqaffari@gmail.com)  
[LinkedIn](https://www.linkedin.com/in/mohaghafari/) | [GitHub](https://github.com/Mohaghafari)

---

Built this over a few weeks while learning Kafka and Spark. If you have questions or suggestions, open an issue!
