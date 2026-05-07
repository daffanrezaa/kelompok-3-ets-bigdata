#!/bin/bash

set -e

echo "Starting Kafka & Hadoop..."
docker-compose -f docker-compose-kafka.yml -f docker-compose-hadoop.yml up -d --remove-orphans

sleep 60

echo "Starting Kafka services..."

nohup python3 kafka/producer_api.py > producer_api.log 2>&1 &
echo $! > producer_api.pid
echo "✔ producer_api started (PID $(cat producer_api.pid))"

nohup python3 kafka/producer_rss.py > producer_rss.log 2>&1 &
echo $! > producer_rss.pid
echo "✔ producer_rss started (PID $(cat producer_rss.pid))"

nohup python3 kafka/consumer_to_hdfs.py > consumer.log 2>&1 &
echo $! > consumer.pid
echo "✔ consumer started (PID $(cat consumer.pid))"

echo "Semua service running!"