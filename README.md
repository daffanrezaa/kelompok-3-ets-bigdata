# GitTrend — Monitor Repositori Open Source Populer

Big Data Pipeline end-to-end: **Kafka → HDFS → Spark → Flask Dashboard**

```
GitHub API (60 detik)         TechCrunch RSS (5 menit)
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

## Prasyarat

| Tool             | Versi           |
| ---------------- | --------------- |
| Docker Desktop   | Latest          |
| Python           | 3.9+            |
| Git              | Latest          |

---

## Step 0 — Setup Awal
### 0a. Buat Virtual Environment & Install Dependencies

```bash
# Buat venv
python -m venv venv

# Aktifkan venv
.\\venv\\Scripts\\activate          # Windows PowerShell / CMD
# source venv/bin/activate          # macOS / Linux / Git Bash

# Install semua dependencies
pip install kafka-python feedparser hdfs flask flask-cors requests python-dotenv pyspark
```

---

## Step 1 — Setup GitHub Token (Opsional, Disarankan)

Tanpa token, GitHub API rate limit = 10 request/jam. Dengan token = 30 request/jam.

1. Buka https://github.com/settings/tokens
2. Generate new token (classic) → centang `public_repo`
3. Buat file `.env` di root project:

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

---

## Step 2 — Jalankan Docker Containers

### 2a. Jalankan Kafka + Zookeeper

```bash
docker-compose -f docker-compose-kafka.yml up -d
```

Verifikasi:
```bash
docker ps
# Harus muncul: zookeeper, kafka-broker
```

### 2b. Jalankan Hadoop Cluster

```bash
docker-compose -f docker-compose-hadoop.yml up -d
```

Verifikasi:
```bash
docker ps
# Harus muncul: namenode, datanode, resourcemanager, nodemanager, historyserver
```

Tunggu ~30 detik sampai namenode ready, lalu cek Web UI: http://localhost:9870

### 2c. Buat Direktori HDFS

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

## Step 3 — Jalankan Pipeline (3 Terminal)

Buka **3 terminal terpisah**, aktifkan venv di masing-masing, lalu masuk ke folder `kafka/`:

```bash
.\\venv\\Scripts\\activate    # aktifkan venv di setiap terminal
cd kafka
```

### Terminal 1 — Producer API (GitHub)

```bash
python producer_api.py
```

Output yang diharapkan:
```
GitHub API Producer dimulai
Topic: github-api | Interval: 1 menit
Berhasil fetch 30 repo. Rate limit remaining: 29
Berhasil kirim 30/30 event ke topic 'github-api'
Menunggu 1 menit sebelum polling berikutnya...
```

> **Catatan Demo:** Interval saat ini diset **60 detik** agar data cepat masuk selama demo.

### Terminal 2 — Producer RSS (TechCrunch)

```bash
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

## Step 4 — Verifikasi Data

### 4a. Verifikasi Kafka Topics

```bash
# List semua topic
docker exec -it kafka-broker kafka-topics --list --bootstrap-server localhost:9092

# Baca data dari topic github-api
docker exec -it kafka-broker kafka-console-consumer --topic github-api --from-beginning --bootstrap-server localhost:9092

# Baca data dari topic github-rss
docker exec -it kafka-broker kafka-console-consumer --topic github-rss --from-beginning --bootstrap-server localhost:9092
```

### 4b. Verifikasi Data di HDFS

```bash
# List file di HDFS
docker exec -it namenode hdfs dfs -ls -R /data/github/

# Baca isi salah satu file
docker exec -it namenode hdfs dfs -cat /data/github/api/<nama-file>.json

# Size per folder (api/, rss/, hasil/)
docker exec -it namenode hdfs dfs -du -h /data/github/

# Ringkasan kapasitas cluster (total, used, available)
docker exec -it namenode hdfs dfs -df -h /data/
```

### 4c. Verifikasi File Lokal Dashboard

```bash
# Cek apakah file live data sudah ada
dir dashboard\data\
# Harus ada: live_api.json, live_rss.json
```

---

## Step 5 — Spark Analysis

### Opsi A: Notebook PySpark (dengan HDFS)

Buka `spark/analysis.ipynb` di Jupyter Notebook atau Google Colab:

```bash
jupyter notebook spark/analysis.ipynb
```

- Membaca data dari HDFS
- 3 analisis wajib: distribusi bahasa, top 10 repo, kata trending
- Output: `dashboard/data/spark_results.json`

### Opsi B: Runner PySpark via Script

`run_analysis.py` menjalankan analisis PySpark yang sama, membaca langsung dari HDFS.
Jika PySpark gagal (misal di Windows), otomatis fallback ke plain Python.

```bash
# Jalankan sekali (baca dari HDFS)
python spark/run_analysis.py

# Mode watch — analisis diperbarui otomatis setiap 60 detik
python spark/run_analysis.py --watch 60
```

Output: `dashboard/data/spark_results.json`

### Opsi C: Docker Spark (Alternatif)

Jika ingin menjalankan Spark di dalam Docker container:

```bash
docker compose -f docker-compose-spark.yml up -d
docker exec spark-master spark-submit /opt/spark-apps/spark_analysis.py
```

---

## Step 6 — Flask Dashboard

```bash
cd dashboard
python app.py
```

Buka browser: http://localhost:5000

---

## Troubleshooting

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

## Struktur Project

```
kelompok-3-ets-bigdata/
├── docker-compose-kafka.yml      # Kafka + Zookeeper
├── docker-compose-hadoop.yml     # Hadoop cluster (5 container)
├── docker-compose-spark.yml      # Spark master + worker (alternatif)
├── hadoop.env                    # Konfigurasi Hadoop
├── run.sh                        # Start semua services (Linux/Mac)
├── stop.sh                       # Stop semua services (Linux/Mac)
├── .env                          # GitHub Token (tidak di-commit)
├── .gitignore
├── README.md
│
├── kafka/
│   ├── producer_api.py           # GitHub API → Kafka (interval: 60 detik)
│   ├── producer_rss.py           # RSS Feed → Kafka (interval: 5 menit)
│   └── consumer_to_hdfs.py       # Kafka → HDFS + file lokal
│
├── spark/
│   ├── analysis.ipynb            # PySpark analysis notebook (HDFS)
│   ├── run_analysis.py           # PySpark runner (HDFS, dengan fallback)
│   └── spark_analysis.py         # PySpark untuk Docker Spark (alternatif)
│
├── dashboard/
│   ├── app.py                    # Flask server
│   ├── templates/
│   │   └── index.html
│   ├── static/
│   │   └── style.css
│   └── data/                     # (auto-generated, gitignored)
│       ├── live_api.json
│       ├── live_rss.json
│       └── spark_results.json
```

---

## Pembagian Tugas

| Anggota | Peran | File |
|---------|-------|------|
| 1 | Project Lead & Integrator | `docker-compose-*.yml`, `hadoop.env`, `README.md` |
| 2 | Kafka Producer (API) | `kafka/producer_api.py` |
| 3 | Kafka Producer (RSS) + Consumer | `kafka/producer_rss.py`, `kafka/consumer_to_hdfs.py` |
| 4 | Spark Analysis | `spark/analysis.ipynb`, `spark/run_analysis.py`, `spark/spark_analysis.py` |
| 5 | Flask Dashboard | `dashboard/app.py`, `dashboard/templates/index.html` |

---

## Menghentikan Semua Services

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
