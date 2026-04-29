# 🚀 GitTrend: Panduan Lengkap ETS Big Data
## Topik 7 — Monitor Repositori Open Source Populer
### Big Data Pipeline: Kafka → HDFS → Spark → Flask Dashboard

---

## 📚 Daftar Isi

1. [Gambaran Besar Sistem](#gambaran-besar-sistem)
2. [Tech Stack Lengkap](#tech-stack-lengkap)
3. [Pembagian Tugas 5 Anggota](#pembagian-tugas-5-anggota)
4. [Persiapan Lingkungan Kerja](#persiapan-lingkungan-kerja)
5. [Komponen 1: Apache Kafka (Ingestion Layer)](#komponen-1-apache-kafka)
6. [Komponen 2: HDFS (Storage Layer)](#komponen-2-hdfs-storage-layer)
7. [Komponen 3: Apache Spark (Processing Layer)](#komponen-3-apache-spark)
8. [Komponen 4: Dashboard Flask (Serving Layer)](#komponen-4-dashboard-flask)
9. [README.md Template](#readmemd-template)
10. [Tips Debugging & Troubleshooting](#tips-debugging--troubleshooting)
11. [Checklist Final Submission](#checklist-final-submission)

---

## Gambaran Besar Sistem

Sistem yang kalian bangun adalah **Big Data Pipeline end-to-end** untuk memonitor repositori GitHub trending. Berikut cara kerja sistem dari ujung ke ujung:

```
GitHub API (polling 30 menit)
         │
         ▼
  producer_api.py  ──────────►  Kafka Topic: github-api
                                       │
TechCrunch RSS (polling 5 menit)       │
         │                             │
         ▼                             │
  producer_rss.py  ──────────►  Kafka Topic: github-rss
                                       │
                                       ▼
                            consumer_to_hdfs.py
                                       │
                           ┌───────────┴───────────┐
                           ▼                       ▼
                    HDFS /data/github/api/   HDFS /data/github/rss/
                           │                       │
                           └───────────┬───────────┘
                                       ▼
                               analysis.ipynb (Spark)
                                       │
                           ┌───────────┴───────────┐
                           ▼                       ▼
                  HDFS /data/github/hasil/   spark_results.json
                                                   │
                                                   ▼
                                          Flask Dashboard :5000
```

**Mengapa arsitektur ini penting?**

| Lapisan | Masalah yang Diselesaikan |
|---------|--------------------------|
| **Kafka** | GitHub API bisa lambat atau down — Kafka menyangga data agar tidak hilang |
| **HDFS** | Data tersimpan terdistribusi, fault-tolerant, tidak hilang meski 1 node mati |
| **Spark** | Memproses ribuan file JSON sekaligus dalam hitungan detik (bukan menit) |
| **Flask** | Non-engineer bisa melihat insight tanpa harus baca terminal |

---

## Tech Stack Lengkap

### 🛠️ Tools Utama (Wajib Terinstall)

| Tool | Versi Rekomendasi | Fungsi | Platform |
|------|-------------------|--------|----------|
| **Docker Desktop** | Latest | Menjalankan Kafka & Hadoop tanpa install manual | Windows/Mac/Linux |
| **Python** | 3.9+ | Menulis producer, consumer, Flask | Lokal |
| **VS Code** | Latest | Editor kode utama | Lokal |
| **Git** | Latest | Version control & submit ke GitHub | Lokal |
| **Postman** | Latest | Testing GitHub API sebelum koding | Lokal |

### 📦 Python Libraries

```bash
# Kafka
pip install kafka-python

# RSS Parsing
pip install feedparser

# HDFS Python Client (untuk bonus +2 poin)
pip install hdfs

# Flask Dashboard
pip install flask flask-cors

# Spark (jika pakai Jupyter lokal)
pip install pyspark

# Utilitas
pip install requests python-dotenv
```

### ☁️ Platform Cloud/Online

| Platform | Kapan Digunakan | Link |
|----------|-----------------|------|
| **Google Colab** | Menjalankan Spark analysis.ipynb (gratis GPU/RAM besar) | colab.research.google.com |
| **GitHub** | Submit repository final | github.com |
| **draw.io** | Membuat diagram arsitektur untuk README | app.diagrams.net |

### 🐳 Docker Images yang Digunakan

| Image | Container | Port |
|-------|-----------|------|
| `confluentinc/cp-zookeeper` | zookeeper | 2181 |
| `confluentinc/cp-kafka` | kafka-broker | 9092 |
| `bde2020/hadoop-namenode` | namenode | 9870 (Web UI) |
| `bde2020/hadoop-datanode` | datanode | — |
| `bde2020/hadoop-resourcemanager` | resourcemanager | 8088 |

---

## Pembagian Tugas 5 Anggota

### 🗂️ Struktur Tim yang Direkomendasikan

```
Ketua Tim (koordinasi + README + integrasi akhir)
    │
    ├── Anggota A → Kafka Producer (API + RSS)
    ├── Anggota B → Kafka Consumer + HDFS
    ├── Anggota C → Spark Analysis (Notebook)
    └── Anggota D → Flask Dashboard
```

---

### 👤 Anggota 1 — Ketua Tim: Project Lead & Integrator

**Tanggung Jawab:**
- Setup repository GitHub (buat repo, invite anggota, setup `.gitignore`)
- Setup `docker-compose-kafka.yml` dan `docker-compose-hadoop.yml`
- Membuat `hadoop.env`
- Integrasi akhir: pastikan semua komponen tersambung
- Menulis `README.md` lengkap (screenshot, dokumentasi)
- Testing end-to-end pipeline

**File yang dikerjakan:**
```
docker-compose-kafka.yml
docker-compose-hadoop.yml
hadoop.env
README.md
.gitignore
```

**Timeline yang disarankan:**
- Hari 1–2: Setup repo + Docker Compose (Kafka dan Hadoop berjalan)
- Hari 3–4: Koordinasi anggota lain, bantu debugging
- Hari 5–6: Integrasi + screenshot untuk README
- Hari 7: Final review + submit

**Cara verifikasi tugasnya berhasil:**
```bash
# Kafka berjalan
docker ps | grep kafka

# Hadoop berjalan
docker ps | grep namenode

# Akses HDFS Web UI
open http://localhost:9870
```

---

### 👤 Anggota 2 — Kafka Producer (GitHub API)

**Tanggung Jawab:**
- Menulis `kafka/producer_api.py`
- Koneksi ke GitHub REST API dengan Personal Access Token
- Polling setiap 30 menit
- Format JSON konsisten dan dikirim ke topic `github-api`

**File yang dikerjakan:**
```
kafka/producer_api.py
```

**Skill yang dibutuhkan:**
- Python dasar (requests, json, time)
- Pemahaman HTTP API (GET request, headers, response parsing)
- Sedikit pemahaman Kafka producer

**Timeline:**
- Hari 1: Pelajari GitHub API, dapatkan Personal Access Token (PAT)
- Hari 2: Tulis dan test `producer_api.py` secara standalone (tanpa Kafka dulu)
- Hari 3: Integrasikan dengan Kafka, test kirim event
- Hari 4: Verifikasi event masuk ke topic dengan `kafka-console-consumer`

---

### 👤 Anggota 3 — Kafka Producer (RSS) + Consumer HDFS

**Tanggung Jawab:**
- Menulis `kafka/producer_rss.py`
- Menulis `kafka/consumer_to_hdfs.py`
- RSS feed TechCrunch → Kafka → HDFS
- Consumer membaca kedua topic dan simpan ke HDFS + file lokal dashboard

**File yang dikerjakan:**
```
kafka/producer_rss.py
kafka/consumer_to_hdfs.py
```

**Timeline:**
- Hari 1–2: Tulis `producer_rss.py`, test dengan feedparser
- Hari 3: Tulis `consumer_to_hdfs.py` dengan strategi penyimpanan ke HDFS
- Hari 4: Test consumer berjalan paralel membaca 2 topic
- Hari 5: Verifikasi file tersimpan di HDFS

---

### 👤 Anggota 4 — Spark Analysis

**Tanggung Jawab:**
- Menulis `spark/analysis.ipynb`
- Membaca data dari HDFS
- Menjalankan 3 analisis wajib + narasi interpretasi
- Menyimpan hasil ke HDFS dan `dashboard/data/spark_results.json`

**File yang dikerjakan:**
```
spark/analysis.ipynb
```

**Platform:**
- **Opsi A (Lebih mudah):** Google Colab — tersedia PySpark gratis
- **Opsi B (Lebih realistis):** Jupyter Notebook lokal dengan PySpark

**Timeline:**
- Hari 1–2: Pelajari PySpark DataFrame API dan Spark SQL
- Hari 3: Tulis analisis 1 (distribusi bahasa)
- Hari 4: Tulis analisis 2 (top 10 repo) dan analisis 3 (kata trending)
- Hari 5: Tambahkan narasi, simpan hasil ke JSON

---

### 👤 Anggota 5 — Flask Dashboard

**Tanggung Jawab:**
- Menulis `dashboard/app.py`
- Menulis `dashboard/templates/index.html`
- 3 panel: Spark results + Live API + Live RSS
- Auto-refresh setiap 30–60 detik
- Bonus: Chart.js untuk visualisasi (+3 poin)

**File yang dikerjakan:**
```
dashboard/app.py
dashboard/templates/index.html
dashboard/static/style.css (opsional)
```

**Timeline:**
- Hari 1: Setup Flask minimal, bisa akses localhost:5000
- Hari 2: Endpoint `/api/data` yang return JSON dari 3 file
- Hari 3: HTML dengan 3 panel + auto-refresh
- Hari 4: Tambahkan Chart.js (distribusi bahasa sebagai pie chart)
- Hari 5: Styling + testing dengan data nyata

---

## Persiapan Lingkungan Kerja

### Step 1: Install Tools

```bash
# 1. Install Docker Desktop
# Download dari https://www.docker.com/products/docker-desktop/

# 2. Install Python 3.9+
python --version  # Verifikasi

# 3. Install Git
git --version

# 4. Install VS Code
# Download dari https://code.visualstudio.com/

# 5. Install VS Code extensions (rekomendasi)
# - Python (Microsoft)
# - Docker
# - GitLens
# - Jupyter
```

### Step 2: Clone & Setup Repository

```bash
# Buat folder proyek
git clone https://github.com/[username]/[repo-name].git
cd [repo-name]

# Buat struktur folder
mkdir -p kafka spark dashboard/templates dashboard/static dashboard/data

# Buat .gitignore
cat > .gitignore << 'EOF'
dashboard/data/
__pycache__/
*.pyc
.env
*.log
*.json.tmp
EOF
```

### Step 3: Setup Virtual Environment

```bash
# Buat virtual environment
python -m venv venv

# Aktifkan (Windows)
.\venv\bin\activate

# Aktifkan (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install kafka-python feedparser hdfs flask flask-cors requests python-dotenv pyspark
```

### Step 4: Dapatkan GitHub Personal Access Token

1. Buka https://github.com/settings/tokens
2. Klik **"Generate new token (classic)"**
3. Centang scope: `public_repo`, `read:org`
4. Salin token → simpan di file `.env`:

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

---

## Komponen 1: Apache Kafka

### docker-compose-kafka.yml

```yaml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka-broker:
    image: confluentinc/cp-kafka:7.5.0
    container_name: kafka-broker
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "29092:29092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka-broker:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
```

```bash
# Jalankan Kafka
docker-compose -f docker-compose-kafka.yml up -d

# Buat topic (jika belum auto-create)
docker exec -it kafka-broker kafka-topics.sh \
  --create --topic github-api \
  --bootstrap-server localhost:9092 \
  --partitions 1 --replication-factor 1

docker exec -it kafka-broker kafka-topics.sh \
  --create --topic github-rss \
  --bootstrap-server localhost:9092 \
  --partitions 1 --replication-factor 1

# Verifikasi topic
docker exec -it kafka-broker kafka-topics.sh \
  --list --bootstrap-server localhost:9092
```

---

### kafka/producer_api.py

```python
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
    logger.info("🚀 GitHub API Producer dimulai")
    logger.info(f"Topic: {KAFKA_TOPIC} | Interval: {POLLING_INTERVAL//60} menit")
    
    producer = create_producer()
    
    try:
        while True:
            logger.info(f"⏳ Fetching data dari GitHub API...")
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
                logger.info(f"✅ Berhasil kirim {sent_count}/{len(repos)} event ke topic '{KAFKA_TOPIC}'")
            else:
                logger.warning("Tidak ada data yang di-fetch, coba lagi di interval berikutnya")
            
            logger.info(f"😴 Menunggu {POLLING_INTERVAL//60} menit sebelum polling berikutnya...")
            time.sleep(POLLING_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Producer dihentikan oleh user")
    finally:
        producer.close()
        logger.info("Producer ditutup")


if __name__ == '__main__':
    main()
```

---

### kafka/producer_rss.py

```python
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
    logger.info("📰 RSS Feed Producer dimulai")
    logger.info(f"Topic: {KAFKA_TOPIC} | Interval: {POLLING_INTERVAL//60} menit")
    
    producer = create_producer()
    
    try:
        while True:
            logger.info("⏳ Polling RSS feeds...")
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
            logger.info(f"✅ Total {total_sent} artikel baru dikirim ke '{KAFKA_TOPIC}'")
            logger.info(f"📊 Total artikel di-track: {len(sent_ids)}")
            
            logger.info(f"😴 Menunggu {POLLING_INTERVAL//60} menit...")
            time.sleep(POLLING_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("RSS Producer dihentikan")
    finally:
        producer.close()


if __name__ == '__main__':
    main()
```

---

### Verifikasi Kafka Berjalan

```bash
# 1. Cek topic yang ada
docker exec -it kafka-broker kafka-topics.sh \
  --list --bootstrap-server localhost:9092

# 2. Monitor event masuk ke github-api (real-time)
docker exec -it kafka-broker kafka-console-consumer.sh \
  --topic github-api \
  --from-beginning \
  --bootstrap-server localhost:9092

# 3. Cek consumer group dan LAG
docker exec -it kafka-broker kafka-consumer-groups.sh \
  --describe \
  --group github-consumer-group \
  --bootstrap-server localhost:9092

# 4. Cek detail topic
docker exec -it kafka-broker kafka-topics.sh \
  --describe --topic github-api \
  --bootstrap-server localhost:9092
```

---

## Komponen 2: HDFS Storage Layer

### docker-compose-hadoop.yml

```yaml
version: "3"

services:
  namenode:
    image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
    container_name: namenode
    restart: always
    ports:
      - 9870:9870
      - 8020:8020
    volumes:
      - hadoop_namenode:/hadoop/dfs/name
    environment:
      - CLUSTER_NAME=test
    env_file:
      - ./hadoop.env

  datanode:
    image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
    container_name: datanode
    restart: always
    volumes:
      - hadoop_datanode:/hadoop/dfs/data
    environment:
      SERVICE_PRECONDITION: "namenode:9870"
    env_file:
      - ./hadoop.env

  resourcemanager:
    image: bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8
    container_name: resourcemanager
    restart: always
    environment:
      SERVICE_PRECONDITION: "namenode:8020 namenode:9870 datanode:9864"
    env_file:
      - ./hadoop.env

  nodemanager1:
    image: bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8
    container_name: nodemanager
    restart: always
    environment:
      SERVICE_PRECONDITION: "namenode:8020 namenode:9870 datanode:9864 resourcemanager:8088"
    env_file:
      - ./hadoop.env

  historyserver:
    image: bde2020/hadoop-historyserver:2.0.0-hadoop3.2.1-java8
    container_name: historyserver
    restart: always
    environment:
      SERVICE_PRECONDITION: "namenode:8020 namenode:9870 datanode:9864 resourcemanager:8088"
    volumes:
      - hadoop_historyserver:/hadoop/yarn/timeline
    env_file:
      - ./hadoop.env

volumes:
  hadoop_namenode:
  hadoop_datanode:
  hadoop_historyserver:
```

### hadoop.env

```env
CORE_CONF_fs_defaultFS=hdfs://namenode:8020
CORE_CONF_hadoop_http_staticuser_user=root
CORE_CONF_hadoop_proxyuser_hue_hosts=*
CORE_CONF_hadoop_proxyuser_hue_groups=*
CORE_CONF_io_compression_codecs=org.apache.hadoop.io.compress.SnappyCodec

HDFS_CONF_dfs_webhdfs_enabled=true
HDFS_CONF_dfs_permissions_enabled=false
HDFS_CONF_dfs_namenode_datanode_registration_ip___hostname___check=false

YARN_CONF_yarn_log___aggregation___enable=true
YARN_CONF_yarn_log_server_url=http://historyserver:8188/applicationhistory/logs/
YARN_CONF_yarn_resourcemanager_recovery_enabled=true
YARN_CONF_yarn_resourcemanager_store_class=org.apache.hadoop.yarn.server.resourcemanager.recovery.FileSystemRMStateStore
YARN_CONF_yarn_resourcemanager_scheduler_class=org.apache.hadoop.yarn.server.resourcemanager.scheduler.capacity.CapacityScheduler
YARN_CONF_yarn_scheduler_capacity_root_default_maximum___allocation___mb=8192
YARN_CONF_yarn_scheduler_capacity_root_default_maximum___allocation___vcores=4
YARN_CONF_yarn_resourcemanager_fs_state___store_uri=/rmstate
YARN_CONF_yarn_resourcemanager_system___metrics___publisher_enabled=true
YARN_CONF_yarn_resourcemanager_hostname=resourcemanager
YARN_CONF_yarn_resourcemanager_address=resourcemanager:8032
YARN_CONF_yarn_resourcemanager_scheduler_address=resourcemanager:8030
YARN_CONF_yarn_resourcemanager_resource__tracker_address=resourcemanager:8031
YARN_CONF_yarn_timeline___service_enabled=true
YARN_CONF_yarn_timeline___service_generic___application___history_enabled=true
YARN_CONF_yarn_timeline___service_hostname=historyserver
YARN_CONF_mapreduce_map_output_compress=true
YARN_CONF_mapred_map_output_compress_codec=org.apache.hadoop.io.compress.SnappyCodec
YARN_CONF_yarn_nodemanager_resource_memory___mb=16384
YARN_CONF_yarn_nodemanager_resource_cpu___vcores=8
YARN_CONF_yarn_nodemanager_disk___health___checker_max___disk___utilization___per___disk___percentage=98.5
YARN_CONF_yarn_nodemanager_remote___app___log___dir=/app-logs
YARN_CONF_yarn_nodemanager_aux___services=mapreduce_shuffle
```

### Setup Direktori HDFS

```bash
# Jalankan Hadoop
docker-compose -f docker-compose-hadoop.yml up -d

# Tunggu namenode ready (cek di http://localhost:9870)
# Buat struktur direktori di HDFS
docker exec -it namenode hdfs dfs -mkdir -p /data/github/api
docker exec -it namenode hdfs dfs -mkdir -p /data/github/rss
docker exec -it namenode hdfs dfs -mkdir -p /data/github/hasil

# Beri permission
docker exec -it namenode hdfs dfs -chmod -R 777 /data

# Verifikasi
docker exec -it namenode hdfs dfs -ls -R /data/
```

---

### kafka/consumer_to_hdfs.py

```python
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
```

---

## Komponen 3: Apache Spark

### Menjalankan Spark di Google Colab

Karena Spark membutuhkan resource besar, Google Colab adalah pilihan termudah untuk mahasiswa.

```python
# Cell 1: Install PySpark di Colab
!pip install pyspark findspark
```

---

### spark/analysis.ipynb (Konten Notebook)

#### Cell 1: Setup & Import

```python
# Setup SparkSession
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
import json
import os

# Inisialisasi Spark
# Opsi A: Spark lokal (untuk testing tanpa HDFS)
spark = SparkSession.builder \
    .appName("GitTrend Analysis") \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

# Opsi B: Spark dengan HDFS (untuk submission final)
# spark = SparkSession.builder \
#     .appName("GitTrend Analysis") \
#     .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:8020") \
#     .config("spark.driver.memory", "2g") \
#     .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print(f"✅ SparkSession berhasil! Version: {spark.version}")
```

#### Cell 2: Load Data dari HDFS

```python
# ============================================
# LOAD DATA DARI HDFS
# ============================================

# Path HDFS
HDFS_API_PATH = "hdfs://namenode:8020/data/github/api/"
HDFS_RSS_PATH = "hdfs://namenode:8020/data/github/rss/"

# Untuk testing lokal (ganti dengan path HDFS saat final)
# HDFS_API_PATH = "./sample_data/api/"

try:
    # Baca semua file JSON dari folder API
    df_api = spark.read \
        .option("multiLine", True) \
        .json(HDFS_API_PATH)
    
    # Jika data berupa array JSON (output consumer), perlu explode
    # df_api = df_api.select(F.explode(F.col("_corrupt_record")).alias("data"))
    
    print(f"✅ Data API dimuat: {df_api.count()} records")
    df_api.printSchema()
    df_api.show(5, truncate=50)
    
except Exception as e:
    print(f"⚠️ Error load HDFS: {e}")
    print("Menggunakan sample data lokal untuk demo...")
    
    # Fallback ke data lokal
    df_api = spark.read \
        .option("multiLine", True) \
        .json("./sample_api_data.json")

# Load RSS data
try:
    df_rss = spark.read \
        .option("multiLine", True) \
        .json(HDFS_RSS_PATH)
    print(f"✅ Data RSS dimuat: {df_rss.count()} records")
except Exception as e:
    print(f"⚠️ RSS data tidak tersedia: {e}")
    df_rss = None
```

#### Cell 3: Analisis 1 — Distribusi Bahasa Pemrograman

```python
# ============================================
# ANALISIS 1: DISTRIBUSI BAHASA PEMROGRAMAN
# ============================================
print("=" * 60)
print("ANALISIS 1: Distribusi Bahasa Pemrograman di Repo Trending")
print("=" * 60)

# Register sebagai temp view untuk Spark SQL
df_api.createOrReplaceTempView("github_repos")

# Menggunakan Spark SQL
lang_distribution = spark.sql("""
    SELECT 
        COALESCE(language, 'Unknown') AS language,
        COUNT(*) AS total_repo,
        SUM(stargazers_count) AS total_stars,
        ROUND(AVG(stargazers_count), 0) AS avg_stars,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
    FROM github_repos
    WHERE language IS NOT NULL AND language != ''
    GROUP BY language
    ORDER BY total_repo DESC
    LIMIT 15
""")

lang_distribution.show(15, truncate=False)

# Simpan hasil
lang_df = lang_distribution.toPandas()

print("\n📊 INTERPRETASI BISNIS:")
top_lang = lang_df.iloc[0]['language']
top_pct = lang_df.iloc[0]['percentage']
print(f"""
Dari {df_api.count()} repositori trending yang dianalisis:

• Bahasa pemrograman PALING DOMINAN adalah {top_lang} ({top_pct}% dari semua repo).
  Ini menunjukkan bahwa komunitas open source saat ini sangat aktif
  dalam ekosistem {top_lang}.

• Top 3 bahasa mencakup {lang_df.head(3)['percentage'].sum():.1f}% dari semua repo trending,
  mengindikasikan konsentrasi tinggi pada beberapa bahasa utama.

• Rekomendasi untuk newsletter: Fokus kurasi konten pada proyek {top_lang}
  dan {lang_df.iloc[1]['language']} untuk menjangkau developer terbanyak.
""")
```

#### Cell 4: Analisis 2 — Top 10 Repositori Berdasarkan Stars

```python
# ============================================
# ANALISIS 2: TOP 10 REPOSITORI (LEADERBOARD)
# ============================================
print("=" * 60)
print("ANALISIS 2: Top 10 Repositori Berdasarkan Stars")
print("=" * 60)

# Menggunakan DataFrame API
top_repos = df_api.select(
    'full_name',
    'language',
    'stargazers_count',
    'forks_count',
    'description',
    'topics',
    'html_url'
) \
.orderBy(F.desc('stargazers_count')) \
.limit(10)

top_repos.show(10, truncate=60)

# Format untuk output yang lebih readable
top_repos_pandas = top_repos.toPandas()

print("\n🏆 LEADERBOARD REPO TRENDING:")
print("-" * 80)
for i, row in top_repos_pandas.iterrows():
    desc_preview = str(row['description'])[:60] + "..." if len(str(row['description'])) > 60 else str(row['description'])
    print(f"{i+1:2}. {'⭐' * min(5, row['stargazers_count']//1000)} {row['full_name']}")
    print(f"    ⭐ {row['stargazers_count']:,} stars | 🍴 {row['forks_count']:,} forks | 💻 {row['language']}")
    print(f"    📝 {desc_preview}")
    print()

print("\n📊 INTERPRETASI BISNIS:")
print(f"""
• Repositori #1 ({top_repos_pandas.iloc[0]['full_name']}) mendapat 
  {top_repos_pandas.iloc[0]['stargazers_count']:,} bintang — signifikan untuk dimasukkan
  dalam edisi newsletter sebagai "Proyek Pilihan Minggu Ini".

• Dari top 10, bahasa dominan adalah:
  {top_repos_pandas['language'].value_counts().to_dict()}

• Proyek-proyek ini adalah kandidat utama untuk kurasi newsletter — 
  tingginya engagement (stars + forks) menunjukkan relevansi komunitas yang tinggi.
""")
```

#### Cell 5: Analisis 3 — Kata Trending di Deskripsi

```python
# ============================================
# ANALISIS 3: KATA PALING SERING DI DESKRIPSI/TOPIK
# ============================================
print("=" * 60)
print("ANALISIS 3: Tema Proyek — Kata Paling Sering Muncul")
print("=" * 60)

# Stopwords yang akan difilter
STOPWORDS = {
    'the', 'and', 'for', 'with', 'from', 'this', 'that', 'are', 'was', 
    'were', 'will', 'have', 'been', 'your', 'you', 'our', 'their', 'its',
    'using', 'based', 'built', 'made', 'tool', 'open', 'source', 'project',
    'new', 'add', 'use', 'get', 'run', 'make', 'can', 'also'
}

# Menggunakan DataFrame API - split deskripsi menjadi kata-kata
word_freq = df_api \
    .select(
        F.explode(
            F.split(
                F.lower(F.regexp_replace(F.col('description'), '[^a-zA-Z\\s]', '')),
                ' '
            )
        ).alias('word')
    ) \
    .filter(F.length('word') >= 4) \
    .filter(~F.col('word').isin(list(STOPWORDS))) \
    .filter(F.col('word') != '') \
    .groupBy('word') \
    .agg(F.count('*').alias('frequency')) \
    .orderBy(F.desc('frequency')) \
    .limit(30)

# Tambahkan juga kata dari topics
topics_words = df_api \
    .select(F.explode(F.col('topics')).alias('word')) \
    .filter(F.length('word') >= 4) \
    .groupBy('word') \
    .agg(F.count('*').alias('frequency')) \
    .orderBy(F.desc('frequency')) \
    .limit(20)

word_freq.show(20, truncate=False)
topics_words.show(20, truncate=False)

word_df = word_freq.toPandas()
topics_df = topics_words.toPandas()

print("\n📊 INTERPRETASI BISNIS:")
top_words = word_df.head(5)['word'].tolist()
top_topics = topics_df.head(5)['word'].tolist()
print(f"""
• Kata-kata yang PALING SERING muncul di deskripsi repo: {', '.join(top_words)}
  Ini mencerminkan TEMA UTAMA yang sedang tren di komunitas open source.

• Topik (tags) yang paling banyak digunakan: {', '.join(top_topics)}
  Topik-topik ini bisa dijadikan kategori utama untuk newsletter.

• Rekomendasi: Newsletter bisa mengkategorikan artikel berdasarkan
  tema-tema ini — misal seksi "🤖 AI Tools", "🔒 Security", "☁️ Cloud Native".
""")
```

#### Cell 6: Simpan Hasil ke HDFS & JSON

```python
# ============================================
# SIMPAN HASIL KE HDFS DAN LOCAL JSON
# ============================================

import json
from datetime import datetime

print("💾 Menyimpan hasil analisis...")

# Simpan ke HDFS (format Parquet untuk efisiensi)
try:
    lang_distribution.write \
        .mode('overwrite') \
        .json("hdfs://namenode:8020/data/github/hasil/language_distribution")
    
    top_repos.write \
        .mode('overwrite') \
        .json("hdfs://namenode:8020/data/github/hasil/top_repos")
    
    word_freq.write \
        .mode('overwrite') \
        .json("hdfs://namenode:8020/data/github/hasil/word_frequency")
    
    print("✅ Hasil tersimpan ke HDFS /data/github/hasil/")
except Exception as e:
    print(f"⚠️ Tidak bisa simpan ke HDFS: {e}")

# Simpan sebagai JSON lokal untuk dashboard
spark_results = {
    'generated_at': datetime.now().isoformat(),
    'summary': {
        'total_repos_analyzed': int(df_api.count()),
        'analysis_date': datetime.now().strftime('%Y-%m-%d')
    },
    'language_distribution': lang_df.to_dict('records'),
    'top_repos': top_repos_pandas.to_dict('records'),
    'trending_words': word_df.head(20).to_dict('records'),
    'trending_topics': topics_df.head(15).to_dict('records')
}

# Bersihkan nilai NaN
import math
def clean_nan(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(i) for i in obj]
    return obj

spark_results = clean_nan(spark_results)

os.makedirs('dashboard/data', exist_ok=True)
with open('dashboard/data/spark_results.json', 'w', encoding='utf-8') as f:
    json.dump(spark_results, f, ensure_ascii=False, indent=2, default=str)

print("✅ spark_results.json tersimpan untuk dashboard!")
print(f"📊 Total data: {len(spark_results['language_distribution'])} bahasa, {len(spark_results['top_repos'])} repo")

spark.stop()
print("✅ SparkSession ditutup")
```

---

## Komponen 4: Dashboard Flask

### dashboard/app.py

```python
"""
Flask Dashboard untuk GitTrend Big Data Pipeline
Menampilkan: Spark Results + Live API Data + Live RSS Feed
Berjalan di http://localhost:5000
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Path ke file data
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def read_json_safe(filepath: str, default=None):
    """Baca file JSON dengan error handling."""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {filepath}: {e}")
    return default if default is not None else {}


@app.route('/')
def index():
    """Halaman utama dashboard."""
    return render_template('index.html')


@app.route('/api/data')
def get_all_data():
    """
    Endpoint utama — return semua data dalam satu response.
    Frontend polling endpoint ini setiap 30 detik.
    """
    spark_results = read_json_safe(
        os.path.join(DATA_DIR, 'spark_results.json'),
        default={'summary': {}, 'language_distribution': [], 'top_repos': [], 'trending_words': []}
    )
    
    live_api = read_json_safe(
        os.path.join(DATA_DIR, 'live_api.json'),
        default=[]
    )
    
    live_rss = read_json_safe(
        os.path.join(DATA_DIR, 'live_rss.json'),
        default=[]
    )
    
    # Ambil 10 repo terbaru dari live feed
    latest_repos = sorted(
        live_api[-50:] if isinstance(live_api, list) else [],
        key=lambda x: x.get('stargazers_count', 0),
        reverse=True
    )[:10]
    
    # Ambil 10 berita terbaru dari RSS
    latest_news = (live_rss[-20:] if isinstance(live_rss, list) else [])[::-1][:10]
    
    return jsonify({
        'status': 'ok',
        'last_updated': datetime.now().isoformat(),
        'spark': spark_results,
        'live_repos': latest_repos,
        'latest_news': latest_news
    })


@app.route('/api/status')
def get_status():
    """Status pipeline — untuk monitoring."""
    files = ['spark_results.json', 'live_api.json', 'live_rss.json']
    status = {}
    
    for fname in files:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            stat = os.stat(fpath)
            status[fname] = {
                'exists': True,
                'size_kb': round(stat.st_size / 1024, 2),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        else:
            status[fname] = {'exists': False}
    
    return jsonify({'status': 'ok', 'files': status})


if __name__ == '__main__':
    # Pastikan folder data ada
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("🚀 GitTrend Dashboard dimulai di http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

### dashboard/templates/index.html

```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔭 GitTrend Dashboard</title>
    
    <!-- Chart.js untuk visualisasi (Bonus +3 poin) -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            min-height: 100vh;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #161b22, #1f6feb);
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #30363d;
        }
        
        .header h1 { font-size: 1.5rem; color: #fff; }
        
        .status-badge {
            background: #238636;
            color: #fff;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
        }
        
        .last-update {
            font-size: 0.8rem;
            color: #8b949e;
            margin-top: 4px;
        }
        
        /* Layout Grid */
        .container { max-width: 1400px; margin: 0 auto; padding: 24px; }
        
        .grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .grid-full { margin-bottom: 24px; }
        
        /* Cards */
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
        }
        
        .card-title {
            font-size: 0.9rem;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Stat Cards */
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #58a6ff;
        }
        
        .stat-label { font-size: 0.85rem; color: #8b949e; margin-top: 4px; }
        
        /* Repo Leaderboard */
        .repo-item {
            display: flex;
            align-items: flex-start;
            padding: 12px 0;
            border-bottom: 1px solid #21262d;
            gap: 12px;
        }
        
        .repo-item:last-child { border-bottom: none; }
        
        .repo-rank {
            font-size: 1.2rem;
            font-weight: 700;
            color: #f0b429;
            min-width: 30px;
        }
        
        .repo-info { flex: 1; }
        
        .repo-name {
            color: #58a6ff;
            font-weight: 600;
            font-size: 0.95rem;
            text-decoration: none;
        }
        
        .repo-name:hover { text-decoration: underline; }
        
        .repo-desc {
            font-size: 0.8rem;
            color: #8b949e;
            margin: 4px 0;
            line-height: 1.4;
        }
        
        .repo-meta {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .badge {
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 12px;
            background: #21262d;
            color: #c9d1d9;
        }
        
        .badge.stars { background: #2d3748; color: #f0b429; }
        .badge.language { background: #1f3a52; color: #79c0ff; }
        
        /* News Feed */
        .news-item {
            padding: 12px 0;
            border-bottom: 1px solid #21262d;
        }
        
        .news-item:last-child { border-bottom: none; }
        
        .news-title {
            color: #e6edf3;
            font-size: 0.9rem;
            font-weight: 500;
            text-decoration: none;
            line-height: 1.4;
        }
        
        .news-title:hover { color: #58a6ff; }
        
        .news-meta {
            font-size: 0.75rem;
            color: #8b949e;
            margin-top: 4px;
        }
        
        /* Charts */
        .chart-container { position: relative; height: 300px; }
        
        /* Loading */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: #8b949e;
        }
        
        /* Refresh indicator */
        .refresh-bar {
            height: 3px;
            background: #1f6feb;
            width: 0%;
            transition: width 30s linear;
            border-radius: 2px;
        }
        
        @media (max-width: 768px) {
            .grid-3 { grid-template-columns: 1fr; }
            .grid-2 { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

<div class="header">
    <div>
        <h1>🔭 GitTrend Monitor</h1>
        <div class="last-update" id="lastUpdate">Memuat data...</div>
    </div>
    <div>
        <span class="status-badge" id="statusBadge">● LIVE</span>
        <div style="margin-top: 8px;">
            <div class="refresh-bar" id="refreshBar"></div>
        </div>
    </div>
</div>

<div class="container">

    <!-- PANEL 1: Stats Summary -->
    <div class="grid-3">
        <div class="card">
            <div class="card-title">📦 Total Repo Dianalisis</div>
            <div class="stat-value" id="totalRepos">—</div>
            <div class="stat-label">Dari HDFS via Spark</div>
        </div>
        <div class="card">
            <div class="card-title">💻 Bahasa Terpopuler</div>
            <div class="stat-value" id="topLanguage">—</div>
            <div class="stat-label" id="topLanguagePct">% dari total repo</div>
        </div>
        <div class="card">
            <div class="card-title">📰 Berita Terbaru</div>
            <div class="stat-value" id="newsCount">—</div>
            <div class="stat-label">Artikel dari RSS feed</div>
        </div>
    </div>

    <!-- PANEL 1: Spark Analysis — Chart + Leaderboard -->
    <div class="grid-2">
        <!-- Chart Distribusi Bahasa -->
        <div class="card">
            <div class="card-title">🥧 Distribusi Bahasa Pemrograman</div>
            <div class="chart-container">
                <canvas id="languageChart"></canvas>
            </div>
        </div>
        
        <!-- Top Repos Leaderboard -->
        <div class="card">
            <div class="card-title">🏆 Top Repositori (Live)</div>
            <div id="liveReposList">
                <div class="loading">⏳ Memuat data live...</div>
            </div>
        </div>
    </div>

    <!-- PANEL 2: Top Repos dari Spark -->
    <div class="grid-full">
        <div class="card">
            <div class="card-title">⭐ Top 10 Repo dari Analisis Spark</div>
            <div id="sparkReposList">
                <div class="loading">⏳ Memuat hasil Spark...</div>
            </div>
        </div>
    </div>

    <!-- PANEL 3: Trending Words + RSS News -->
    <div class="grid-2">
        <!-- Trending Words Chart -->
        <div class="card">
            <div class="card-title">🔤 Kata Trending di Deskripsi</div>
            <div class="chart-container">
                <canvas id="wordsChart"></canvas>
            </div>
        </div>
        
        <!-- RSS News Feed -->
        <div class="card">
            <div class="card-title">📰 Berita Teknologi Terbaru</div>
            <div id="newsList">
                <div class="loading">⏳ Memuat berita...</div>
            </div>
        </div>
    </div>

</div>

<script>
// ============================================
// JAVASCRIPT — Auto-refresh & Data Fetching
// ============================================

let languageChart = null;
let wordsChart = null;
const REFRESH_INTERVAL = 30000; // 30 detik

// Warna untuk chart
const CHART_COLORS = [
    '#1f6feb', '#f0b429', '#3fb950', '#ff7b72', '#d2a8ff',
    '#79c0ff', '#56d364', '#ffa657', '#f85149', '#a5f3fc'
];

async function fetchData() {
    try {
        const response = await fetch('/api/data');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        document.getElementById('statusBadge').textContent = '● ERROR';
        document.getElementById('statusBadge').style.background = '#da3633';
        return null;
    }
}

function updateStats(data) {
    const spark = data.spark || {};
    const summary = spark.summary || {};
    const langDist = spark.language_distribution || [];
    
    document.getElementById('totalRepos').textContent = 
        (summary.total_repos_analyzed || '—').toLocaleString();
    
    if (langDist.length > 0) {
        const topLang = langDist[0];
        document.getElementById('topLanguage').textContent = topLang.language || '—';
        document.getElementById('topLanguagePct').textContent = 
            `${topLang.percentage || 0}% dari total repo`;
    }
    
    document.getElementById('newsCount').textContent = 
        (data.latest_news || []).length;
    
    document.getElementById('lastUpdate').textContent = 
        `Terakhir update: ${new Date().toLocaleTimeString('id-ID')}`;
}

function renderLanguageChart(langData) {
    const ctx = document.getElementById('languageChart').getContext('2d');
    
    const labels = langData.slice(0, 8).map(d => d.language);
    const values = langData.slice(0, 8).map(d => d.total_repo);
    
    if (languageChart) languageChart.destroy();
    
    languageChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: CHART_COLORS,
                borderColor: '#0d1117',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#c9d1d9',
                        font: { size: 11 },
                        padding: 8
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.label}: ${ctx.raw} repo`
                    }
                }
            }
        }
    });
}

function renderWordsChart(words) {
    const ctx = document.getElementById('wordsChart').getContext('2d');
    
    const top15 = words.slice(0, 15);
    const labels = top15.map(d => d.word);
    const values = top15.map(d => d.frequency);
    
    if (wordsChart) wordsChart.destroy();
    
    wordsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Frekuensi',
                data: values,
                backgroundColor: '#1f6feb',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    ticks: { color: '#8b949e' },
                    grid: { color: '#21262d' }
                },
                y: {
                    ticks: { color: '#c9d1d9', font: { size: 11 } },
                    grid: { color: '#21262d' }
                }
            }
        }
    });
}

function renderLiveRepos(repos) {
    const container = document.getElementById('liveReposList');
    
    if (!repos || repos.length === 0) {
        container.innerHTML = '<div class="loading">Tidak ada data live</div>';
        return;
    }
    
    container.innerHTML = repos.slice(0, 8).map((repo, i) => `
        <div class="repo-item">
            <div class="repo-rank">${i + 1}</div>
            <div class="repo-info">
                <a href="${repo.html_url || '#'}" target="_blank" class="repo-name">
                    ${repo.full_name || 'N/A'}
                </a>
                <div class="repo-desc">
                    ${(repo.description || 'No description').substring(0, 80)}...
                </div>
                <div class="repo-meta">
                    <span class="badge stars">⭐ ${(repo.stargazers_count || 0).toLocaleString()}</span>
                    <span class="badge language">💻 ${repo.language || 'Unknown'}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function renderSparkRepos(repos) {
    const container = document.getElementById('sparkReposList');
    
    if (!repos || repos.length === 0) {
        container.innerHTML = '<div class="loading">Belum ada hasil Spark</div>';
        return;
    }
    
    container.innerHTML = `
        <div style="overflow-x: auto;">
        <table style="width:100%; border-collapse: collapse; font-size: 0.875rem;">
            <thead>
                <tr style="border-bottom: 1px solid #30363d; color: #8b949e; text-align: left;">
                    <th style="padding: 8px 12px;">#</th>
                    <th style="padding: 8px 12px;">Repository</th>
                    <th style="padding: 8px 12px;">Bahasa</th>
                    <th style="padding: 8px 12px;">⭐ Stars</th>
                    <th style="padding: 8px 12px;">Deskripsi</th>
                </tr>
            </thead>
            <tbody>
                ${repos.slice(0, 10).map((repo, i) => `
                    <tr style="border-bottom: 1px solid #21262d;">
                        <td style="padding: 10px 12px; color: #f0b429; font-weight: bold;">${i+1}</td>
                        <td style="padding: 10px 12px;">
                            <a href="${repo.html_url || '#'}" target="_blank" 
                               style="color: #58a6ff; text-decoration: none; font-weight: 600;">
                               ${repo.full_name || 'N/A'}
                            </a>
                        </td>
                        <td style="padding: 10px 12px;">
                            <span class="badge language">${repo.language || 'Unknown'}</span>
                        </td>
                        <td style="padding: 10px 12px; color: #f0b429; font-weight: 600;">
                            ${(repo.stargazers_count || 0).toLocaleString()}
                        </td>
                        <td style="padding: 10px 12px; color: #8b949e; max-width: 300px;">
                            ${(repo.description || '-').substring(0, 80)}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        </div>
    `;
}

function renderNews(news) {
    const container = document.getElementById('newsList');
    
    if (!news || news.length === 0) {
        container.innerHTML = '<div class="loading">Belum ada berita</div>';
        return;
    }
    
    container.innerHTML = news.map(item => `
        <div class="news-item">
            <a href="${item.link || '#'}" target="_blank" class="news-title">
                ${item.title || 'No title'}
            </a>
            <div class="news-meta">
                📅 ${item.published || 'Unknown'} 
                ${item.author ? `· ✍️ ${item.author}` : ''}
            </div>
        </div>
    `).join('');
}

// Refresh bar animation
function startRefreshBar() {
    const bar = document.getElementById('refreshBar');
    bar.style.width = '0%';
    bar.style.transition = 'none';
    
    setTimeout(() => {
        bar.style.transition = `width ${REFRESH_INTERVAL/1000}s linear`;
        bar.style.width = '100%';
    }, 100);
}

// Main update function
async function updateDashboard() {
    const data = await fetchData();
    if (!data) return;
    
    const spark = data.spark || {};
    
    updateStats(data);
    
    if (spark.language_distribution?.length > 0) {
        renderLanguageChart(spark.language_distribution);
    }
    
    if (spark.trending_words?.length > 0) {
        renderWordsChart(spark.trending_words);
    }
    
    if (spark.top_repos?.length > 0) {
        renderSparkRepos(spark.top_repos);
    }
    
    renderLiveRepos(data.live_repos || []);
    renderNews(data.latest_news || []);
    
    startRefreshBar();
}

// Inisialisasi
updateDashboard();

// Auto-refresh setiap 30 detik
setInterval(updateDashboard, REFRESH_INTERVAL);
</script>

</body>
</html>
```

---

## README.md Template

```markdown
# 🔭 GitTrend: Monitor Repositori Open Source Populer
## ETS Big Data — Topik 7

---

## 👥 Anggota Kelompok

| Nama | NIM | Kontribusi |
|------|-----|------------|
| [Nama 1] | [NIM] | Project Lead, Docker Setup, Integrasi |
| [Nama 2] | [NIM] | Kafka Producer API (GitHub REST) |
| [Nama 3] | [NIM] | Kafka Producer RSS + Consumer HDFS |
| [Nama 4] | [NIM] | Spark Analysis (3 analisis wajib) |
| [Nama 5] | [NIM] | Flask Dashboard + Chart.js |

---

## 🎯 Topik yang Dipilih

**GitTrend** — monitoring repositori GitHub trending untuk newsletter teknologi mingguan.

**Justifikasi:** GitHub adalah barometer terbaik aktivitas open source global. Dengan memonitor repo trending secara real-time, newsletter dapat mengkurasi konten yang paling relevan untuk pembaca developer. Data GitHub bersifat publik, gratis, dan terus berubah — sempurna untuk demonstrasi pipeline big data.

---

## 🏗️ Diagram Arsitektur

[Sisipkan gambar diagram di sini — bisa dari draw.io atau gambar tangan]

---

## 🚀 Cara Menjalankan Sistem

### Prasyarat
- Docker Desktop terinstall
- Python 3.9+
- Git

### Step 1: Clone Repository
\`\`\`bash
git clone https://github.com/[username]/[repo].git
cd [repo]
\`\`\`

### Step 2: Setup Environment
\`\`\`bash
pip install kafka-python feedparser hdfs flask flask-cors requests python-dotenv
cp .env.example .env
# Edit .env: masukkan GITHUB_TOKEN
\`\`\`

### Step 3: Jalankan Kafka
\`\`\`bash
docker-compose -f docker-compose-kafka.yml up -d
# Buat topic
docker exec -it kafka-broker kafka-topics.sh --create --topic github-api --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker exec -it kafka-broker kafka-topics.sh --create --topic github-rss --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
\`\`\`

### Step 4: Jalankan Hadoop
\`\`\`bash
docker-compose -f docker-compose-hadoop.yml up -d
# Tunggu ~30 detik, buat direktori HDFS
docker exec -it namenode hdfs dfs -mkdir -p /data/github/api
docker exec -it namenode hdfs dfs -mkdir -p /data/github/rss
docker exec -it namenode hdfs dfs -mkdir -p /data/github/hasil
\`\`\`

### Step 5: Jalankan Producer & Consumer (terminal terpisah)
\`\`\`bash
# Terminal 1: Producer API
python kafka/producer_api.py

# Terminal 2: Producer RSS
python kafka/producer_rss.py

# Terminal 3: Consumer ke HDFS
python kafka/consumer_to_hdfs.py
\`\`\`

### Step 6: Tunggu Data Terkumpul (minimal 5 menit)
\`\`\`bash
# Verifikasi data di HDFS
docker exec -it namenode hdfs dfs -ls -R /data/github/
\`\`\`

### Step 7: Jalankan Spark Analysis
\`\`\`bash
# Buka spark/analysis.ipynb di Jupyter atau Google Colab
jupyter notebook spark/analysis.ipynb
\`\`\`

### Step 8: Jalankan Dashboard
\`\`\`bash
python dashboard/app.py
# Buka http://localhost:5000
\`\`\`

---

## 📸 Screenshots

### HDFS Web UI
[Screenshot http://localhost:9870]

### Kafka Consumer Output
[Screenshot terminal kafka-console-consumer]

### Dashboard Berjalan
[Screenshot http://localhost:5000]

---

## 💡 Tantangan & Solusi

| Tantangan | Solusi |
|-----------|--------|
| GitHub API rate limit (60 req/jam tanpa auth) | Gunakan Personal Access Token → 5000 req/jam |
| Consumer tidak bisa akses HDFS dari luar Docker | Gunakan `subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-put', ...])` |
| Spark tidak bisa baca HDFS dari lokal | Jalankan di Google Colab yang bisa mount drive, atau gunakan SparkContext dengan config HDFS |
| Data RSS duplikat | Tracking dengan set ID berbasis hash URL |
| Flask tidak bisa baca file JSON saat data belum ada | Buat `read_json_safe()` dengan default value |
```

---

## Tips Debugging & Troubleshooting

### 🐛 Kafka Issues

```bash
# Kafka tidak bisa connect
docker logs kafka-broker | tail -20

# Reset consumer offset (jika mau baca ulang dari awal)
docker exec -it kafka-broker kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group github-consumer-group \
  --topic github-api \
  --reset-offsets --to-earliest --execute

# Hapus topic dan buat ulang
docker exec -it kafka-broker kafka-topics.sh \
  --delete --topic github-api \
  --bootstrap-server localhost:9092
```

### 🐛 HDFS Issues

```bash
# Namenode masih dalam safe mode (baru start)
docker exec -it namenode hdfs dfsadmin -safemode leave

# Cek status namenode
docker exec -it namenode hdfs dfsadmin -report

# File tidak bisa di-put ke HDFS
docker exec -it namenode hdfs dfs -chmod -R 777 /data/github
```

### 🐛 Spark Issues

```python
# Spark tidak bisa baca JSON multi-level
df = spark.read.option("multiLine", True).json(path)

# Column tidak ketemu (karena schema inference gagal)
df.printSchema()  # Cek schema aktual dulu

# Spark tidak bisa connect HDFS
# Pastikan config: spark.hadoop.fs.defaultFS = hdfs://namenode:8020
# Dan port 8020 di-expose di docker-compose-hadoop.yml
```

### 🐛 Flask Issues

```python
# CORS error dari browser
# Sudah di-handle dengan flask-cors, pastikan: from flask_cors import CORS; CORS(app)

# Data tidak muncul di dashboard
# Cek apakah file JSON ada:
import os
print(os.path.exists('dashboard/data/spark_results.json'))

# File kosong atau format salah
import json
with open('dashboard/data/spark_results.json') as f:
    data = json.load(f)
    print(type(data))
```

---

## Checklist Final Submission

### Kafka (30 poin)
- [ ] `docker-compose-kafka.yml` berjalan dan semua container up
- [ ] Topic `github-api` dan `github-rss` terbuat
- [ ] `producer_api.py` mengirim event JSON valid ke `github-api` setiap 30 menit
- [ ] `producer_rss.py` mengirim berita ke `github-rss`, menghindari duplikat
- [ ] Consumer group terdaftar (cek dengan `--describe`)
- [ ] Screenshot `kafka-console-consumer` menampilkan event nyata

### HDFS (25 poin)
- [ ] `docker-compose-hadoop.yml` dan `hadoop.env` berjalan
- [ ] Direktori `/data/github/api/`, `/data/github/rss/`, `/data/github/hasil/` ada
- [ ] File JSON bernama timestamp tersimpan di kedua direktori
- [ ] `hdfs dfs -ls -R /data/github/` menampilkan file
- [ ] Screenshot HDFS Web UI (http://localhost:9870) di README

### Spark (30 poin)
- [ ] `analysis.ipynb` berjalan tanpa error
- [ ] Spark membaca dari HDFS (bukan file lokal)
- [ ] Analisis 1: Distribusi bahasa (groupBy + count)
- [ ] Analisis 2: Top 10 repo (orderBy stars)
- [ ] Analisis 3: Kata trending (split + filter + count)
- [ ] Setiap analisis ada narasi interpretasi bisnis
- [ ] `spark_results.json` tersimpan di `dashboard/data/`
- [ ] Hasil tersimpan di HDFS `/data/github/hasil/`

### Dashboard (15 poin)
- [ ] Flask berjalan di http://localhost:5000
- [ ] Panel 1: Hasil Spark (language distribution + top repos)
- [ ] Panel 2: Data live repo terbaru dari Kafka
- [ ] Panel 3: Berita RSS terbaru
- [ ] Auto-refresh setiap 30–60 detik berfungsi

### Bonus
- [ ] (+3) Chart.js dengan pie/bar chart distribusi bahasa
- [ ] (+2) Consumer HDFS menggunakan library Python `hdfs` (bukan subprocess)
- [ ] (+5) Spark MLlib: K-Means clustering atau Linear Regression

### README
- [ ] Nama anggota + kontribusi jelas
- [ ] Diagram arsitektur ada (foto atau draw.io)
- [ ] Step-by-step cara menjalankan
- [ ] Screenshot lengkap (HDFS UI + Kafka output + Dashboard)
- [ ] Seksi tantangan dan solusi

---

*Dokumen ini dibuat sebagai panduan lengkap ETS Big Data — Topik 7 GitTrend*  
*Dibuat: April 2026*
```
