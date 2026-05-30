# 🛠️ Setup: Spark + Delta Lake untuk Lakehouse

## Prerequisites

| Software | Versi | Cek |
|----------|-------|-----|
| Python | 3.9+ | `python --version` |
| Java | 8 atau 11 | `java -version` |
| PySpark | 3.5.x | `pip show pyspark` |

## Instalasi

```bash
# Install PySpark dan Delta Lake
pip install pyspark==3.5.3 delta-spark==3.1.0
```

> **Catatan Windows:** Jika muncul warning tentang `HADOOP_HOME` atau `winutils.exe`,
> ini hanya warning dan **tidak mengganggu** pipeline Delta Lake lokal.
> Pipeline ini berjalan di mode `local[*]` (tanpa cluster Hadoop).

## Cara Menjalankan

Jalankan dari **root project** (`kelompok-3-ets-bigdata/`):

```bash
# 1. Bronze: Ingest data → Delta
python lakehouse/01_bronze.py

# 2. Silver: Cleaning + Transformasi
python lakehouse/02_silver.py

# 3. Gold: Agregasi + Time Travel Demo
python lakehouse/03_gold.py
```

Setiap script akan print statistik dan hasil analisis ke terminal.

## Sumber Data

Pipeline mendukung **dua mode**:

| Mode | Sumber | Kapan |
|------|--------|-------|
| **HDFS** | `hdfs://namenode:8020/data/github/api/` dan `rss/` | Docker Hadoop berjalan |
| **Lokal** (fallback) | `dashboard/data/live_api.json` dan `live_rss.json` | HDFS tidak tersedia |

Script akan otomatis mencoba HDFS terlebih dahulu, lalu fallback ke file lokal.

## Output

Semua Delta tables disimpan di:
```
lakehouse/lakehouse_data/
├── bronze/
│   ├── github_api/     ← Raw data API
│   └── github_rss/     ← Raw data RSS
├── silver/
│   ├── github_api/     ← Cleaned API
│   └── github_rss/     ← Cleaned RSS
├── gold/
│   ├── language_dist/  ← Distribusi bahasa
│   ├── top_repos/      ← Top 10 repo
│   ├── star_velocity/  ← Star velocity
│   ├── emerging_topics/← Topik baru
│   └── cross_source/   ← Cross-source join (bonus)
└── gold_json/          ← Export JSON untuk dashboard
```
