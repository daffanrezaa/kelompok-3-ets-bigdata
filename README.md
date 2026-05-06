# 🚀 GitTrend — Monitor Repositori Open Source Populer

Big Data Pipeline end-to-end: **Kafka → HDFS → Spark → Flask Dashboard**

```
GitHub API (30 menit)          TechCrunch RSS (5 menit)
       │                              │
       ▼                              ▼
 producer_api.py               producer_rss.py
       │                              │
       ▼                              ▼
 Kafka: github-api             Kafka: github-rss
       │                              │
       └──────────┬───────────────────┘
                  ▼
         consumer_to_hdfs.py
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
  HDFS /data/github/   dashboard/data/
        │                   │
        ▼                   │
  analysis.ipynb (Spark)    │
        │                   │
        ▼                   ▼
  spark_results.json → Flask Dashboard :5000
```

---

## 📌 Prasyarat

| Tool             | Versi           |
| ---------------- | --------------- |
| Docker Desktop   | Latest          |
| Python           | 3.9+            |
| Git              | Latest          |

---

## ⚙️ Step 1 — Install Python Dependencies

```bash
pip install kafka-python feedparser hdfs flask flask-cors requests python-dotenv pyspark
```

---

## 🔑 Step 2 — Setup GitHub Token (Opsional, Disarankan)

Tanpa token, GitHub API rate limit = 10 request/jam. Dengan token = 30 request/jam.

1. Buka https://github.com/settings/tokens
2. Generate new token (classic) → centang `public_repo`
3. Buat file `.env` di root project:

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

---

## 🐳 Step 3 — Jalankan Docker Containers

### 3a. Jalankan Kafka + Zookeeper

```bash
docker-compose -f docker-compose-kafka.yml up -d
```

Verifikasi:
```bash
docker ps
# Harus muncul: zookeeper, kafka-broker
```

### 3b. Jalankan Hadoop Cluster

```bash
docker-compose -f docker-compose-hadoop.yml up -d
```

Verifikasi:
```bash
docker ps
# Harus muncul: namenode, datanode, resourcemanager, nodemanager, historyserver
```

Tunggu ~30 detik sampai namenode ready, lalu cek Web UI: http://localhost:9870

### 3c. Buat Direktori HDFS

```bash
docker exec -it namenode hdfs dfs -mkdir -p /data/github/api
docker exec -it namenode hdfs dfs -mkdir -p /data/github/rss
docker exec -it namenode hdfs dfs -mkdir -p /data/github/hasil
docker exec -it namenode hdfs dfs -chmod -R 777 /data
```

Verifikasi:
```bash
docker exec -it namenode hdfs dfs -ls -R /data/
```

---

## ▶️ Step 4 — Jalankan Pipeline (3 Terminal)

Buka **3 terminal terpisah**, semua masuk ke folder `kafka/`:

### Terminal 1 — Producer API (GitHub)

```bash
cd kafka
python producer_api.py
```

Output yang diharapkan:
```
GitHub API Producer dimulai
Topic: github-api | Interval: 30 menit
Berhasil fetch 30 repo. Rate limit remaining: 9
Berhasil kirim 30/30 event ke topic 'github-api'
Menunggu 30 menit sebelum polling berikutnya...
```

### Terminal 2 — Producer RSS (TechCrunch)

```bash
cd kafka
python producer_rss.py
```

Output yang diharapkan:
```
RSS Feed Producer dimulai
Topic: github-rss | Interval: 5 menit
Feed https://techcrunch.com/feed/: 20 total, 20 baru
Total 20 artikel baru dikirim ke 'github-rss'
```

### Terminal 3 — Consumer → HDFS

```bash
cd kafka
python consumer_to_hdfs.py
```

Output yang diharapkan:
```
Consumer HDFS dimulai
Topics: ['github-api', 'github-rss']
HDFS directory ready: /data/github/api
HDFS directory ready: /data/github/rss
Received 30 messages dari 'github-api'
Received 20 messages dari 'github-rss'
Flushed 30 events dari topic 'github-api'    ← (setelah 2 menit)
Flushed 20 events dari topic 'github-rss'
```

---

## 🧪 Step 5 — Verifikasi Data

### 5a. Verifikasi Kafka Topics

```bash
# List semua topic
docker exec -it kafka-broker kafka-topics --list --bootstrap-server localhost:9092

# Baca data dari topic github-api
docker exec -it kafka-broker kafka-console-consumer --topic github-api --from-beginning --bootstrap-server localhost:9092

# Baca data dari topic github-rss
docker exec -it kafka-broker kafka-console-consumer --topic github-rss --from-beginning --bootstrap-server localhost:9092
```

### 5b. Verifikasi Data di HDFS

```bash
# List file di HDFS
docker exec -it namenode hdfs dfs -ls -R /data/github/

# Baca isi salah satu file
docker exec -it namenode hdfs dfs -cat /data/github/api/<nama-file>.json
```

### 5c. Verifikasi File Lokal Dashboard

```bash
# Cek apakah file live data sudah ada
dir dashboard\data\
# Harus ada: live_api.json, live_rss.json
```

---

## 📊 Step 6 — Spark Analysis

Buka `spark/analysis.ipynb` di Jupyter Notebook atau Google Colab:

- Membaca data dari HDFS
- 3 analisis wajib: distribusi bahasa, top 10 repo, kata trending
- Output: `dashboard/data/spark_results.json`

---

## 🌐 Step 7 — Flask Dashboard

```bash
cd dashboard
python app.py
```

Buka browser: http://localhost:5000

---

## 🔧 Troubleshooting

| Problem | Solusi |
|---------|--------|
| `NoBrokersAvailable` | Pastikan Kafka container running: `docker ps` |
| IPv6 connection timeout | Sudah difix — semua config menggunakan `127.0.0.1` |
| `Rate limit tercapai` | Tambahkan GitHub Token di file `.env` |
| HDFS upload gagal | Pastikan Hadoop containers running dan HDFS dirs sudah dibuat |
| `No module named 'kafka'` | `pip install kafka-python` |
| `No module named 'feedparser'` | `pip install feedparser` |
| Consumer tidak menerima data | Pastikan producer sudah mengirim data terlebih dahulu |

---

## 📂 Struktur Project

```
kelompok-3-ets-bigdata/
├── docker-compose-kafka.yml      # Kafka + Zookeeper
├── docker-compose-hadoop.yml     # Hadoop cluster (5 container)
├── hadoop.env                    # Konfigurasi Hadoop
├── .env                          # GitHub Token (tidak di-commit)
├── .gitignore
├── README.md
│
├── kafka/
│   ├── producer_api.py           # GitHub API → Kafka
│   ├── producer_rss.py           # RSS Feed → Kafka
│   └── consumer_to_hdfs.py       # Kafka → HDFS + file lokal
│
├── spark/
│   └── analysis.ipynb            # PySpark analysis
│
└── dashboard/
    ├── app.py                    # Flask server
    ├── templates/
    │   └── index.html
    ├── static/
    │   └── style.css
    └── data/                     # (auto-generated, gitignored)
        ├── live_api.json
        ├── live_rss.json
        └── spark_results.json
```

---

## 👥 Pembagian Tugas

| Anggota | Peran | File |
|---------|-------|------|
| 1 | Project Lead & Integrator | `docker-compose-*.yml`, `hadoop.env`, `README.md` |
| 2 | Kafka Producer (API) | `kafka/producer_api.py` |
| 3 | Kafka Producer (RSS) + Consumer | `kafka/producer_rss.py`, `kafka/consumer_to_hdfs.py` |
| 4 | Spark Analysis | `spark/analysis.ipynb` |
| 5 | Flask Dashboard | `dashboard/app.py`, `dashboard/templates/index.html` |

---

## ⏹️ Menghentikan Semua Services

```bash
# Stop producer/consumer: Ctrl+C di masing-masing terminal

# Stop Kafka
docker-compose -f docker-compose-kafka.yml down

# Stop Hadoop
docker-compose -f docker-compose-hadoop.yml down

# Stop semua + hapus volumes (reset data)
docker-compose -f docker-compose-kafka.yml down -v
docker-compose -f docker-compose-hadoop.yml down -v
```
