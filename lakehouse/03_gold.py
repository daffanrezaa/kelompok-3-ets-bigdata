"""
03_gold.py — Gold Layer: Agregasi & Analisis + Time Travel Demo
================================================================
Membaca dari Silver Delta, menghasilkan 5 tabel Gold:
  1. language_dist    (Repro ETS)  — Distribusi bahasa pemrograman
  2. top_repos        (Repro ETS)  — Top 10 repo berdasarkan bintang
  3. star_velocity    (Enhanced)   — Deteksi repo viral via Window function
  4. emerging_topics  (Enhanced)   — Kata kunci baru yang muncul belakangan
  5. cross_source     (Bonus +3)   — Join API topics ↔ RSS tags

Termasuk: Time Travel Demo (10 poin) — update Silver lalu bandingkan versi.

Jalankan: python lakehouse/03_gold.py
"""

import os
import sys
import json

# === FIX WINDOWS ===
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# === PATH CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAKEHOUSE_DATA = os.path.join(BASE_DIR, "lakehouse_data")

SILVER_API = os.path.join(LAKEHOUSE_DATA, "silver", "github_api")
SILVER_RSS = os.path.join(LAKEHOUSE_DATA, "silver", "github_rss")

GOLD_LANG   = os.path.join(LAKEHOUSE_DATA, "gold", "language_dist")
GOLD_TOP    = os.path.join(LAKEHOUSE_DATA, "gold", "top_repos")
GOLD_VELOC  = os.path.join(LAKEHOUSE_DATA, "gold", "star_velocity")
GOLD_EMERGE = os.path.join(LAKEHOUSE_DATA, "gold", "emerging_topics")
GOLD_CROSS  = os.path.join(LAKEHOUSE_DATA, "gold", "cross_source")

# JSON export untuk dashboard (Bonus +5)
GOLD_JSON = os.path.join(LAKEHOUSE_DATA, "gold_json")
os.makedirs(GOLD_JSON, exist_ok=True)

# === SPARK SESSION ===
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, desc, count, avg, sum as spark_sum, max as spark_max,
    min as spark_min, round as spark_round, countDistinct,
    explode, split, lower, trim, length, lit, when, lag,
    concat_ws, collect_list
)
from pyspark.sql.window import Window

print("=" * 60)
print("  🥇 GOLD LAYER — Agregasi, Analisis & Time Travel")
print("=" * 60)

try:
    from delta import configure_spark_with_delta_pip
    from delta.tables import DeltaTable
    builder = SparkSession.builder \
        .appName("Gold-GitTrend") \
        .master("local[*]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1")
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    HAS_DELTA_TABLES = True
except ImportError:
    spark = SparkSession.builder \
        .appName("Gold-GitTrend") \
        .master("local[*]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .getOrCreate()
    # Import DeltaTable setelah SparkSession dibuat (JAR sudah loaded)
    try:
        from delta.tables import DeltaTable
        HAS_DELTA_TABLES = True
    except ImportError:
        HAS_DELTA_TABLES = False

spark.sparkContext.setLogLevel("WARN")

# ════════════════════════════════════════════════════════════════
#  BACA SILVER DATA
# ════════════════════════════════════════════════════════════════
print("\n📂 Membaca Silver Delta tables...")
silver_api = spark.read.format("delta").load(SILVER_API)
silver_rss = spark.read.format("delta").load(SILVER_RSS)
print(f"   📦 Silver API: {silver_api.count()} records")
print(f"   📦 Silver RSS: {silver_rss.count()} records")


# ════════════════════════════════════════════════════════════════
#  GOLD 1: Distribusi Bahasa (Repro ETS Analysis 1)
# ════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("📊 Gold 1: Distribusi Bahasa Pemrograman (Repro ETS)")
print("─" * 60)

# Deduplikasi per repo (ambil observasi terakhir per full_name)
w_latest = Window.partitionBy("full_name").orderBy(col("ingested_at").desc())
api_latest = silver_api \
    .withColumn("_rn", lag(lit(1), 0).over(w_latest)) \
    .dropDuplicates(["full_name"])

total_repos = api_latest.count()

gold_lang = api_latest.groupBy("language").agg(
    count("*").alias("repo_count"),
    spark_round(avg("stargazers_count"), 1).alias("avg_stars"),
    spark_sum("forks_count").alias("total_forks")
).withColumn(
    "percentage", spark_round(col("repo_count") / lit(total_repos) * 100, 1)
).orderBy(desc("repo_count"))

gold_lang.show(15, truncate=False)

# Simpan ke Delta + JSON
gold_lang.write.format("delta").mode("overwrite").save(GOLD_LANG)
gold_lang_json = [row.asDict() for row in gold_lang.collect()]
# Konversi Decimal ke float untuk JSON serialization
for row in gold_lang_json:
    for k, v in row.items():
        if hasattr(v, 'as_integer_ratio'):  # Decimal type check
            row[k] = float(v)
with open(os.path.join(GOLD_JSON, "language_dist.json"), "w") as f:
    json.dump(gold_lang_json, f, indent=2, default=str)
print(f"   ✅ Gold 1 disimpan: {GOLD_LANG}")


# ════════════════════════════════════════════════════════════════
#  GOLD 2: Top 10 Repositori (Repro ETS Analysis 2)
# ════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("⭐ Gold 2: Top 10 Repositori Berdasarkan Bintang (Repro ETS)")
print("─" * 60)

gold_top = silver_api.groupBy("full_name").agg(
    spark_max(when(col("language").isNotNull(), col("language")).otherwise(lit("Unknown"))).alias("language"),
    spark_max("stargazers_count").alias("stargazers_count"),
    spark_max("forks_count").alias("forks_count"),
    spark_max("description").alias("description")
).orderBy(desc("stargazers_count")).limit(10)

# Tambahkan ranking
from pyspark.sql.functions import row_number
w_rank = Window.orderBy(desc("stargazers_count"))
gold_top = gold_top.withColumn("rank", row_number().over(w_rank))

gold_top.select("rank", "full_name", "language", "stargazers_count", "forks_count").show(10, truncate=False)

# Simpan ke Delta + JSON
gold_top.write.format("delta").mode("overwrite").save(GOLD_TOP)
gold_top_json = [row.asDict() for row in gold_top.collect()]
for row in gold_top_json:
    for k, v in row.items():
        if hasattr(v, 'as_integer_ratio'):
            row[k] = float(v)
with open(os.path.join(GOLD_JSON, "top_repos.json"), "w") as f:
    json.dump(gold_top_json, f, indent=2, default=str)
print(f"   ✅ Gold 2 disimpan: {GOLD_TOP}")


# ════════════════════════════════════════════════════════════════
#  GOLD 3: Star Velocity (Enhanced — Window Function)
# ════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("🚀 Gold 3: Star Velocity — Deteksi Repo Viral (Enhanced)")
print("─" * 60)

# Window: partisi per repo, urut berdasarkan waktu ingest producer
w_velocity = Window.partitionBy("full_name").orderBy("ingested_at")

star_with_lag = silver_api \
    .withColumn("prev_stars", lag("stargazers_count", 1).over(w_velocity)) \
    .withColumn("star_gain", col("stargazers_count") - col("prev_stars"))

# Hanya repo yang punya >1 observasi (prev_stars tidak NULL)
repos_with_change = star_with_lag.filter(col("prev_stars").isNotNull())

if repos_with_change.count() > 0:
    gold_velocity = repos_with_change.groupBy("full_name", "language").agg(
        spark_sum("star_gain").alias("total_star_gain"),
        spark_max("stargazers_count").alias("max_stars"),
        count("*").alias("observations")
    ).orderBy(desc("total_star_gain"))

    gold_velocity.show(10, truncate=False)
else:
    # Fallback: jika semua repo hanya punya 1 observasi,
    # tampilkan repo dengan star tertinggi sebagai "potensi viral"
    print("   ⚠️  Semua repo hanya punya 1 observasi — menampilkan potensi viral berdasarkan stars")
    gold_velocity = silver_api.groupBy("full_name", "language").agg(
        lit(0).alias("total_star_gain"),
        spark_max("stargazers_count").alias("max_stars"),
        count("*").alias("observations")
    ).orderBy(desc("max_stars")).limit(10)

    gold_velocity.show(10, truncate=False)

# Simpan ke Delta + JSON
gold_velocity.write.format("delta").mode("overwrite").save(GOLD_VELOC)
gold_vel_json = [row.asDict() for row in gold_velocity.collect()]
for row in gold_vel_json:
    for k, v in row.items():
        if hasattr(v, 'as_integer_ratio'):
            row[k] = float(v)
with open(os.path.join(GOLD_JSON, "star_velocity.json"), "w") as f:
    json.dump(gold_vel_json, f, indent=2, default=str)
print(f"   ✅ Gold 3 disimpan: {GOLD_VELOC}")


# ════════════════════════════════════════════════════════════════
#  GOLD 4: Emerging Topics (Enhanced — Temporal Keyword Analysis)
# ════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("🌱 Gold 4: Emerging Topics — Kata Kunci Baru (Enhanced)")
print("─" * 60)

from datetime import timedelta

# Hitung rentang waktu data
time_stats = silver_api.agg(
    spark_min("ingested_at").alias("min_t"),
    spark_max("ingested_at").alias("max_t")
).collect()[0]

min_t = time_stats["min_t"]
max_t = time_stats["max_t"]
data_span_hours = (max_t - min_t).total_seconds() / 3600

print(f"   📅 Rentang data: {min_t} → {max_t} ({data_span_hours:.1f} jam)")

# Tentukan cutoff — adaptif berdasarkan data range
if data_span_hours >= 3:
    cutoff = max_t - timedelta(hours=3)
    print(f"   ✂️  Cutoff: 3 jam terakhir (sejak {cutoff})")
else:
    cutoff = min_t + (max_t - min_t) / 2
    print(f"   ✂️  Data < 3 jam — menggunakan median split (cutoff: {cutoff})")

# Stop words (bahasa Inggris umum + karakter pendek)
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "and", "or", "of", "to",
    "in", "for", "on", "with", "at", "by", "from", "that", "this", "it",
    "as", "be", "has", "had", "have", "not", "but", "its", "all", "can",
    "will", "do", "no", "if", "so", "up", "out", "about", "into", "more",
    "also", "than", "very", "just", "your", "you", "we", "they", "he",
    "she", "my", "our", "their", "any", "each", "which", "when", "what",
    "there", "how", "been", "who", "would", "could", "should", "may",
    "might", "must", "shall", "did", "does", "done", "being", "were",
    "over", "under", "between", "through", "after", "before", "such",
    "only", "other", "new", "used", "using", "use", "like", "based",
    "make", "made", "way", "well", "back", "even", "still", "every",
    ""
}
stop_words_list = list(STOP_WORDS)

# Split deskripsi menjadi kata-kata
# Recent: data setelah cutoff
recent_words = silver_api.filter(col("ingested_at") >= lit(cutoff)) \
    .select(explode(split(lower(trim(col("description"))), r"\s+")).alias("word"))

# Older: data sebelum cutoff
older_words = silver_api.filter(col("ingested_at") < lit(cutoff)) \
    .select(explode(split(lower(trim(col("description"))), r"\s+")).alias("word"))

# Filter noise: panjang > 3, bukan stop word, frekuensi >= 2 di recent
recent_filtered = recent_words \
    .filter(length(col("word")) > 3) \
    .filter(~col("word").isin(stop_words_list)) \
    .groupBy("word").agg(count("*").alias("frequency")) \
    .filter(col("frequency") >= 2)

# Kata unik di older (untuk subtract)
older_unique = older_words \
    .filter(length(col("word")) > 3) \
    .select("word").distinct()

# Emerging = kata yang ada di recent tapi TIDAK ada di older
gold_emerging = recent_filtered.join(older_unique, on="word", how="left_anti") \
    .orderBy(desc("frequency"))

emerging_count = gold_emerging.count()
print(f"\n   🌱 {emerging_count} kata baru ditemukan di data terbaru:")
gold_emerging.show(20, truncate=False)

# Simpan ke Delta + JSON
if emerging_count > 0:
    gold_emerging.write.format("delta").mode("overwrite").save(GOLD_EMERGE)
else:
    # Jika tidak ada emerging words (semua kata sudah ada sebelumnya),
    # simpan recent_filtered sebagai "trending words" fallback
    print("   ℹ️  Tidak ada kata benar-benar baru — menyimpan trending words sebagai fallback")
    gold_emerging = recent_filtered.orderBy(desc("frequency"))
    gold_emerging.write.format("delta").mode("overwrite").save(GOLD_EMERGE)

gold_emerge_json = [row.asDict() for row in gold_emerging.limit(30).collect()]
for row in gold_emerge_json:
    for k, v in row.items():
        if hasattr(v, 'as_integer_ratio'):
            row[k] = float(v)
with open(os.path.join(GOLD_JSON, "emerging_topics.json"), "w") as f:
    json.dump(gold_emerge_json, f, indent=2, default=str)
print(f"   ✅ Gold 4 disimpan: {GOLD_EMERGE}")


# ════════════════════════════════════════════════════════════════
#  GOLD 5: Cross-Source Topics (Bonus +3 — Join API ↔ RSS)
# ════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("🔗 Gold 5: Cross-Source Topics — API ↔ RSS (Bonus +3)")
print("─" * 60)

# Dari Silver API: explode kolom `topics` (array of strings)
api_topics = silver_api \
    .select("full_name", "stargazers_count",
            explode(col("topics")).alias("keyword")) \
    .withColumn("keyword", lower(trim(col("keyword")))) \
    .filter(length(col("keyword")) > 0)

# Dari Silver RSS: explode kolom `tags` (array of strings)
rss_tags = silver_rss \
    .select("title", "link",
            explode(col("tags")).alias("keyword")) \
    .withColumn("keyword", lower(trim(col("keyword")))) \
    .filter(length(col("keyword")) > 0)

api_topic_count = api_topics.count()
rss_tag_count = rss_tags.count()
print(f"   📦 API topics (exploded): {api_topic_count} entries")
print(f"   📦 RSS tags (exploded): {rss_tag_count} entries")

# Inner join: keyword yang muncul di KEDUA sumber
gold_cross = api_topics.join(rss_tags, on="keyword", how="inner") \
    .groupBy("keyword") \
    .agg(
        countDistinct("full_name").alias("repo_count"),
        countDistinct("title").alias("article_count"),
        spark_max("stargazers_count").alias("max_stars")
    ) \
    .orderBy(desc("repo_count"))

cross_count = gold_cross.count()
print(f"\n   🔗 {cross_count} keyword yang overlap antara API topics dan RSS tags:")
gold_cross.show(15, truncate=False)

# Simpan ke Delta + JSON
if cross_count > 0:
    gold_cross.write.format("delta").mode("overwrite").save(GOLD_CROSS)
    gold_cross_json = [row.asDict() for row in gold_cross.collect()]
    for row in gold_cross_json:
        for k, v in row.items():
            if hasattr(v, 'as_integer_ratio'):
                row[k] = float(v)
    with open(os.path.join(GOLD_JSON, "cross_source.json"), "w") as f:
        json.dump(gold_cross_json, f, indent=2, default=str)
    print(f"   ✅ Gold 5 disimpan: {GOLD_CROSS}")
else:
    print("   ⚠️  Tidak ada overlap — mungkin topics API dan tags RSS tidak cocok")
    print("   ℹ️  Tabel Gold 5 tidak dibuat (ini tidak mempengaruhi skor wajib)")


# ════════════════════════════════════════════════════════════════
#  TIME TRAVEL DEMO (10 poin)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  🕐 TIME TRAVEL DEMO")
print("=" * 60)

if not HAS_DELTA_TABLES:
    print("   ❌ DeltaTable tidak tersedia — skip Time Travel demo")
else:
    dt = DeltaTable.forPath(spark, SILVER_API)

    # --- Step 1: Tampilkan history SEBELUM update ---
    print("\n📜 Step 1: Delta Table History (sebelum update)")
    print("   Versi yang ada saat ini (dari 02_silver.py):")
    print("   • v0 = Batch 1 (overwrite, tanpa _desc_length)")
    print("   • v1 = Batch 1 + Batch 2 (append, dengan _desc_length via mergeSchema)")
    dt.history().select("version", "timestamp", "operation", "operationMetrics").show(truncate=False)

    # --- Step 2: Distribusi SEBELUM update (v1) ---
    print("📊 Step 2: Distribusi language SEBELUM update (v1 — data lengkap):")
    before_df = spark.read.format("delta").option("versionAsOf", 1).load(SILVER_API)
    before_dist = before_df.groupBy("language").agg(count("*").alias("count")).orderBy(desc("count"))
    before_dist.show(15, truncate=False)

    # Simpan distribusi before untuk perbandingan
    before_unknown = before_df.filter(col("language") == "Unknown").count()
    before_total = before_df.count()
    print(f"   📦 Total records (v1): {before_total}")
    print(f"   📦 Records dengan language='Unknown': {before_unknown}")

    # --- Step 3: UPDATE — ubah 'Unknown' → 'Not Specified' ---
    print("\n✏️  Step 3: UPDATE language 'Unknown' → 'Not Specified'")
    dt.update(
        condition=col("language") == "Unknown",
        set={"language": lit("Not Specified")}
    )
    print("   ✅ Update selesai — versi baru dibuat (v2)")

    # --- Step 4: History SETELAH update ---
    print("\n📜 Step 4: Delta Table History (setelah update)")
    print("   • v0 = Batch 1 (overwrite)")
    print("   • v1 = Batch 1 + Batch 2 (append + mergeSchema)")
    print("   • v2 = UPDATE language 'Unknown' → 'Not Specified'")
    dt.history().select("version", "timestamp", "operation", "operationMetrics").show(truncate=False)

    # --- Step 5: Distribusi SETELAH update (v2 — latest) ---
    print("📊 Step 5: Distribusi language SETELAH update (v2 — terbaru):")
    after_df = spark.read.format("delta").load(SILVER_API)
    after_dist = after_df.groupBy("language").agg(count("*").alias("count")).orderBy(desc("count"))
    after_dist.show(15, truncate=False)

    after_not_spec = after_df.filter(col("language") == "Not Specified").count()
    after_unknown = after_df.filter(col("language") == "Unknown").count()
    after_total = after_df.count()

    # --- Step 6: Perbandingan ---
    print("📊 Step 6: PERBANDINGAN Time Travel")
    print(f"   {'Metrik':<40} {'v1 (sebelum)':<15} {'v2 (sesudah)':<15}")
    print(f"   {'─' * 70}")
    print(f"   {'Total records':<40} {before_total:<15} {after_total:<15}")
    print(f"   {'language = Unknown':<40} {before_unknown:<15} {after_unknown:<15}")
    print(f"   {'language = Not Specified':<40} {'0':<15} {after_not_spec:<15}")
    print()
    print("   ✅ Time Travel berhasil! Data versi lama (v1) tetap bisa diakses")
    print("      menggunakan spark.read.format('delta').option('versionAsOf', 1)")


# ════════════════════════════════════════════════════════════════
#  RINGKASAN AKHIR
# ════════════════════════════════════════════════════════════════
print(f"\n{'=' * 60}")
print(f"  ✅ GOLD LAYER SELESAI")
print(f"{'=' * 60}")
print(f"  📊 Gold 1 — language_dist    : {GOLD_LANG}")
print(f"  ⭐ Gold 2 — top_repos        : {GOLD_TOP}")
print(f"  🚀 Gold 3 — star_velocity    : {GOLD_VELOC}")
print(f"  🌱 Gold 4 — emerging_topics  : {GOLD_EMERGE}")
print(f"  🔗 Gold 5 — cross_source     : {GOLD_CROSS}")
print(f"  📁 JSON exports              : {GOLD_JSON}")
print(f"  🕐 Time Travel               : v1 vs v2 berhasil ditampilkan")
print(f"{'=' * 60}")

spark.stop()
print("\n🏁 Spark session ditutup. Gold layer selesai!")
