"""
01_bronze.py — Bronze Layer: Ingest Raw Data ke Delta Lake
==========================================================
Membaca data GitHub API dan RSS dari HDFS (atau fallback ke JSON lokal),
menambahkan metadata _ingested_at dan _source, lalu menyimpan ke Delta format.

Jalankan: python lakehouse/01_bronze.py
"""

import os
import sys

# === FIX WINDOWS: PySpark Python executable ===
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# === PATH CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))         # lakehouse/
PROJECT_DIR = os.path.dirname(BASE_DIR)                       # kelompok-3-ets-bigdata/
LAKEHOUSE_DATA = os.path.join(BASE_DIR, "lakehouse_data")

# Output paths (Delta)
BRONZE_API = os.path.join(LAKEHOUSE_DATA, "bronze", "github_api")
BRONZE_RSS = os.path.join(LAKEHOUSE_DATA, "bronze", "github_rss")

# Input paths — lokal fallback
LOCAL_API = os.path.join(PROJECT_DIR, "dashboard", "data", "live_api.json")
LOCAL_RSS = os.path.join(PROJECT_DIR, "dashboard", "data", "live_rss.json")

# Input paths — HDFS
HDFS_API = "hdfs://namenode:8020/data/github/api/"
HDFS_RSS = "hdfs://namenode:8020/data/github/rss/"

# === SPARK SESSION DENGAN DELTA LAKE ===
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit

print("=" * 60)
print("  🥉 BRONZE LAYER — Ingest Raw Data ke Delta Lake")
print("=" * 60)

try:
    from delta import configure_spark_with_delta_pip
    print("\n✅ delta-spark ditemukan, menggunakan configure_spark_with_delta_pip")
    builder = SparkSession.builder \
        .appName("Bronze-GitTrend") \
        .master("local[*]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
except ImportError:
    print("\n⚠️  delta-spark tidak ditemukan, menggunakan spark.jars.packages")
    spark = SparkSession.builder \
        .appName("Bronze-GitTrend") \
        .master("local[*]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true") \
        .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print(f"   Spark version: {spark.version}")

# ════════════════════════════════════════════════════════════════
#  BACA DATA API
# ════════════════════════════════════════════════════════════════
print("\n📂 [1/4] Membaca data GitHub API...")
df_api = None
api_source = ""

try:
    df_api = spark.read.option("multiLine", True).json(HDFS_API)
    if df_api.count() > 0:
        api_source = f"HDFS ({HDFS_API})"
        print(f"   ✅ Berhasil baca dari HDFS: {df_api.count()} records")
    else:
        raise Exception("HDFS kosong")
except Exception as e:
    print(f"   ⚠️  HDFS gagal ({e}), mencoba file lokal...")
    df_api = spark.read.option("multiLine", True).json(LOCAL_API)
    api_source = f"Lokal ({LOCAL_API})"
    print(f"   ✅ Berhasil baca dari lokal: {df_api.count()} records")

# ════════════════════════════════════════════════════════════════
#  BACA DATA RSS
# ════════════════════════════════════════════════════════════════
print("\n📂 [2/4] Membaca data RSS...")
df_rss = None
rss_source = ""

try:
    df_rss = spark.read.option("multiLine", True).json(HDFS_RSS)
    if df_rss.count() > 0:
        rss_source = f"HDFS ({HDFS_RSS})"
        print(f"   ✅ Berhasil baca dari HDFS: {df_rss.count()} records")
    else:
        raise Exception("HDFS kosong")
except Exception as e:
    print(f"   ⚠️  HDFS gagal ({e}), mencoba file lokal...")
    df_rss = spark.read.option("multiLine", True).json(LOCAL_RSS)
    rss_source = f"Lokal ({LOCAL_RSS})"
    print(f"   ✅ Berhasil baca dari lokal: {df_rss.count()} records")

# ════════════════════════════════════════════════════════════════
#  TAMBAH METADATA & SIMPAN KE BRONZE DELTA
# ════════════════════════════════════════════════════════════════
print("\n💾 [3/4] Menambahkan metadata dan menyimpan ke Bronze Delta...")

# Tambahkan kolom metadata Bronze
bronze_api = df_api \
    .withColumn("_ingested_at", current_timestamp()) \
    .withColumn("_source", lit("api"))

bronze_rss = df_rss \
    .withColumn("_ingested_at", current_timestamp()) \
    .withColumn("_source", lit("rss"))

# Simpan ke Delta format
bronze_api.write.format("delta").mode("overwrite").save(BRONZE_API)
print(f"   ✅ Bronze API disimpan: {BRONZE_API}")

bronze_rss.write.format("delta").mode("overwrite").save(BRONZE_RSS)
print(f"   ✅ Bronze RSS disimpan: {BRONZE_RSS}")

# ════════════════════════════════════════════════════════════════
#  VERIFIKASI & STATISTIK
# ════════════════════════════════════════════════════════════════
print("\n📊 [4/4] Verifikasi Bronze Layer...")

# Baca kembali dari Delta untuk verifikasi
verify_api = spark.read.format("delta").load(BRONZE_API)
verify_rss = spark.read.format("delta").load(BRONZE_RSS)

api_count = verify_api.count()
rss_count = verify_rss.count()

print(f"\n{'=' * 60}")
print(f"  ✅ BRONZE LAYER SELESAI")
print(f"{'=' * 60}")
print(f"  📦 Bronze API : {api_count} records (sumber: {api_source})")
print(f"  📦 Bronze RSS : {rss_count} records (sumber: {rss_source})")
print(f"  📁 Output     : {LAKEHOUSE_DATA}/bronze/")
print(f"{'=' * 60}")

print("\n📋 Schema Bronze API:")
verify_api.printSchema()
print("📋 Sample Bronze API (5 baris):")
verify_api.select("full_name", "language", "stargazers_count", "ingested_at", "_ingested_at", "_source").show(5, truncate=40)

print("📋 Schema Bronze RSS:")
verify_rss.printSchema()
print("📋 Sample Bronze RSS (5 baris):")
verify_rss.select("title", "author", "ingested_at", "_ingested_at", "_source").show(5, truncate=40)

spark.stop()
print("\n🏁 Spark session ditutup. Bronze layer selesai!")
