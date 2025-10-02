# Use official Spark image with Python support
FROM apache/spark:3.5.0-python3

USER root

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install \
    pyspark==3.5.0 \
    kafka-python==2.0.2 \
    prometheus-client==0.18.0 \
    py4j==0.10.9.7 \
    numpy==1.24.3 \
    pandas==2.0.3 \
    pyarrow==13.0.0

# Create necessary directories
RUN mkdir -p /opt/spark-apps /opt/spark-checkpoints /opt/spark-warehouse /opt/config && \
    chmod -R 777 /opt/spark-checkpoints /opt/spark-warehouse

WORKDIR /opt/spark-apps

USER spark