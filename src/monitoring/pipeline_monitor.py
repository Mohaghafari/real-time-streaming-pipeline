#!/usr/bin/env python3
"""
Pipeline Monitor - Real-time monitoring for the streaming pipeline
"""

import time
import requests
import json
from datetime import datetime
from typing import Dict, Any
import logging
from kafka import KafkaAdminClient
from kafka.admin import ConfigResource, ConfigResourceType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineMonitor:
    """Monitor the health and performance of the streaming pipeline"""
    
    def __init__(self,
                 kafka_bootstrap_servers: str = 'localhost:9092',
                 spark_ui_url: str = 'http://localhost:8081',
                 prometheus_url: str = 'http://localhost:9090',
                 kafka_ui_url: str = 'http://localhost:8080'):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.spark_ui_url = spark_ui_url
        self.prometheus_url = prometheus_url
        self.kafka_ui_url = kafka_ui_url
        self.admin_client = None
        
    def connect_kafka(self):
        """Connect to Kafka admin client"""
        try:
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.kafka_bootstrap_servers,
                client_id='pipeline-monitor'
            )
            logger.info("Connected to Kafka admin client")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            
    def get_kafka_metrics(self) -> Dict[str, Any]:
        """Get Kafka cluster metrics"""
        metrics = {}
        
        try:
            # Get cluster metadata
            metadata = self.admin_client._client.cluster
            metrics['brokers'] = len(metadata.brokers())
            metrics['topics'] = len(metadata.topics())
            
            # Get topic details
            topic_details = {}
            for topic in metadata.topics():
                partitions = metadata.partitions_for_topic(topic)
                if partitions:
                    topic_details[topic] = {
                        'partitions': len(partitions),
                        'replicas': len(metadata.replicas_for_partition(topic, 0)) if 0 in partitions else 0
                    }
            metrics['topic_details'] = topic_details
            
        except Exception as e:
            logger.error(f"Error getting Kafka metrics: {e}")
            
        return metrics
    
    def get_spark_metrics(self) -> Dict[str, Any]:
        """Get Spark application metrics"""
        metrics = {}
        
        try:
            # Get running applications
            response = requests.get(f"{self.spark_ui_url}/api/v1/applications")
            if response.status_code == 200:
                apps = response.json()
                metrics['running_apps'] = len([app for app in apps if app['state'] == 'RUNNING'])
                
                # Get details for each running app
                for app in apps:
                    if app['state'] == 'RUNNING':
                        app_id = app['id']
                        # Get streaming statistics
                        streaming_response = requests.get(
                            f"{self.spark_ui_url}/api/v1/applications/{app_id}/streaming/batches"
                        )
                        if streaming_response.status_code == 200:
                            batches = streaming_response.json()
                            if batches:
                                latest_batch = batches[0]
                                metrics['latest_batch'] = {
                                    'input_size': latest_batch.get('inputSize', 0),
                                    'processing_time': latest_batch.get('processingTime', 0),
                                    'status': latest_batch.get('status', 'unknown')
                                }
                                
        except Exception as e:
            logger.error(f"Error getting Spark metrics: {e}")
            
        return metrics
    
    def query_prometheus(self, query: str) -> Any:
        """Query Prometheus for metrics"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query}
            )
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    return data['data']['result']
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
        return None
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get overall pipeline metrics from Prometheus"""
        metrics = {}
        
        # Events produced rate
        result = self.query_prometheus('rate(events_produced_total[1m])')
        if result and len(result) > 0:
            metrics['events_per_second'] = float(result[0]['value'][1])
        
        # Events processed rate
        result = self.query_prometheus('rate(events_processed_total[1m])')
        if result and len(result) > 0:
            metrics['processed_per_second'] = float(result[0]['value'][1])
        
        # Processing delay
        result = self.query_prometheus('stream_processing_delay_seconds')
        if result and len(result) > 0:
            metrics['processing_delay_ms'] = float(result[0]['value'][1]) * 1000
        
        # Failed events
        result = self.query_prometheus('events_failed_total')
        if result and len(result) > 0:
            metrics['failed_events'] = int(result[0]['value'][1])
        
        return metrics
    
    def check_health(self) -> Dict[str, Any]:
        """Check overall pipeline health"""
        health = {
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'healthy',
            'components': {}
        }
        
        # Check Kafka
        try:
            kafka_metrics = self.get_kafka_metrics()
            health['components']['kafka'] = {
                'status': 'healthy' if kafka_metrics.get('brokers', 0) > 0 else 'unhealthy',
                'metrics': kafka_metrics
            }
        except:
            health['components']['kafka'] = {'status': 'unhealthy'}
            health['status'] = 'degraded'
        
        # Check Spark
        try:
            spark_metrics = self.get_spark_metrics()
            health['components']['spark'] = {
                'status': 'healthy' if spark_metrics.get('running_apps', 0) > 0 else 'unhealthy',
                'metrics': spark_metrics
            }
        except:
            health['components']['spark'] = {'status': 'unhealthy'}
            health['status'] = 'degraded'
        
        # Check Pipeline metrics
        try:
            pipeline_metrics = self.get_pipeline_metrics()
            
            # Calculate health based on metrics
            events_rate = pipeline_metrics.get('events_per_second', 0)
            processed_rate = pipeline_metrics.get('processed_per_second', 0)
            delay_ms = pipeline_metrics.get('processing_delay_ms', 0)
            
            pipeline_health = 'healthy'
            if events_rate == 0 or processed_rate == 0:
                pipeline_health = 'unhealthy'
            elif delay_ms > 5000:  # More than 5 seconds delay
                pipeline_health = 'degraded'
            elif processed_rate < events_rate * 0.9:  # Processing less than 90% of events
                pipeline_health = 'degraded'
            
            health['components']['pipeline'] = {
                'status': pipeline_health,
                'metrics': pipeline_metrics
            }
            
            if pipeline_health == 'unhealthy':
                health['status'] = 'unhealthy'
            elif pipeline_health == 'degraded' and health['status'] != 'unhealthy':
                health['status'] = 'degraded'
                
        except:
            health['components']['pipeline'] = {'status': 'unknown'}
            
        return health
    
    def print_dashboard(self, health: Dict[str, Any]):
        """Print a simple text dashboard"""
        print("\n" + "="*60)
        print(f"STREAMING PIPELINE MONITOR - {health['timestamp']}")
        print("="*60)
        print(f"Overall Status: {health['status'].upper()}")
        print("-"*60)
        
        # Kafka status
        kafka_status = health['components'].get('kafka', {})
        print(f"Kafka: {kafka_status.get('status', 'unknown').upper()}")
        if 'metrics' in kafka_status:
            metrics = kafka_status['metrics']
            print(f"  Brokers: {metrics.get('brokers', 'N/A')}")
            print(f"  Topics: {metrics.get('topics', 'N/A')}")
        
        print("-"*60)
        
        # Spark status
        spark_status = health['components'].get('spark', {})
        print(f"Spark: {spark_status.get('status', 'unknown').upper()}")
        if 'metrics' in spark_status:
            metrics = spark_status['metrics']
            print(f"  Running Apps: {metrics.get('running_apps', 'N/A')}")
            if 'latest_batch' in metrics:
                batch = metrics['latest_batch']
                print(f"  Latest Batch:")
                print(f"    Input Size: {batch.get('input_size', 'N/A')}")
                print(f"    Processing Time: {batch.get('processing_time', 'N/A')}ms")
        
        print("-"*60)
        
        # Pipeline metrics
        pipeline_status = health['components'].get('pipeline', {})
        print(f"Pipeline: {pipeline_status.get('status', 'unknown').upper()}")
        if 'metrics' in pipeline_status:
            metrics = pipeline_status['metrics']
            print(f"  Events/sec (produced): {metrics.get('events_per_second', 0):.2f}")
            print(f"  Events/sec (processed): {metrics.get('processed_per_second', 0):.2f}")
            print(f"  Processing Delay: {metrics.get('processing_delay_ms', 0):.2f}ms")
            print(f"  Failed Events: {metrics.get('failed_events', 0)}")
        
        print("="*60)
    
    def run(self, interval: int = 10):
        """Run the monitor continuously"""
        logger.info("Starting pipeline monitor...")
        self.connect_kafka()
        
        try:
            while True:
                health = self.check_health()
                self.print_dashboard(health)
                
                # Log to file for historical tracking
                with open('pipeline_health.jsonl', 'a') as f:
                    f.write(json.dumps(health) + '\n')
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping pipeline monitor...")
        except Exception as e:
            logger.error(f"Monitor error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor streaming pipeline')
    parser.add_argument('--interval', type=int, default=10,
                        help='Monitoring interval in seconds')
    parser.add_argument('--kafka-servers', default='localhost:9092',
                        help='Kafka bootstrap servers')
    parser.add_argument('--spark-ui', default='http://localhost:8081',
                        help='Spark UI URL')
    parser.add_argument('--prometheus', default='http://localhost:9090',
                        help='Prometheus URL')
    
    args = parser.parse_args()
    
    monitor = PipelineMonitor(
        kafka_bootstrap_servers=args.kafka_servers,
        spark_ui_url=args.spark_ui,
        prometheus_url=args.prometheus
    )
    
    monitor.run(interval=args.interval)


if __name__ == '__main__':
    main()
