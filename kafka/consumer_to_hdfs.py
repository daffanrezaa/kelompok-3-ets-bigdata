"""
Consumer: Kafka Topics → HDFS
Membaca dari 'github-api' dan 'github-rss' secara paralel,
buffer setiap 2 menit, simpan ke:
  1. HDFS (via WebHDFS)                 ← storage utama
  2. dashboard/data/live_*.json         ← live feed untuk Flask
  3. tmp/spark_staging/{api,rss}/       ← dibaca oleh spark/run_analysis.py
"""

import json
import time
import threading
import logging
import os
from datetime import datetime
from kafka import KafkaConsumer
from hdfs import InsecureClient

# === PATH SETUP ===
# Resolve semua path relatif terhadap project root (parent dari kafka/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BUFFER_DIR       = os.path.join(PROJECT_ROOT, 'tmp', 'github_buffer')
DASHBOARD_DATA_DIR = os.path.join(PROJECT_ROOT, 'dashboard', 'data')
# tmp/spark_staging/ dibaca oleh spark/run_analysis.py
STAGING_BASE_DIR = os.path.join(PROJECT_ROOT, 'tmp', 'spark_staging')

# === KONFIGURASI ===
KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']
HDFS_URL = 'http://127.0.0.1:9870'
HDFS_USER = 'root'
CONSUMER_GROUP = 'github-consumer-group'
TOPICS = {
    'github-api': {
        'hdfs_path':    '/data/github/api',
        'local_path':   os.path.join(DASHBOARD_DATA_DIR, 'live_api.json'),
        'staging_dir':  os.path.join(STAGING_BASE_DIR, 'api'),
    },
    'github-rss': {
        'hdfs_path':    '/data/github/rss',
        'local_path':   os.path.join(DASHBOARD_DATA_DIR, 'live_rss.json'),
        'staging_dir':  os.path.join(STAGING_BASE_DIR, 'rss'),
    }
}
BUFFER_INTERVAL  = 2 * 60  # Flush buffer setiap 2 menit
MAX_LOCAL_EVENTS = 50       # Simpan N event terbaru untuk dashboard

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# HDFS Client
hdfs_client = InsecureClient(HDFS_URL, user=HDFS_USER)

# Shared buffers (thread-safe dengan lock)
buffers = {topic: [] for topic in TOPICS}
buffers_lock = threading.Lock()

# Pastikan semua folder ada saat startup
os.makedirs(DASHBOARD_DATA_DIR, exist_ok=True)
os.makedirs(BUFFER_DIR, exist_ok=True)
for _topic_cfg in TOPICS.values():
    os.makedirs(_topic_cfg['staging_dir'], exist_ok=True)


def ensure_hdfs_dirs():
    """Buat direktori HDFS jika belum ada menggunakan WebHDFS."""
    for topic, config in TOPICS.items():
        hdfs_path = config['hdfs_path']
        try:
            hdfs_client.makedirs(hdfs_path)
            logger.info(f"HDFS directory ready: {hdfs_path}")
        except Exception as e:
            logger.error(f"Error creating HDFS dir {hdfs_path}: {e}")


def save_to_hdfs(data: list, hdfs_path: str, topic: str):
    """
    Simpan data ke HDFS menggunakan WebHDFS API.
    """
    if not data:
        return

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    hdfs_file = f'{hdfs_path}/{timestamp}.json'

    try:
        # Konversi data ke JSON string dan encode utf-8
        json_data = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        
        # Tulis langsung ke HDFS tanpa file lokal sementara
        with hdfs_client.write(hdfs_file, overwrite=True) as writer:
            writer.write(json_data)
            
        logger.info(f"Berhasil upload {len(data)} events ke HDFS: {hdfs_file}")
        
    except Exception as e:
        logger.error(f"Error upload HDFS: {e}")


def save_live_data(data: list, local_path: str):
    """
    Simpan N event terbaru ke file JSON lokal untuk dashboard (live_*.json).
    File ini di-overwrite setiap flush — berisi N event paling baru.
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

        logger.info(f"Updated {local_path} ({len(latest)} events)")

    except Exception as e:
        logger.error(f"Error saving local data: {e}")


def save_to_staging(data: list, staging_dir: str, topic: str):
    """
    Simpan batch data ke tmp/spark_staging/{api|rss}/ sebagai file bertimestamp.

    Tujuan: agar spark/run_analysis.py bisa membaca data ini tanpa perlu
    copy manual.  Setiap flush menghasilkan satu file baru (tidak di-overwrite)
    sehingga data terakumulasi persis seperti di HDFS.
    """
    if not data:
        return

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    staging_file = os.path.join(staging_dir, f'{timestamp}.json')

    try:
        with open(staging_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Staging ({topic}): {len(data)} events → {staging_file}")
    except Exception as e:
        logger.error(f"Error saving staging file ({topic}): {e}")


def flush_buffers():
    """
    Flush semua buffer secara periodik ke 3 tujuan:
      1. HDFS             (save_to_hdfs)
      2. dashboard/data/  (save_live_data)
      3. tmp/spark_staging/ (save_to_staging)  ← dibaca run_analysis.py
    """
    while True:
        time.sleep(BUFFER_INTERVAL)

        with buffers_lock:
            for topic, config in TOPICS.items():
                if buffers[topic]:
                    data_to_save = buffers[topic].copy()
                    buffers[topic] = []  # Reset buffer

                    save_to_hdfs(data_to_save, config['hdfs_path'], topic)
                    save_live_data(data_to_save, config['local_path'])
                    save_to_staging(data_to_save, config['staging_dir'], topic)

                    logger.info(f"Flushed {len(data_to_save)} events dari topic '{topic}'")


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

    logger.info(f"Consumer untuk topic '{topic}' dimulai")

    try:
        while True:
            # Poll pesan dengan timeout
            message_pack = consumer.poll(timeout_ms=1000)

            for tp, messages in message_pack.items():
                with buffers_lock:
                    for msg in messages:
                        buffers[topic].append(msg.value)

                if messages:
                    logger.info(f"Received {len(messages)} messages dari '{topic}' | Buffer size: {len(buffers[topic])}")

    except Exception as e:
        logger.error(f"Error consumer '{topic}': {e}")
    finally:
        consumer.close()


def main():
    """Jalankan consumer dan buffer flusher secara paralel."""
    logger.info("Consumer HDFS dimulai")
    logger.info(f"Topics: {list(TOPICS.keys())}")
    logger.info(f"Buffer flush interval: {BUFFER_INTERVAL//60} menit")

    # Buat direktori HDFS
    ensure_hdfs_dirs()

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

    logger.info(f"{len(threads)} thread berjalan")

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