# Development Notes

Random notes from building this.

## Why Crypto Data?

Initially was generating fake e-commerce events. Decided real data would be way more impressive for portfolio. Binance has a free WebSocket API - perfect!

## Binance WebSocket

Their API is actually really good. No auth needed for public trade streams. Just connect and data flows. Getting 100-500 trades/sec depending on market activity.

Format is simple:
```
wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade...
```

## Initial Setup Issues

Spark Docker image issues. bitnami/spark wasn't working. Switched to apache/spark:3.5.0-python3.

## Kafka Configuration

Docker networking was confusing. Inside network: `kafka:29092`. From host: `localhost:9092`. Took 2 hours to figure out.

## Checkpointing

First version didn't have checkpointing and lost all state when Spark restarted. Added:
```python
.config("spark.sql.streaming.checkpointLocation", checkpoint_location)
```

Makes a huge difference for fault tolerance.

## Watermarking

Without watermarking, late events were getting dropped silently. Added 5-minute watermark:
```python
watermarked_df = df.withWatermark("event_time", "5 minutes")
```

This lets the system wait for late data before finalizing aggregations.

## Performance

With real crypto data, volume is unpredictable. During Asian trading hours can get 500+ trades/sec. Weekends are quieter ~50-100/sec.

Tuning helped:
- Enabled backpressure (critical for variable rates)
- Shuffle partitions = 10
- maxOffsetsPerTrigger = 10000

BTC and ETH generate the most volume. DOGE is surprisingly active too.

## Docker Memory

Needs at least 8GB. Spark worker is configured for 2GB which seems to be enough for this workload.

## Things That Broke

1. Port conflicts - make sure 8080, 8081, 9092 aren't in use
2. Kafka takes ~30s to fully start, producer retries automatically
3. Docker on Mac has different networking than Linux

## To Do

- Calculate VWAP (Volume Weighted Average Price) in Spark
- Add price alerts when big moves happen
- Compare prices across exchanges (add Coinbase feed)
- Better error handling for WebSocket disconnects
- Maybe add order book data (more complex than trades)

