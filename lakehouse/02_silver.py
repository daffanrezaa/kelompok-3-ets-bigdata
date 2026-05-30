"""
02_silver.py — Silver Layer: Cleaning & Transformasi
=====================================================
Membaca dari Bronze Delta, menerapkan 5 transformasi untuk API
dan 3 transformasi untuk RSS, lalu menyimpan ke Silver Delta.
Termasuk demo Schema Evolution (Bonus +2).

Jalankan: python lakehouse/02_silver.py
"""

import os
import sys

# === FIX WINDOWS ===
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# === PATH CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAKEHOUSE_DATA = os.path.join(BASE_DIR, "lakehouse_data")

BRONZE_API = os.path.join(LAKEHOUSE_DATA, "bronze", "github_api")
BRONZE_RSS = os.path.join(LAKEHOUSE_DATA, "bronze", "github_rss")
SILVER_API = os.path.join(LAKEHOUSE_DATA, "silver", "github_api")
SILVER_RSS = os.path.join(LAKEHOUSE_DATA, "silver", "github_rss")

# === SPARK SESSION ===
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_timestamp, hour, trim, when, length, lit, coalesce
)
from pyspark.sql.types import TimestampType

print("=" * 60)
print("  🥈 SILVER LAYER — Cleaning & Transformasi")
print("=" * 60)

try:
    from delta import configure_spark_with_delta_pip
    builder = SparkSession.builder \
        .appName("Silver-GitTrend") \
        .master("local[*]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1")
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
except ImportError:
    spark = SparkSession.builder \
        .appName("Silver-GitTrend") \
        .master("local[*]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# ════════════════════════════════════════════════════════════════
#  HELPER: Print statistik per transformasi
# ════════════════════════════════════════════════════════════════
def print_transform(name, before, after):
    diff = before - after
    pct = (diff / before * 100) if before > 0 else 0
    symbol = "🔻" if diff > 0 else "✅"
    print(f"   {symbol} {name}: {before} → {after} ({diff:+d} baris, {pct:.1f}% dihapus)")

# ════════════════════════════════════════════════════════════════
#  SILVER API — 5 Transformasi
# ════════════════════════════════════════════════════════════════
print("\n📂 Membaca Bronze API...")
bronze_api = spark.read.format("delta").load(BRONZE_API)
initial_count = bronze_api.count()
print(f"   📦 Bronze API: {initial_count} records")

silver_api = bronze_api

# --- Transformasi 1: Drop Duplikat ---
# Menggunakan ingested_at (original dari producer, TANPA underscore)
# agar observasi berbeda waktu untuk repo yang sama tetap dipertahankan
# (dibutuhkan untuk star_velocity di Gold layer)
count_before = silver_api.count()
silver_api = silver_api.dropDuplicates(["full_name", "ingested_at"])
print_transform("T1 — Drop duplikat (full_name + ingested_at)", count_before, silver_api.count())

# --- Transformasi 2: Parse Timestamps ---
# ingested_at: "2026-05-05T23:46:36.518914" → TimestampType
# created_at:  "2026-05-05T03:09:57Z"       → TimestampType
# pushed_at:   "2026-05-05T03:24:48Z"       → TimestampType
count_before = silver_api.count()
silver_api = silver_api \
    .withColumn("ingested_at", to_timestamp(col("ingested_at"))) \
    .withColumn("created_at", to_timestamp(col("created_at"))) \
    .withColumn("pushed_at", to_timestamp(col("pushed_at")))
print_transform("T2 — Parse timestamps (ingested_at, created_at, pushed_at)", count_before, silver_api.count())

# --- Transformasi 3: Handle Null ---
# language null/empty → 'Unknown'
# Filter baris tanpa full_name (tidak berguna tanpa identifier)
count_before = silver_api.count()
silver_api = silver_api \
    .withColumn("language",
        when(
            col("language").isNull() | (trim(col("language")) == ""),
            lit("Unknown")
        ).otherwise(col("language"))
    ) \
    .filter(col("full_name").isNotNull())
print_transform("T3 — Handle null (language → 'Unknown', filter full_name null)", count_before, silver_api.count())

# --- Transformasi 4: Ekstrak Jam ---
# Menggunakan ingested_at (producer timestamp, sudah di-parse di T2)
# untuk analisis temporal di Gold (emerging_topics)
count_before = silver_api.count()
silver_api = silver_api.withColumn("_hour", hour(col("ingested_at")))
print_transform("T4 — Ekstrak jam (_hour dari ingested_at)", count_before, silver_api.count())

# --- Transformasi 5: Standarisasi ---
# Trim whitespace dari full_name dan description
count_before = silver_api.count()
silver_api = silver_api \
    .withColumn("full_name", trim(col("full_name"))) \
    .withColumn("description", trim(coalesce(col("description"), lit(""))))
print_transform("T5 — Standarisasi (trim full_name, description)", count_before, silver_api.count())

final_api_count = silver_api.count()
print(f"\n   📊 API Total: {initial_count} → {final_api_count} "
      f"({initial_count - final_api_count} baris dihapus)")

# ════════════════════════════════════════════════════════════════
#  SILVER RSS — 3 Transformasi
# ════════════════════════════════════════════════════════════════
print("\n📂 Membaca Bronze RSS...")
bronze_rss = spark.read.format("delta").load(BRONZE_RSS)
initial_rss = bronze_rss.count()
print(f"   📦 Bronze RSS: {initial_rss} records")

silver_rss = bronze_rss

# --- Transformasi 1: Drop Duplikat ---
# Setiap artikel RSS memiliki link unik
count_before = silver_rss.count()
silver_rss = silver_rss.dropDuplicates(["link"])
print_transform("T1 — Drop duplikat (link)", count_before, silver_rss.count())

# --- Transformasi 2: Parse Timestamps ---
# ingested_at: ISO format → TimestampType
# published: RFC 2822 "Tue, 05 May 2026 15:20:24 +0000" → TimestampType
#   Menggunakan UDF karena format RFC 2822 sulit di-handle oleh to_timestamp
from pyspark.sql.functions import udf

@udf(TimestampType())
def parse_rfc2822(date_str):
    """Parse RFC 2822 date string ke Python datetime (robust)."""
    if not date_str:
        return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception:
        return None

count_before = silver_rss.count()
silver_rss = silver_rss \
    .withColumn("ingested_at", to_timestamp(col("ingested_at"))) \
    .withColumn("published", parse_rfc2822(col("published")))
print_transform("T2 — Parse timestamps (ingested_at, published RFC2822)", count_before, silver_rss.count())

# --- Transformasi 3: Handle Null ---
# Filter artikel tanpa title atau link (tidak berguna)
count_before = silver_rss.count()
silver_rss = silver_rss.filter(
    col("title").isNotNull() & col("link").isNotNull()
)
print_transform("T3 — Handle null (filter title/link null)", count_before, silver_rss.count())

final_rss_count = silver_rss.count()
print(f"\n   📊 RSS Total: {initial_rss} → {final_rss_count} "
      f"({initial_rss - final_rss_count} baris dihapus)")

# ════════════════════════════════════════════════════════════════
#  SIMPAN KE SILVER DELTA + SCHEMA EVOLUTION (Bonus +2)
# ════════════════════════════════════════════════════════════════
print("\n💾 Menyimpan ke Silver Delta...")

# --- Silver RSS: tulis langsung (tidak perlu schema evolution) ---
silver_rss.write.format("delta").mode("overwrite").save(SILVER_RSS)
print(f"   ✅ Silver RSS disimpan: {SILVER_RSS}")

# --- Silver API: Schema Evolution dengan dua batch ---
print("\n🧬 Demo Schema Evolution (Bonus +2)...")

# Langkah 1: Bagi data menjadi 2 batch berdasarkan ingested_at
# Batch 1 = data polling pertama, Batch 2 = data polling kedua
# Ini memastikan TIDAK ADA duplikat antara batch
from pyspark.sql.functions import min as spark_min, max as spark_max

time_stats = silver_api.agg(
    spark_min("ingested_at").alias("min_t"),
    spark_max("ingested_at").alias("max_t")
).collect()[0]

min_t = time_stats["min_t"]
max_t = time_stats["max_t"]

if min_t and max_t and min_t != max_t:
    # Data multi-batch: split berdasarkan median waktu
    from datetime import timedelta
    midpoint = min_t + (max_t - min_t) / 2
    batch1 = silver_api.filter(col("ingested_at") < lit(midpoint))
    batch2 = silver_api.filter(col("ingested_at") >= lit(midpoint))
    print(f"   📦 Batch 1 (sebelum {midpoint}): {batch1.count()} records")
    print(f"   📦 Batch 2 (sesudah {midpoint}): {batch2.count()} records")
else:
    # Data single-batch: split 70/30 berdasarkan urutan
    total = silver_api.count()
    split_n = int(total * 0.7)
    # Gunakan monotonically_increasing_id untuk split deterministik
    from pyspark.sql.functions import monotonically_increasing_id
    with_id = silver_api.withColumn("_row_id", monotonically_increasing_id())
    batch1 = with_id.limit(split_n).drop("_row_id")
    batch2 = with_id.subtract(with_id.limit(split_n)).drop("_row_id")
    print(f"   📦 Batch 1 (70%): {batch1.count()} records")
    print(f"   📦 Batch 2 (30%): {batch2.count()} records")

# Langkah 2: Tulis batch1 TANPA kolom tambahan → versi 0
batch1.write.format("delta").mode("overwrite").save(SILVER_API)
print(f"   ✅ Batch 1 ditulis (v0, tanpa _desc_length)")

# Print schema versi 0
print("\n   📋 Schema Silver API v0:")
v0 = spark.read.format("delta").load(SILVER_API)
v0_cols = v0.columns
print(f"      Kolom: {v0_cols}")

# Langkah 3: Tambah kolom baru _desc_length ke batch2 saja
batch2_evolved = batch2.withColumn("_desc_length", length(col("description")))

# Langkah 4: Append batch2 dengan mergeSchema
batch2_evolved.write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save(SILVER_API)
print(f"   ✅ Batch 2 ditulis dengan mergeSchema (v1, dengan _desc_length)")

# Print schema versi 1
print("\n   📋 Schema Silver API v1 (setelah Schema Evolution):")
v1 = spark.read.format("delta").load(SILVER_API)
v1_cols = v1.columns
new_cols = [c for c in v1_cols if c not in v0_cols]
print(f"      Kolom: {v1_cols}")
print(f"      🆕 Kolom baru: {new_cols}")

# ════════════════════════════════════════════════════════════════
#  VERIFIKASI
# ════════════════════════════════════════════════════════════════
print(f"\n{'=' * 60}")
print(f"  ✅ SILVER LAYER SELESAI")
print(f"{'=' * 60}")

verify_api = spark.read.format("delta").load(SILVER_API)
verify_rss = spark.read.format("delta").load(SILVER_RSS)

print(f"  📦 Silver API : {verify_api.count()} records")
print(f"  📦 Silver RSS : {verify_rss.count()} records")
print(f"  🧬 Schema Evolution: kolom _desc_length ditambahkan via mergeSchema")
print(f"  📁 Output     : {LAKEHOUSE_DATA}/silver/")
print(f"{'=' * 60}")

print("\n📋 Sample Silver API (5 baris):")
verify_api.select(
    "full_name", "language", "stargazers_count",
    "ingested_at", "_hour", "_desc_length"
).show(5, truncate=30)

print("📋 Sample Silver RSS (5 baris):")
verify_rss.select("title", "author", "published", "ingested_at").show(5, truncate=40)

spark.stop()
print("\n🏁 Spark session ditutup. Silver layer selesai!")
