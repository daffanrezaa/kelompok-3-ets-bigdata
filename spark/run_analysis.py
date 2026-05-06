"""
GitTrend — Local Analysis Runner
Replika 3 analisis Spark menggunakan plain Python.
Membaca dari tmp/spark_staging/, simpan ke dashboard/data/spark_results.json.

Bisa dijalankan sekali atau loop berkala:
  python spark/run_analysis.py              # sekali
  python spark/run_analysis.py --watch 60   # setiap 60 detik
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime
from collections import Counter, defaultdict
import re
import statistics

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(BASE_DIR, "tmp", "spark_staging", "api")
RSS_DIR = os.path.join(BASE_DIR, "tmp", "spark_staging", "rss")
OUTPUT_PATH = os.path.join(BASE_DIR, "dashboard", "data", "spark_results.json")


def load_json_files(directory):
    """Load semua file JSON dari directory."""
    records = []
    if not os.path.exists(directory):
        print(f"  ⚠️  Directory tidak ditemukan: {directory}")
        return records
    for fname in os.listdir(directory):
        if fname.endswith(".json"):
            fpath = os.path.join(directory, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        records.extend(data)
                    else:
                        records.append(data)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"  ⚠️  Skip {fname}: {e}")
    return records


def analysis_1_language_distribution(api_records):
    """Analisis 1: Distribusi bahasa pemrograman (replika Spark SQL GROUP BY)."""
    lang_stats = defaultdict(lambda: {"count": 0, "stars": [], "forks": 0})

    for repo in api_records:
        lang = repo.get("language") or "Unknown"
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        lang_stats[lang]["count"] += 1
        lang_stats[lang]["stars"].append(stars)
        lang_stats[lang]["forks"] += forks

    total = len(api_records)
    results = []
    for lang, stats in lang_stats.items():
        avg_stars = round(sum(stats["stars"]) / len(stats["stars"]), 1) if stats["stars"] else 0
        results.append({
            "language": lang,
            "repo_count": stats["count"],
            "percentage": str(round(stats["count"] * 100.0 / total, 1)) if total > 0 else "0",
            "avg_stars": avg_stars,
            "total_forks": stats["forks"],
        })

    results.sort(key=lambda x: x["repo_count"], reverse=True)
    return results


def analysis_2_top_repos(api_records):
    """Analisis 2: Top 10 repo berdasarkan stars (replika DataFrame API orderBy)."""
    sorted_repos = sorted(api_records, key=lambda x: x.get("stargazers_count", 0), reverse=True)
    results = []
    for rank, repo in enumerate(sorted_repos[:10], 1):
        desc = repo.get("description", "") or ""
        results.append({
            "rank": rank,
            "full_name": repo.get("full_name", ""),
            "language": repo.get("language") or "Unknown",
            "stargazers_count": repo.get("stargazers_count", 0),
            "forks_count": repo.get("forks_count", 0),
            "description_short": desc[:80],
        })
    return results


def analysis_3_trending_words(api_records):
    """Analisis 3: Kata trending di deskripsi (replika DataFrame explode + groupBy)."""
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "it", "that", "this", "are", "was",
        "be", "has", "have", "had", "not", "no", "can", "will", "do", "if",
        "your", "you", "we", "they", "all", "any", "as", "up", "out", "so",
        "its", "than", "then", "into", "over", "also", "just", "more", "about",
        "one", "two", "new", "use", "using", "used", "get", "set", "via", "etc",
        "", "-", "--", "—", "|", "https", "http", "www", "com",
    }

    word_counts = Counter()
    for repo in api_records:
        desc = repo.get("description", "") or ""
        # Lowercase, remove non-alpha, split
        cleaned = re.sub(r"[^a-zA-Z\s]", "", desc.lower())
        words = cleaned.split()
        for word in words:
            if word not in stop_words and len(word) >= 4:
                word_counts[word] += 1

    results = [{"word": word, "frequency": freq} for word, freq in word_counts.most_common(30)]
    return results


def run_analysis():
    """Jalankan 3 analisis dan simpan ke spark_results.json."""
    print(f"\n{'='*60}")
    print(f"🔄 Running analysis at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    # Load data
    print("📂 Loading API data...")
    api_records = load_json_files(API_DIR)
    print(f"   ✅ {len(api_records)} API records")

    print("📂 Loading RSS data...")
    rss_records = load_json_files(RSS_DIR)
    print(f"   ✅ {len(rss_records)} RSS records")

    if not api_records:
        print("❌ No API data found. Run consumer_to_hdfs.py first.")
        return False

    # Analysis 1
    print("\n📊 Analisis 1: Distribusi Bahasa Pemrograman...")
    lang_results = analysis_1_language_distribution(api_records)
    print(f"   ✅ {len(lang_results)} bahasa ditemukan")
    for r in lang_results[:5]:
        print(f"      {r['language']}: {r['repo_count']} repos ({r['percentage']}%)")

    # Analysis 2
    print("\n⭐ Analisis 2: Top 10 Repositori...")
    top10_results = analysis_2_top_repos(api_records)
    print(f"   ✅ Top {len(top10_results)} repos")
    for r in top10_results[:3]:
        print(f"      #{r['rank']} ⭐{r['stargazers_count']} {r['full_name']}")

    # Analysis 3
    print("\n🔥 Analisis 3: Kata Trending...")
    word_results = analysis_3_trending_words(api_records)
    print(f"   ✅ {len(word_results)} trending words")
    for r in word_results[:5]:
        print(f"      \"{r['word']}\": {r['frequency']}x")

    # Compile results
    spark_results = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "spark_version": "local-python-runner",
            "total_api_records": len(api_records),
            "total_rss_records": len(rss_records),
            "analysis_count": 3,
        },
        "analysis_1_language_distribution": lang_results,
        "analysis_2_top_repos": top10_results,
        "analysis_3_trending_words": word_results,
    }

    # Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(spark_results, f, indent=2, ensure_ascii=False)

    size = os.path.getsize(OUTPUT_PATH)
    print(f"\n✅ Saved to: {OUTPUT_PATH}")
    print(f"   File size: {size} bytes")
    return True


def main():
    parser = argparse.ArgumentParser(description="GitTrend Local Analysis Runner")
    parser.add_argument(
        "--watch", type=int, default=0,
        help="Re-run analysis every N seconds (0 = run once)"
    )
    args = parser.parse_args()

    print("🚀 GitTrend Local Analysis Runner")
    print(f"   API dir:  {API_DIR}")
    print(f"   RSS dir:  {RSS_DIR}")
    print(f"   Output:   {OUTPUT_PATH}")

    if args.watch > 0:
        print(f"   Mode:     🔄 Watch (every {args.watch}s)")
        print(f"   Stop:     Ctrl+C")
        try:
            while True:
                run_analysis()
                print(f"\n⏳ Next update in {args.watch}s... (Ctrl+C to stop)")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\n\n👋 Stopped.")
    else:
        print("   Mode:     ⚡ Single run")
        success = run_analysis()
        if success:
            print("\n🎉 Done! Dashboard can now read spark_results.json")


if __name__ == "__main__":
    main()
