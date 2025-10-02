# Development Notes

Random notes I took while building this.

## Initial Setup Issues

Had trouble with the Spark Docker image. The bitnami/spark images weren't working properly, kept getting connection errors. Switched to apache/spark:3.5.0-python3 and that fixed it.

## Kafka Configuration

Took a while to get the bootstrap servers right. Inside Docker network it's `kafka:29092` but from host it's `localhost:9092`. This tripped me up for like 2 hours.

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

Started at about 10 events/sec. After some tuning:
- Enabled backpressure
- Adjusted shuffle partitions to 10
- Set maxOffsetsPerTrigger to 10000

Now consistently hitting 18 events/sec (~65K/hour).

## Docker Memory

Needs at least 8GB. Spark worker is configured for 2GB which seems to be enough for this workload.

## Things That Broke

1. Port conflicts - make sure 8080, 8081, 9092 aren't in use
2. Kafka takes ~30s to fully start, producer retries automatically
3. Docker on Mac has different networking than Linux

## To Do

- Add exactly-once semantics (harder than it sounds)
- Better error handling
- Schema registry would be nice
- Maybe add Flink for comparison?

