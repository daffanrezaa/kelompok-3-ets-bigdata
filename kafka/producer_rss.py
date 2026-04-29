"""
Producer 2: TechCrunch RSS Feed → Kafka Topic 'github-rss'
Polling setiap 5 menit, menghindari duplikat artikel
"""

import json
import time
import hashlib
import logging
from datetime import datetime
from kafka import KafkaProducer
import feedparser

# === KONFIGURASI ===
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_TOPIC = 'github-rss'
RSS_URLS = [
    'https://techcrunch.com/feed/',
    'https://tekno.kompas.com/rss/'  # Backup
]
POLLING_INTERVAL = 5 * 60  # 5 menit dalam detik

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Set untuk tracking artikel yang sudah dikirim (in-memory)
# Untuk produksi: gunakan Redis atau file persisten
sent_ids = set()


def create_producer():
    """Membuat Kafka producer."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        enable_idempotence=True,
        acks='all',
        retries=5
    )


def get_entry_id(entry) -> str:
    """
    Buat ID unik untuk setiap entry RSS.
    Gunakan hash dari URL agar konsisten meskipun ID tidak ada.
    """
    raw = getattr(entry, 'link', '') or getattr(entry, 'id', '') or entry.title
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


def parse_rss_feed(url: str) -> list:
    """Parse RSS feed dan return list entry baru (belum dikirim)."""
    try:
        feed = feedparser.parse(url)
        
        if feed.bozo:
            logger.warning(f"RSS parse warning untuk {url}: {feed.bozo_exception}")
        
        new_entries = []
        for entry in feed.entries:
            entry_id = get_entry_id(entry)
            
            if entry_id not in sent_ids:
                new_entries.append((entry_id, entry))
        
        logger.info(f"Feed {url}: {len(feed.entries)} total, {len(new_entries)} baru")
        return new_entries
        
    except Exception as e:
        logger.error(f"Error parsing RSS {url}: {e}")
        return []


def format_rss_event(entry, source_url: str) -> dict:
    """Format entry RSS menjadi event JSON konsisten."""
    # Ambil summary dengan aman
    summary = ''
    if hasattr(entry, 'summary'):
        summary = entry.summary
    elif hasattr(entry, 'description'):
        summary = entry.description
    
    # Bersihkan HTML tags sederhana dari summary
    import re
    clean_summary = re.sub(r'<[^>]+>', '', summary)[:500]  # Max 500 karakter
    
    return {
        'title': getattr(entry, 'title', ''),
        'link': getattr(entry, 'link', ''),
        'summary': clean_summary,
        'published': getattr(entry, 'published', ''),
        'author': getattr(entry, 'author', '') if hasattr(entry, 'author') else '',
        'tags': [tag.term for tag in getattr(entry, 'tags', [])] if hasattr(entry, 'tags') else [],
        'source_url': source_url,
        'ingested_at': datetime.now().isoformat(),
        'source': 'rss-feed'
    }


def main():
    """Loop utama producer RSS."""
    logger.info("RSS Feed Producer dimulai")
    logger.info(f"Topic: {KAFKA_TOPIC} | Interval: {POLLING_INTERVAL//60} menit")
    
    producer = create_producer()
    
    try:
        while True:
            logger.info("Polling RSS feeds...")
            total_sent = 0
            
            for rss_url in RSS_URLS:
                new_entries = parse_rss_feed(rss_url)
                
                for entry_id, entry in new_entries:
                    event = format_rss_event(entry, rss_url)
                    
                    # Key: hash URL artikel
                    future = producer.send(
                        KAFKA_TOPIC,
                        key=entry_id,
                        value=event
                    )
                    
                    try:
                        future.get(timeout=10)
                        sent_ids.add(entry_id)  # Tandai sebagai sudah dikirim
                        total_sent += 1
                    except Exception as e:
                        logger.error(f"Gagal kirim entry {entry_id}: {e}")
            
            producer.flush()
            logger.info(f"Total {total_sent} artikel baru dikirim ke '{KAFKA_TOPIC}'")
            logger.info(f"Total artikel di-track: {len(sent_ids)}")
            
            logger.info(f"Menunggu {POLLING_INTERVAL//60} menit...")
            time.sleep(POLLING_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("RSS Producer dihentikan")
    finally:
        producer.close()


if __name__ == '__main__':
    main()