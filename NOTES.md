# Dev Notes

Random stuff I learned while building this.

## Day 1 - Why Crypto?

Started with fake e-commerce events but they felt pointless. Found out Binance has free WebSocket API for trades. Way cooler to use real data.

Their API is actually really clean:
```
wss://stream.binance.com:9443/stream?streams=btcusdt@trade
```
Just connect and data flows. No rate limits on public streams.

## Docker Networking Headache

Spent like 3 hours on this. Inside containers, Kafka is at `kafka:29092`. From my Mac, it's `localhost:9092`. 

The docker-compose networking stuff is confusing. Finally got it working by setting:
```yaml
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
```

## WebSocket Client in Python

Tried a few libraries:
- `websockets` - too low level
- `websocket-client` - perfect, simple callbacks

Just install with `pip install websocket-client` and use the `WebSocketApp` class. Easy.

## Spark Dockerfile Issues

bitnami/spark images didn't work. Container would just exit immediately. No error messages.

Switched to official `apache/spark:3.5.0-python3` and it worked first try. 🤷

## Checkpointing (learned the hard way)

First version had no checkpointing. Restarted Spark and lost all state. Oops.

Added this:
```python
.config("spark.sql.streaming.checkpointLocation", checkpoint_location)
```

Now it recovers from crashes. Checkpoints go in `data/spark-checkpoints/`.

## Watermarking

Without watermarking, late trades were silently dropped. With crypto, clocks can be slightly off.

Added 1-minute watermark:
```python
watermarked_df = df.withWatermark("event_time", "1 minute")
```

Lets Spark wait a bit for stragglers before finalizing windows.

## Data Volume

Varies wildly by time of day:
- Asian hours: 300-500 trades/sec
- US hours: 200-300 trades/sec  
- Weekends: 50-100 trades/sec
- Random 3am pumps: 1000+ trades/sec

BTC and ETH are always active. DOGE surprisingly gets a lot of trades too.

## Kafka Partitioning

Using symbol as the partition key:
```python
key = event['symbol']  # e.g., "BTCUSDT"
```

This way all BTC trades go to same partition, keeps ordering. With 10 symbols and default 3 partitions, distribution is pretty even.

## Spark Aggregations

Doing three types:
1. 1-min windows for recent price changes
2. 5-min windows for OHLC candlesticks
3. Buy/sell pressure (based on `buyer_is_maker` flag)

Initially tried 10-second windows but that's overkill and just clutters the output.

## Prometheus Metrics

Producer exports:
- `events_produced_total` - counter
- `event_production_latency_seconds` - histogram

Consumer would export processing metrics but haven't hooked that up yet. TODO.

## Memory

Docker needs at least 8GB. Spark worker is set to 2GB which seems fine for this workload.

If you get OOM errors, bump `SPARK_WORKER_MEMORY` in docker-compose.yml.

## Bugs I Hit

1. **KeyError: 'user_id'** - Was copying code from old version. Crypto trades don't have user_id, duh.

2. **Schema mismatch** - Spark consumer was still expecting e-commerce schema. Had to update all the struct fields.

3. **WebSocket disconnect** - Happens occasionally. Should add auto-reconnect logic. For now just restarts container.

4. **Kafka takes 30sec to start** - Producer connection fails initially, then retries. Normal behavior.

## What's Actually Useful

The buy/sell pressure metric is interesting. When `buyer_is_maker=true`, means market sell into a limit buy. Vice versa for `false`. 

Can see when people are aggressively buying vs selling. Might be useful for trading signals.

## Performance Notes

No real bottleneck yet. Kafka handles the throughput fine. Spark processes in 30-second microbatches.

Could probably handle 10x more volume without changes. Would need to tune partition count and Spark parallelism for 100x.

## TODO

- Calculate VWAP (volume-weighted average price)
- Add simple moving average (SMA) calculations
- Detect big price movements (>2% in 1 min)
- Add Coinbase feed for price comparison
- Better error handling on WebSocket disconnect
- Actually connect Grafana dashboards (just have the containers running)

## Random Observations

- Crypto markets never sleep. 4am activity is wild.
- Most trades are tiny (< 0.01 BTC)
- Occasional massive trades show up (50+ BTC)
- ETH has more small retail trades
- BTC has more institutional-looking patterns

## Useful Commands

```bash
# Watch live trades
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic streaming-events

# Check message count
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 --topic streaming-events --time -1

# Clear Kafka data
docker-compose down -v

# See Spark logs
docker logs spark-master

# Restart just producer
docker-compose restart kafka-producer
```

## If I Started Over

Would I change anything? Maybe:
- Use Flink instead of Spark (native streaming, not microbatch)
- Add Redis for real-time price cache
- Store aggregations in TimescaleDB instead of Parquet
- Add a simple FastAPI endpoint to query recent prices

But for learning Kafka + Spark, this worked great.

## Resources I Used

- Binance API docs (actually pretty good)
- Spark Structured Streaming guide
- Stack Overflow (obviously)
- Random Medium articles about Kafka tuning

No courses or tutorials, just figured it out by breaking things.
