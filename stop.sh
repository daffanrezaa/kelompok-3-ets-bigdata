#!/bin/bash

echo "Stopping Python services..."

for f in producer_api.pid producer_rss.pid consumer.pid; do
  if [ -f "$f" ]; then
    PID=$(cat $f)
    if ps -p $PID > /dev/null 2>&1; then
      kill $PID
      echo "Killed $f (PID $PID)"
    else
      echo "PID $PID tidak aktif"
    fi
    rm -f $f
  else
    echo "File $f tidak ditemukan"
  fi
done

echo "Stopping Kafka & Hadoop..."
docker-compose -f docker-compose-kafka.yml -f docker-compose-hadoop.yml down --remove-orphans

echo "Semua dimatikan!"