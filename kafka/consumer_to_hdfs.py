"""
Consumer: Kafka Topics → HDFS
Membaca dari 'github-api' dan 'github-rss' secara paralel,
buffer setiap 2 menit, simpan ke HDFS dan file lokal untuk dashboard
"""

import json
import time
import threading
import logging
import subprocess
import os
from datetime import datetime
from kafka import KafkaConsumer

# === KONFIGURASI ===
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
CONSUMER_GROUP = 'github-consumer-group'
TOPICS = {
    'github-api': {
        'hdfs_path': '/data/github/api',
        'local_path': 'dashboard/data/live_api.json'
    },
    'github-rss': {
        'hdfs_path': '/data/github/rss',
        'local_path': 'dashboard/data/live_rss.json'
    }
}
BUFFER_INTERVAL = 2 * 60  # Flush buffer setiap 2 menit
MAX_LOCAL_EVENTS = 50       # Simpan N event terbaru untuk dashboard

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Shared buffers (thread-safe dengan lock)
buffers = {topic: [] for topic in TOPICS}
buffers_lock = threading.Lock()

# Pastikan folder lokal ada
os.makedirs('dashboard/data', exist_ok=True)
os.makedirs('/tmp/github_buffer', exist_ok=True)


def save_to_hdfs(data: list, hdfs_path: str, topic: str):
    """
    Simpan data ke HDFS menggunakan subprocess (Opsi A - lebih mudah).
    File diberi nama timestamp untuk memudahkan tracking.
    """
    if not data:
        return
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    local_file = f'/tmp/github_buffer/{topic}_{timestamp}.json'
    hdfs_file = f'{hdfs_path}/{timestamp}.json'
    
    # Simpan ke file lokal sementara
    with open(local_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Upload ke HDFS
    try:
        result = subprocess.run(
            ['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-put', 
             f'/tmp/{topic}_{timestamp}.json', hdfs_file],
            capture_output=True, text=True, timeout=30
        )
        
        # Alternatif: jalankan langsung jika di dalam container
        # result = subprocess.run(
        #     ['hdfs', 'dfs', '-put', local_file, hdfs_file],
        #     capture_output=True, text=True, timeout=30
        # )
        
        if result.returncode == 0:
            logger.info(f"✅ Berhasil upload {len(data)} events ke HDFS: {hdfs_file}")
        else:
            logger.error(f"❌ Gagal upload ke HDFS: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout saat upload ke HDFS")
    except Exception as e:
        logger.error(f"Error upload HDFS: {e}")
    finally:
        # Hapus file lokal sementara
        if os.path.exists(local_file):
            os.remove(local_file)


def save_live_data(data: list, local_path: str):
    """
    Simpan N event terbaru ke file JSON lokal untuk dashboard.
    Dashboard membaca file ini untuk menampilkan data live.
    """
    try:
        # Baca data existing
        existing = []
        if os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        
        # Gabungkan dan ambil N terbaru
        combined = existing + data
        latest = combined[-MAX_LOCAL_EVENTS:]
        
        with open(local_path, 'w', encoding='utf-8') as f:
            json.dump(latest, f, ensure_ascii=False, indent=2)
            
        logger.info(f"📝 Updated {local_path} ({len(latest)} events)")
        
    except Exception as e:
        logger.error(f"Error saving local data: {e}")


def flush_buffers():
    """Flush semua buffer ke HDFS dan file lokal secara periodik."""
    while True:
        time.sleep(BUFFER_INTERVAL)
        
        with buffers_lock:
            for topic, config in TOPICS.items():
                if buffers[topic]:
                    data_to_save = buffers[topic].copy()
                    buffers[topic] = []  # Reset buffer
                    
                    # Simpan ke HDFS (async bisa dioptimasi dengan threading)
                    save_to_hdfs(data_to_save, config['hdfs_path'], topic)
                    save_live_data(data_to_save, config['local_path'])
                    
                    logger.info(f"🔄 Flushed {len(data_to_save)} events dari topic '{topic}'")


def consume_topic(topic: str):
    """Consumer untuk satu topic Kafka."""
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=1000  # Timeout agar bisa di-interrupt
    )
    
    logger.info(f"🎧 Consumer untuk topic '{topic}' dimulai")
    
    try:
        while True:
            # Poll pesan dengan timeout
            message_pack = consumer.poll(timeout_ms=1000)
            
            for tp, messages in message_pack.items():
                with buffers_lock:
                    for msg in messages:
                        buffers[topic].append(msg.value)
                        
                if messages:
                    logger.info(f"📥 Received {len(messages)} messages dari '{topic}' | Buffer size: {len(buffers[topic])}")
                        
    except Exception as e:
        logger.error(f"Error consumer '{topic}': {e}")
    finally:
        consumer.close()


def main():
    """Jalankan consumer dan buffer flusher secara paralel."""
    logger.info("🎬 Consumer HDFS dimulai")
    logger.info(f"Topics: {list(TOPICS.keys())}")
    logger.info(f"Buffer flush interval: {BUFFER_INTERVAL//60} menit")
    
    threads = []
    
    # Thread per topic consumer
    for topic in TOPICS:
        t = threading.Thread(target=consume_topic, args=(topic,), daemon=True)
        t.start()
        threads.append(t)
    
    # Thread untuk flush buffer ke HDFS
    flush_thread = threading.Thread(target=flush_buffers, daemon=True)
    flush_thread.start()
    threads.append(flush_thread)
    
    logger.info(f"✅ {len(threads)} thread berjalan")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(10)
            with buffers_lock:
                for topic in TOPICS:
                    logger.debug(f"Buffer '{topic}': {len(buffers[topic])} events pending")
    except KeyboardInterrupt:
        logger.info("Consumer dihentikan oleh user")


if __name__ == '__main__':
    main()