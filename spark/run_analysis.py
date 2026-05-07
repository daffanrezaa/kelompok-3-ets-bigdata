"""
GitTrend — Spark Analysis Runner (Komponen 3)
==============================================
Pengganti analysis.ipynb — bisa dijalankan langsung sebagai script Python.

Sesuai ketentuan ETS:
  ✅ Apache Spark (DataFrame API + Spark SQL)
  ✅ Baca dari HDFS (/data/github/api/ dan /data/github/rss/)
  ✅ 3 Analisis Wajib (distribusi bahasa, top 10, kata trending)
  ✅ Simpan hasil ke HDFS (/data/github/hasil/)
  ✅ Simpan spark_results.json ke dashboard/data/ (otomatis, tanpa download)

Mode penggunaan:
  python spark/run_analysis.py                    # sekali, baca HDFS
  python spark/run_analysis.py --local             # sekali, baca file lokal
  python spark/run_analysis.py --watch 60          # loop setiap 60 detik
  python spark/run_analysis.py --watch 60 --local  # loop, baca lokal

Fallback: Jika PySpark gagal (misal di Windows), otomatis fallback ke
          plain Python agar pipeline tetap jalan.
"""

import json
import os
import sys
import time
import argparse
import subprocess
import re
from datetime import datetime
from collections import Counter, defaultdict

# ──────────────────────────── PATHS ────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING_API = os.path.join(BASE_DIR, "tmp", "spark_staging", "api")
STAGING_RSS = os.path.join(BASE_DIR, "tmp", "spark_staging", "rss")
OUTPUT_JSON = os.path.join(BASE_DIR, "dashboard", "data", "spark_results.json")

HDFS_API = "hdfs://localhost:8020/data/github/api/"
HDFS_RSS = "hdfs://localhost:8020/data/github/rss/"
HDFS_HASIL = "hdfs://localhost:8020/data/github/hasil/"

# ════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS — Baca data dari HDFS / lokal
# ════════════════════════════════════════════════════════════════

def _load_json_dir(directory):
    """Load semua file JSON dari directory lokal."""
    records = []
    if not os.path.exists(directory):
        return records
    for fname in os.listdir(directory):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(directory, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        records.extend(data)
                    else:
                        records.append(data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
    return records


def _load_from_hdfs(hdfs_path):
    """Baca semua file JSON dari HDFS via docker exec."""
    records = []
    try:
        # List files in HDFS directory
        result = subprocess.run(
            ["docker", "exec", "namenode", "hdfs", "dfs", "-ls", hdfs_path],
            capture_output=True, text=True, timeout=15, encoding='utf-8', errors='replace'
        )
        if result.returncode != 0:
            return records

        # Parse file paths from ls output
        for line in result.stdout.strip().split("\n"):
            if line.startswith("-"):  # file entry
                parts = line.split()
                if len(parts) >= 8:
                    filepath = parts[-1]
                    if filepath.endswith(".json"):
                        # Cat each file from HDFS
                        cat_result = subprocess.run(
                            ["docker", "exec", "namenode", "hdfs", "dfs", "-cat", filepath],
                            capture_output=True, text=True, timeout=15,
                            encoding='utf-8', errors='replace'
                        )
                        if cat_result.returncode == 0 and cat_result.stdout.strip():
                            try:
                                data = json.loads(cat_result.stdout)
                                if isinstance(data, list):
                                    records.extend(data)
                                else:
                                    records.append(data)
                            except json.JSONDecodeError:
                                pass
    except Exception as e:
        print(f" docker exec gagal: {e}")
    return records


def _upload_to_hdfs_docker():
    """Upload spark_results.json ke HDFS via docker cp + hdfs dfs -put."""
    try:
        print(" Upload ke HDFS via docker cp...")
        subprocess.run(
            ["docker", "cp", OUTPUT_JSON, "namenode:/tmp/spark_results.json"],
            check=True, capture_output=True, timeout=15
        )
        subprocess.run(
            ["docker", "exec", "namenode", "hdfs", "dfs", "-mkdir", "-p", "/data/github/hasil"],
            check=True, capture_output=True, timeout=15
        )
        subprocess.run(
            ["docker", "exec", "namenode", "hdfs", "dfs", "-put", "-f",
             "/tmp/spark_results.json", "/data/github/hasil/spark_results.json"],
            check=True, capture_output=True, timeout=15
        )
        print(" Tersimpan ke HDFS: /data/github/hasil/spark_results.json")
    except Exception as e:
        print(f" Upload ke HDFS gagal (Docker mungkin mati): {e}")


# ════════════════════════════════════════════════════════════════
#  MODE 1: SPARK (sesuai ketentuan tugas)
#  Data dibaca dari HDFS (via docker exec), dianalisis dengan
#  Spark SQL + DataFrame API.
# ════════════════════════════════════════════════════════════════

def run_spark_analysis(use_hdfs=True):
    """Jalankan 3 analisis menggunakan PySpark (DataFrame API + Spark SQL).
    
    Data dibaca dari HDFS via docker exec (karena PySpark di Windows
    tidak bisa langsung konek ke HDFS datanode di Docker internal IP).
    """
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    # Fix Windows: PySpark cari 'python3' yang tidak ada di Windows
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    print(" Inisialisasi SparkSession...")

    # SESUAI KETENTUAN TUGAS
    spark = SparkSession.builder \
        .appName("GitTrend-Analysis") \
        .master("local[*]") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:8020") \
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.pyspark.python", sys.executable) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    print(f" Spark {spark.version} ready")

    # ── Load Data dari HDFS (Native Spark) ──
    print("\n Membaca data dari HDFS secara native (spark.read)...")
    try:
        # Sesuai ketentuan tugas (Baca file JSON dari HDFS langsung tanpa loop)
        df_api = spark.read.option("multiLine", True).json("hdfs://namenode:8020/data/github/api/")
        total_api = df_api.count()
        
        # Baca juga RSS
        try:
            df_rss = spark.read.option("multiLine", True).json("hdfs://namenode:8020/data/github/rss/")
            total_rss = df_rss.count()
        except Exception:
            df_rss = None
            total_rss = 0
            
    except Exception as e:
        print(f" Gagal membaca HDFS secara native: {e}")
        spark.stop()
        return False

    print(f" {total_api} API records, {total_rss} RSS records (source: HDFS Native)")

    if total_api == 0:
        print(" Tidak ada data API. Jalankan producer + consumer dulu.")
        spark.stop()
        return False

    # Register untuk Spark SQL (Sesuai ketentuan)
    df_api.createOrReplaceTempView("repos")

    # ══════════════════════════════════════════════════════════
    # ANALISIS 1: Distribusi Bahasa Pemrograman (Spark SQL)
    # ══════════════════════════════════════════════════════════
    print("\n Analisis 1: Distribusi Bahasa Pemrograman (Spark SQL)...")

    df_lang = spark.sql("""
        SELECT
            COALESCE(language, 'Unknown') AS language,
            COUNT(*)                      AS repo_count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM repos), 1) AS percentage,
            ROUND(AVG(stargazers_count), 1)  AS avg_stars,
            SUM(forks_count)                 AS total_forks
        FROM repos
        GROUP BY COALESCE(language, 'Unknown')
        ORDER BY repo_count DESC
    """)

    lang_results = []
    for row in df_lang.collect():
        lang_results.append({
            "language": row["language"],
            "repo_count": row["repo_count"],
            "percentage": str(row["percentage"]),
            "avg_stars": float(row["avg_stars"]),
            "total_forks": int(row["total_forks"]),
        })
    print(f" {len(lang_results)} bahasa ditemukan")
    for r in lang_results[:5]:
        print(f"      {r['language']}: {r['repo_count']} repos ({r['percentage']}%)")

    # ══════════════════════════════════════════════════════════
    # ANALISIS 2: Top 10 Repositori (Spark SQL + DataFrame API)
    # ══════════════════════════════════════════════════════════
    print("\n Analisis 2: Top 10 Repositori (Spark SQL)...")

    df_top = spark.sql("""
        SELECT
            full_name,
            MAX(COALESCE(language, 'Unknown')) AS language,
            MAX(stargazers_count) AS stargazers_count,
            MAX(forks_count) AS forks_count,
            MAX(SUBSTRING(COALESCE(description, ''), 1, 80)) AS description_short
        FROM repos
        WHERE full_name IS NOT NULL
        GROUP BY full_name
        ORDER BY stargazers_count DESC
        LIMIT 10
    """)

    top10_results = []
    for rank, row in enumerate(df_top.collect(), 1):
        top10_results.append({
            "rank": rank,
            "full_name": row["full_name"],
            "language": row["language"],
            "stargazers_count": int(row["stargazers_count"]),
            "forks_count": int(row["forks_count"]),
            "description_short": row["description_short"] or "",
        })
    print(f" Top {len(top10_results)} repos")
    for r in top10_results[:3]:
        print(f"      #{r['rank']} {r['stargazers_count']} {r['full_name']}")

    # ══════════════════════════════════════════════════════════
    # ANALISIS 3: Kata Trending di Deskripsi (DataFrame API)
    # ══════════════════════════════════════════════════════════
    print("\n Analisis 3: Kata Trending (DataFrame API + explode)...")

    stop_words = [
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'it', 'that', 'this', 'are', 'was',
        'be', 'has', 'have', 'had', 'not', 'no', 'can', 'will', 'do', 'if',
        'your', 'you', 'we', 'they', 'all', 'any', 'as', 'up', 'out', 'so',
        'its', 'than', 'then', 'into', 'over', 'also', 'just', 'more', 'about',
        'one', 'two', 'new', 'use', 'using', 'used', 'get', 'set', 'via', 'etc',
        '', '-', '--', '—', '|', 'https', 'http', 'www', 'com'
    ]

    # Pipeline: filter null → lowercase → remove non-alpha → split → explode → filter → count
    df_words = df_api \
        .filter(F.col("description").isNotNull()) \
        .filter(F.col("description") != '') \
        .select(F.explode(
            F.split(
                F.lower(F.regexp_replace(F.col("description"), r"[^a-zA-Z\s]", "")),
                r"\s+"
            )
        ).alias("word")) \
        .filter(~F.col("word").isin(stop_words)) \
        .filter(F.length("word") >= 4) \
        .groupBy("word") \
        .agg(F.count("*").alias("frequency")) \
        .orderBy(F.desc("frequency")) \
        .limit(30)

    word_results = []
    for row in df_words.collect():
        word_results.append({
            "word": row["word"],
            "frequency": int(row["frequency"]),
        })
    print(f" {len(word_results)} trending words")
    for r in word_results[:5]:
        print(f"      \"{r['word']}\": {r['frequency']}x")

    # ── Compile Results ──
    spark_results = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "spark_version": spark.version,
            "total_api_records": total_api,
            "total_rss_records": total_rss,
            "analysis_count": 3,
            "source": "HDFS" if use_hdfs else "local_staging",
        },
        "analysis_1_language_distribution": lang_results,
        "analysis_2_top_repos": top10_results,
        "analysis_3_trending_words": word_results,
    }

    # ── Save ke lokal (dashboard/data/spark_results.json) ──
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(spark_results, f, indent=2, ensure_ascii=False)
    print(f"\n Tersimpan: {OUTPUT_JSON}")

    # ── Save ke HDFS (/data/github/hasil/) (Native Spark) ──
    if use_hdfs:
        try:
            print(" Menyimpan hasil ke HDFS secara native (df.write)...")
            from pyspark.sql.types import StringType
            result_rdd = spark.sparkContext.parallelize([json.dumps(spark_results, ensure_ascii=False)])
            result_df = spark.read.json(result_rdd)
            # Sesuai ketentuan tugas
            result_df.coalesce(1).write.mode("overwrite").json("hdfs://namenode:8020/data/github/hasil/")
            print(f" Tersimpan ke HDFS: hdfs://namenode:8020/data/github/hasil/")
        except Exception as e:
            print(f" Gagal simpan ke HDFS secara native: {e}")
            print("   (Mencoba fallback via docker cp...)")
            _upload_to_hdfs_docker()
    else:
        _upload_to_hdfs_docker()

    spark.stop()
    print(" SparkSession stopped")
    return True



# ════════════════════════════════════════════════════════════════
#  MODE 2: FALLBACK (plain Python, jika PySpark gagal)
#  Tetap baca dari HDFS via docker exec (sesuai ketentuan tugas)
# ════════════════════════════════════════════════════════════════


def run_fallback_analysis():
    """Jalankan 3 analisis dengan plain Python. Baca dari HDFS via docker exec."""
    print("⚠️  PySpark tidak tersedia — menggunakan fallback plain Python")
    print("   (Tetap membaca dari HDFS via docker exec)\n")

    # Coba baca dari HDFS dulu (sesuai ketentuan tugas)
    print("📂 Membaca data dari HDFS via docker exec...")
    api_records = _load_from_hdfs("/data/github/api/")
    rss_records = _load_from_hdfs("/data/github/rss/")
    data_source = "HDFS"

    # Fallback ke lokal jika HDFS kosong/gagal
    if not api_records:
        print("   ⚠️  HDFS kosong, fallback ke staging lokal...")
        api_records = _load_json_dir(STAGING_API)
        rss_records = _load_json_dir(STAGING_RSS)
        data_source = "local_staging"

    print(f"   ✅ {len(api_records)} API records, {len(rss_records)} RSS records (source: {data_source})")

    if not api_records:
        print("❌ Tidak ada data API.")
        return False

    # Analisis 1: Distribusi Bahasa
    print("\n📊 Analisis 1: Distribusi Bahasa Pemrograman...")
    lang_stats = defaultdict(lambda: {"count": 0, "stars": [], "forks": 0})
    for repo in api_records:
        lang = repo.get("language") or "Unknown"
        lang_stats[lang]["count"] += 1
        lang_stats[lang]["stars"].append(repo.get("stargazers_count", 0))
        lang_stats[lang]["forks"] += repo.get("forks_count", 0)

    total = len(api_records)
    lang_results = sorted([
        {
            "language": lang,
            "repo_count": s["count"],
            "percentage": str(round(s["count"] * 100.0 / total, 1)),
            "avg_stars": round(sum(s["stars"]) / len(s["stars"]), 1),
            "total_forks": s["forks"],
        }
        for lang, s in lang_stats.items()
    ], key=lambda x: x["repo_count"], reverse=True)
    print(f"   ✅ {len(lang_results)} bahasa")

    # Analisis 2: Top 10
    print("⭐ Analisis 2: Top 10 Repositori...")
    
    unique_repos = {}
    for r in api_records:
        name = r.get("full_name", "")
        if not name:
            continue
        # Simpan jika belum ada, atau jika stars-nya lebih tinggi (update terbaru)
        if name not in unique_repos or r.get("stargazers_count", 0) > unique_repos[name].get("stargazers_count", 0):
            unique_repos[name] = r

    sorted_repos = sorted(unique_repos.values(), key=lambda x: x.get("stargazers_count", 0), reverse=True)
    top10_results = [{
        "rank": i + 1,
        "full_name": r.get("full_name", ""),
        "language": r.get("language") or "Unknown",
        "stargazers_count": r.get("stargazers_count", 0),
        "forks_count": r.get("forks_count", 0),
        "description_short": (r.get("description") or "")[:80],
    } for i, r in enumerate(sorted_repos[:10])]
    print(f"   ✅ Top {len(top10_results)} repos")

    # Analisis 3: Kata Trending
    print("🔥 Analisis 3: Kata Trending...")
    stop = {"the", "and", "for", "with", "that", "this", "from", "your", "have",
            "will", "about", "into", "over", "also", "just", "more", "than", "then",
            "used", "using", "http", "https", "www", "com"}
    counter = Counter()
    for repo in api_records:
        desc = repo.get("description") or ""
        words = re.sub(r"[^a-zA-Z\s]", "", desc.lower()).split()
        counter.update(w for w in words if len(w) >= 4 and w not in stop)

    word_results = [{"word": w, "frequency": f} for w, f in counter.most_common(30)]
    print(f"   ✅ {len(word_results)} trending words")

    # Compile & Save
    spark_results = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "spark_version": "fallback-python",
            "total_api_records": len(api_records),
            "total_rss_records": len(rss_records),
            "analysis_count": 3,
            "source": data_source,
        },
        "analysis_1_language_distribution": lang_results,
        "analysis_2_top_repos": top10_results,
        "analysis_3_trending_words": word_results,
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(spark_results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Tersimpan: {OUTPUT_JSON}")

    _upload_to_hdfs_docker()
    return True


# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════

def run_once(use_local):
    """Jalankan analisis sekali.
    
    Mencoba menjalankan PySpark asli terlebih dahulu. Jika gagal (misal
    karena error environment/Java/network), baru akan menggunakan fallback.
    """
    try:
        success = run_spark_analysis(use_hdfs=not use_local)
        if success:
            return True
        return run_fallback_analysis()
    except Exception as e:
        print(f"\n⚠️ PySpark gagal dijalankan ({e}).\nBeralih ke fallback plain Python...")
        return run_fallback_analysis()


def main():
    parser = argparse.ArgumentParser(
        description="GitTrend Spark Analysis Runner — pengganti analysis.ipynb"
    )
    parser.add_argument(
        "--watch", type=int, default=0,
        help="Re-run analysis setiap N detik (0 = sekali saja)"
    )
    parser.add_argument(
        "--local", action="store_true",
        help="Baca dari tmp/spark_staging/ (bukan HDFS)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 GitTrend Spark Analysis Runner")
    print("=" * 60)
    print(f"   HDFS API:   {HDFS_API}")
    print(f"   HDFS RSS:   {HDFS_RSS}")
    print(f"   Staging:    {STAGING_API}")
    print(f"   Output:     {OUTPUT_JSON}")
    print(f"   Mode:       {'🔄 Watch (' + str(args.watch) + 's)' if args.watch else '⚡ Single run'}")
    print(f"   Source:     {'📁 Local staging' if args.local else '🐘 HDFS'}")

    if args.watch > 0:
        print(f"   Stop:       Ctrl+C\n")
        try:
            while True:
                run_once(args.local)
                print(f"\n⏳ Next update in {args.watch}s... (Ctrl+C to stop)")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\n\n👋 Stopped.")
    else:
        success = run_once(args.local)
        if success:
            print("\n🎉 Done! Dashboard bisa baca spark_results.json")


if __name__ == "__main__":
    main()
