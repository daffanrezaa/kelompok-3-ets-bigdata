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

# === PATH SETUP ===
# Resolve semua path relatif terhadap project root (parent dari kafka/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BUFFER_DIR = os.path.join(PROJECT_ROOT, 'tmp', 'github_buffer')
DASHBOARD_DATA_DIR = os.path.join(PROJECT_ROOT, 'dashboard', 'data')

# === KONFIGURASI ===
KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']
CONSUMER_GROUP = 'github-consumer-group'
TOPICS = {
    'github-api': {
        'hdfs_path': '/data/github/api',
        'local_path': os.path.join(DASHBOARD_DATA_DIR, 'live_api.json')
    },
    'github-rss': {
        'hdfs_path': '/data/github/rss',
        'local_path': os.path.join(DASHBOARD_DATA_DIR, 'live_rss.json')
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

# Pastikan folder ada
os.makedirs(DASHBOARD_DATA_DIR, exist_ok=True)
os.makedirs(BUFFER_DIR, exist_ok=True)


def ensure_hdfs_dirs():
    """Buat direktori HDFS jika belum ada."""
    for topic, config in TOPICS.items():
        hdfs_path = config['hdfs_path']
        try:
            result = subprocess.run(
                ['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-mkdir', '-p', hdfs_path],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                logger.info(f"HDFS directory ready: {hdfs_path}")
            else:
                logger.warning(f"HDFS mkdir warning: {result.stderr.strip()}")
        except Exception as e:
            logger.error(f"Error creating HDFS dir {hdfs_path}: {e}")


def save_to_hdfs(data: list, hdfs_path: str, topic: str):
    """
    Simpan data ke HDFS.
    Strategi: simpan ke file lokal → docker cp ke namenode → hdfs dfs -put → cleanup
    """
    if not data:
        return

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'{topic}_{timestamp}.json'
    local_file = os.path.join(BUFFER_DIR, filename)
    container_tmp = f'/tmp/{filename}'
    hdfs_file = f'{hdfs_path}/{timestamp}.json'

    # Step 1: Simpan ke file lokal sementara
    try:
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Gagal menulis file lokal: {e}")
        return

    # Step 2: Copy file dari host ke dalam container namenode
    try:
        cp_result = subprocess.run(
            ['docker', 'cp', local_file, f'namenode:{container_tmp}'],
            capture_output=True, text=True, timeout=30
        )
        if cp_result.returncode != 0:
            logger.error(f"Gagal docker cp: {cp_result.stderr.strip()}")
            return
    except subprocess.TimeoutExpired:
        logger.error("Timeout saat docker cp")
        return
    except Exception as e:
        logger.error(f"Error docker cp: {e}")
        return

    # Step 3: Upload dari container ke HDFS
    try:
        put_result = subprocess.run(
            ['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-put', '-f',
             container_tmp, hdfs_file],
            capture_output=True, text=True, timeout=30
        )

        if put_result.returncode == 0:
            logger.info(f"Berhasil upload {len(data)} events ke HDFS: {hdfs_file}")
        else:
            logger.error(f"Gagal upload ke HDFS: {put_result.stderr.strip()}")

    except subprocess.TimeoutExpired:
        logger.error("Timeout saat upload ke HDFS")
    except Exception as e:
        logger.error(f"Error upload HDFS: {e}")

    # Step 4: Cleanup file sementara (host + container)
    finally:
        if os.path.exists(local_file):
            os.remove(local_file)
        try:
            subprocess.run(
                ['docker', 'exec', 'namenode', 'rm', '-f', container_tmp],
                capture_output=True, text=True, timeout=10
            )
        except Exception:
            pass


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

        logger.info(f"Updated {local_path} ({len(latest)} events)")

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

                    # Simpan ke HDFS dan file lokal
                    save_to_hdfs(data_to_save, config['hdfs_path'], topic)
                    save_live_data(data_to_save, config['local_path'])

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