"""
Producer 1: GitHub REST API → Kafka Topic 'github-api'
Polling setiap 30 menit untuk repositori trending terbaru
"""

import json
import time
import os
import logging
from datetime import datetime, timedelta
from kafka import KafkaProducer
import requests
from dotenv import load_dotenv

# Load environment variables dari .env
load_dotenv()

# === KONFIGURASI ===
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_TOPIC = 'github-api'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')  # Optional, tapi disarankan
POLLING_INTERVAL = 30 * 60  # 30 menit dalam detik
REPOS_PER_PAGE = 30

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def create_producer():
    """Membuat Kafka producer dengan konfigurasi idempotent."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        enable_idempotence=True,
        acks='all',
        retries=5,
        max_in_flight_requests_per_connection=1
    )


def fetch_trending_repos():
    """
    Fetch repositori trending dari GitHub API.
    Mengambil repo yang dibuat kemarin dengan sort berdasarkan stars.
    """
    # Tanggal kemarin untuk filter repo baru
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    url = "https://api.github.com/search/repositories"
    params = {
        'q': f'created:>{yesterday}',
        'sort': 'stars',
        'order': 'desc',
        'per_page': REPOS_PER_PAGE
    }
    
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Tambahkan token jika tersedia (menghindari rate limit)
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        # Handle rate limiting
        if response.status_code == 403:
            reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
            wait_time = max(reset_time - time.time(), 60)
            logger.warning(f"Rate limit tercapai. Menunggu {wait_time:.0f} detik...")
            time.sleep(wait_time)
            return []
        
        response.raise_for_status()
        data = response.json()
        
        remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
        logger.info(f"Berhasil fetch {len(data.get('items', []))} repo. Rate limit remaining: {remaining}")
        
        return data.get('items', [])
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching dari GitHub API: {e}")
        return []


def format_repo_event(repo: dict) -> dict:
    """
    Format data repo menjadi event JSON yang konsisten.
    Hanya ambil field yang relevan.
    """
    return {
        # Identifiers
        'full_name': repo.get('full_name', ''),
        'html_url': repo.get('html_url', ''),
        
        # Konten
        'description': repo.get('description', '') or '',
        'language': repo.get('language', '') or 'Unknown',
        'topics': repo.get('topics', []),
        
        # Metrics
        'stargazers_count': repo.get('stargazers_count', 0),
        'forks_count': repo.get('forks_count', 0),
        'watchers_count': repo.get('watchers_count', 0),
        'open_issues_count': repo.get('open_issues_count', 0),
        
        # Meta
        'owner': repo.get('owner', {}).get('login', ''),
        'created_at': repo.get('created_at', ''),
        'pushed_at': repo.get('pushed_at', ''),
        'size': repo.get('size', 0),
        'license': (repo.get('license') or {}).get('name', 'No License'),
        
        # Pipeline metadata
        'ingested_at': datetime.now().isoformat(),
        'source': 'github-api'
    }


def main():
    """Loop utama producer API."""
    logger.info("GitHub API Producer dimulai")
    logger.info(f"Topic: {KAFKA_TOPIC} | Interval: {POLLING_INTERVAL//60} menit")
    
    producer = create_producer()
    
    try:
        while True:
            logger.info(f"Fetching data dari GitHub API...")
            repos = fetch_trending_repos()
            
            if repos:
                sent_count = 0
                for repo in repos:
                    event = format_repo_event(repo)
                    key = event['full_name']  # Key berdasarkan nama repo
                    
                    # Kirim ke Kafka
                    future = producer.send(
                        KAFKA_TOPIC,
                        key=key,
                        value=event
                    )
                    
                    # Tunggu konfirmasi (opsional, bisa dihapus untuk performa)
                    try:
                        record_metadata = future.get(timeout=10)
                        sent_count += 1
                    except Exception as e:
                        logger.error(f"Gagal kirim {key}: {e}")
                
                producer.flush()
                logger.info(f"Berhasil kirim {sent_count}/{len(repos)} event ke topic '{KAFKA_TOPIC}'")
            else:
                logger.warning("Tidak ada data yang di-fetch, coba lagi di interval berikutnya")
            
            logger.info(f"Menunggu {POLLING_INTERVAL//60} menit sebelum polling berikutnya...")
            time.sleep(POLLING_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Producer dihentikan oleh user")
    finally:
        producer.close()
        logger.info("Producer ditutup")


if __name__ == '__main__':
    main()