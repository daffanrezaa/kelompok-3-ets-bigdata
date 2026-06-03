# 🛠️ Setup: Spark + Delta Lake untuk Lakehouse

## Prerequisites

| Software | Versi | Cek |
|----------|-------|-----|
| Python | **3.9 – 3.11** (bukan 3.12+) | `python --version` |
| Java | 8 atau 11 | `java -version` |
| PySpark | 3.5.x | `pip show pyspark` |
| winutils.exe | Hadoop 3.3.x (**wajib di Windows**) | `winutils.exe ls` |

## Instalasi

```bash
# Install PySpark dan Delta Lake
pip install pyspark==3.5.3 delta-spark==3.1.0
```

> ⚠️ **Python harus 3.9–3.11.** PySpark 3.5.3 belum kompatibel dengan Python 3.12+/3.14.
> UDF di `02_silver.py` (cloudpickle) akan gagal `RecursionError: Stack overflow`.
> Buat venv khusus: `py -3.11 -m venv venv311`.

> 🪟 **Windows WAJIB winutils.exe.** Untuk pipeline Delta, warning `HADOOP_HOME`/`winutils.exe`
> **bukan** sekadar warning — `SparkContext` gagal init (`FileUtil.chmod` butuh winutils).
> Download `winutils.exe` + `hadoop.dll` untuk Hadoop 3.3.x (mis. github.com/cdarlint/winutils
> `hadoop-3.3.6/bin`) ke `C:\hadoop\bin\`, lalu `setx HADOOP_HOME "C:\hadoop"` dan tambahkan
> `C:\hadoop\bin` ke `PATH`. Salin juga `hadoop.dll` ke `C:\Windows\System32\`.
> (Hanya analisis ETS `run_analysis.py` yang aman mengabaikan warning ini.)

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
