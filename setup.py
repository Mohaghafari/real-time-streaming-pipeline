from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="real-time-streaming-pipeline",
    version="1.0.0",
    author="ghafarimstream-analytics",
    description="Real-time streaming pipeline with Kafka and Spark Structured Streaming",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ghafarimstream-analytics/real-time-streaming-pipeline",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "kafka-python>=2.0.2",
        "pyspark>=3.5.0",
        "prometheus-client>=0.18.0",
        "numpy>=1.24.3",
        "pandas>=2.0.3",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.7.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "streaming-producer=producer.event_generator:main",
            "streaming-consumer=consumer.streaming_consumer:main",
            "pipeline-monitor=monitoring.pipeline_monitor:main",
        ],
    },
)
