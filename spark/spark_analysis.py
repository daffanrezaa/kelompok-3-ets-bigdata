"""
GitTrend — Spark Analysis (Docker Version)
============================================
Script ini dijalankan di dalam Docker container Spark,
sehingga bisa akses HDFS langsung via hdfs://namenode:8020.

Cara menjalankan:
  docker exec spark-master spark-submit /opt/spark-apps/spark_analysis.py

Sesuai ketentuan ETS:
  ✅ Apache Spark (DataFrame API + Spark SQL)
  ✅ Baca dari HDFS (/data/github/api/ dan /data/github/rss/)
  ✅ 3 Analisis Wajib (distribusi bahasa, top 10, kata trending)
  ✅ Simpan hasil ke HDFS (/data/github/hasil/)
  ✅ Simpan spark_results.json ke dashboard/data/
"""

import json
import os
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# ──────────────────────────── CONFIG ────────────────────────────
HDFS_API = "hdfs://namenode:8020/data/github/api/"
HDFS_RSS = "hdfs://namenode:8020/data/github/rss/"
HDFS_HASIL = "hdfs://namenode:8020/data/github/hasil/"
OUTPUT_JSON = "/opt/dashboard-data/spark_results.json"

# ──────────────────────────── SPARK SESSION ─────────────────────
print("=" * 60)
print("🚀 GitTrend Spark Analysis (Docker)")
print("=" * 60)

spark = SparkSession.builder \
    .appName("GitTrend-Analysis") \
    .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:8020") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print(f"   ✅ Spark {spark.version} ready")

# ──────────────────────────── LOAD DATA ─────────────────────────
print(f"\n📂 Membaca dari HDFS...")
print(f"   API: {HDFS_API}")
print(f"   RSS: {HDFS_RSS}")

df_api = spark.read.option("multiLine", True).json(HDFS_API)
df_rss = spark.read.option("multiLine", True).json(HDFS_RSS)

total_api = df_api.count()
total_rss = df_rss.count()
print(f"   ✅ {total_api} API records, {total_rss} RSS records")

if total_api == 0:
    print("❌ Tidak ada data API. Jalankan producer + consumer dulu.")
    spark.stop()
    exit(1)

# Register untuk Spark SQL
df_api.createOrReplaceTempView("repos")
df_rss.createOrReplaceTempView("rss_articles")

# ══════════════════════════════════════════════════════════════
# ANALISIS 1: Distribusi Bahasa Pemrograman (Spark SQL)
# ══════════════════════════════════════════════════════════════
print("\n📊 Analisis 1: Distribusi Bahasa Pemrograman (Spark SQL)...")
df_lang = spark.sql(f"""
    SELECT
        COALESCE(language, 'Unknown') AS language,
        COUNT(*) AS repo_count,
        ROUND(COUNT(*) * 100.0 / {total_api}, 1) AS percentage,
        ROUND(AVG(stargazers_count), 1) AS avg_stars,
        SUM(forks_count) AS total_forks
    FROM repos
    GROUP BY COALESCE(language, 'Unknown')
    ORDER BY repo_count DESC
""")
df_lang.show(20, truncate=False)
lang_results = [row.asDict() for row in df_lang.collect()]
# Convert percentage to string for JSON consistency
for r in lang_results:
    r["percentage"] = str(r["percentage"])
print(f"   ✅ {len(lang_results)} bahasa ditemukan")

# Narasi Analisis 1
top_lang = lang_results[0]["language"] if lang_results else "N/A"
print(f"\n   📝 Interpretasi: Bahasa '{top_lang}' mendominasi repositori trending,")
print(f"      menunjukkan popularitasnya dalam ekosistem open-source GitHub.")

# ══════════════════════════════════════════════════════════════
# ANALISIS 2: Top 10 Repositori (Spark SQL)
# ══════════════════════════════════════════════════════════════
print("\n⭐ Analisis 2: Top 10 Repositori Berdasarkan Bintang (Spark SQL)...")
df_top = spark.sql("""
    SELECT
        full_name,
        COALESCE(language, 'Unknown') AS language,
        stargazers_count,
        forks_count,
        SUBSTRING(COALESCE(description, ''), 1, 80) AS description_short
    FROM repos
    ORDER BY stargazers_count DESC
    LIMIT 10
""")
df_top.show(10, truncate=False)
top10_raw = [row.asDict() for row in df_top.collect()]
top10_results = [{"rank": i + 1, **r} for i, r in enumerate(top10_raw)]
print(f"   ✅ Top {len(top10_results)} repos")

# Narasi Analisis 2
if top10_results:
    top_repo = top10_results[0]
    print(f"\n   📝 Interpretasi: '{top_repo['full_name']}' adalah repo paling populer")
    print(f"      dengan {top_repo['stargazers_count']} stars, menunjukkan minat tinggi komunitas.")

# ══════════════════════════════════════════════════════════════
# ANALISIS 3: Kata Trending di Deskripsi (DataFrame API)
# ══════════════════════════════════════════════════════════════
print("\n🔥 Analisis 3: Kata Trending di Deskripsi Repo (DataFrame API)...")

# Stop words yang difilter
stop_words = ["the", "and", "for", "with", "that", "this", "from", "your",
              "have", "will", "about", "into", "over", "also", "just", "more",
              "than", "then", "used", "using", "http", "https", "www", "com"]

df_words = df_api \
    .filter(F.col("description").isNotNull()) \
    .select(F.explode(
        F.split(
            F.regexp_replace(F.lower(F.col("description")), "[^a-zA-Z\\s]", ""),
            "\\s+"
        )
    ).alias("word")) \
    .filter(F.length("word") >= 4) \
    .filter(~F.col("word").isin(stop_words)) \
    .groupBy("word") \
    .agg(F.count("*").alias("frequency")) \
    .orderBy(F.desc("frequency")) \
    .limit(30)

df_words.show(30, truncate=False)
word_results = [row.asDict() for row in df_words.collect()]
print(f"   ✅ {len(word_results)} trending words")

# Narasi Analisis 3
if word_results:
    top_word = word_results[0]
    print(f"\n   📝 Interpretasi: Kata '{top_word['word']}' (muncul {top_word['frequency']}x)")
    print(f"      menggambarkan tema utama yang sedang trending di GitHub saat ini.")

# ══════════════════════════════════════════════════════════════
# SIMPAN HASIL
# ══════════════════════════════════════════════════════════════
print("\n💾 Menyimpan hasil...")

spark_results = {
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "spark_version": spark.version,
        "total_api_records": total_api,
        "total_rss_records": total_rss,
        "analysis_count": 3,
        "source": "HDFS",
    },
    "analysis_1_language_distribution": lang_results,
    "analysis_2_top_repos": top10_results,
    "analysis_3_trending_words": word_results,
}

# 1. Simpan ke lokal (untuk dashboard)
os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(spark_results, f, indent=2, ensure_ascii=False)
print(f"   ✅ Lokal: {OUTPUT_JSON}")

# 2. Simpan ke HDFS
try:
    # Simpan JSON string sebagai single file di HDFS
    rdd = spark.sparkContext.parallelize([json.dumps(spark_results, ensure_ascii=False)])
    rdd.coalesce(1).saveAsTextFile(HDFS_HASIL + "spark_results_tmp")

    # Pindahkan ke nama file yang benar
    hadoop = spark._jvm.org.apache.hadoop
    fs = hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())
    src_dir = hadoop.fs.Path(HDFS_HASIL + "spark_results_tmp")
    
    # Cari file part-00000
    status = fs.listStatus(src_dir)
    for s in status:
        name = s.getPath().getName()
        if name.startswith("part-"):
            fs.rename(s.getPath(), hadoop.fs.Path(HDFS_HASIL + "spark_results.json"))
            break
    
    # Cleanup temp dir
    fs.delete(src_dir, True)
    print(f"   ✅ HDFS: {HDFS_HASIL}spark_results.json")
except Exception as e:
    print(f"   ⚠️  HDFS save error: {e}")
    # Fallback: simpan via RDD text
    try:
        rdd = spark.sparkContext.parallelize([json.dumps(spark_results)])
        rdd.saveAsTextFile(HDFS_HASIL + "output_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        print(f"   ✅ HDFS fallback: saved")
    except Exception as e2:
        print(f"   ❌ HDFS gagal total: {e2}")

spark.stop()
print("\n🎉 Selesai! Spark analysis complete.")
print("=" * 60)
