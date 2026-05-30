from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

# Definisikan path untuk ketiga file
DATA_SPARK = "./data/spark_results.json"
DATA_LIVE_API = "./data/live_api.json"
DATA_LIVE_RSS = "./data/live_rss.json"

def load_json(filepath, default_value):
    """
    Membaca file JSON dengan error handling penuh.
    Jika file tidak ada, isinya kosong, atau JSON tidak valid/rusak, 
    maka akan mengembalikan default_value dengan aman.
    """
    if not os.path.exists(filepath):
        return default_value
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Jika file isinya cuma kata 'null' atau kosong, kembalikan default
            return data if data is not None else default_value
    except json.JSONDecodeError as e:
        print(f"Warning: Format JSON rusak atau kosong di {filepath} - {e}")
        return default_value
    except Exception as e:
        print(f"Error: Gagal mengakses file {filepath} - {e}")
        return default_value

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    # Gunakan default {} (Dictionary) untuk Spark karena bentuknya Object
    spark_data = load_json(DATA_SPARK, default_value={})
    
    # Gunakan default [] (List/Array) untuk data Kafka/Live karena bentuknya Array
    live_api_data = load_json(DATA_LIVE_API, default_value=[])
    live_rss_data = load_json(DATA_LIVE_RSS, default_value=[])

    return jsonify({
        "spark_data": spark_data,
        "live_api": live_api_data,
        "live_rss": live_rss_data
    })

# === BONUS LAKEHOUSE: Path ke Gold Delta JSON exports ===
# Endpoint /api/gold membaca dari output 03_gold.py (lakehouse pipeline)
# Endpoint /api/data yang lama TIDAK DIUBAH (bersifat additive)
GOLD_JSON_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "lakehouse", "lakehouse_data", "gold_json"
)

@app.route("/api/gold")
def gold_data():
    """
    Endpoint baru: membaca analisis dari Gold Delta Lake layer.
    Fallback ke spark_results.json jika Gold belum di-generate.
    """
    gold_result = {}

    # Coba baca dari Gold JSON exports
    gold_files = {
        "language_dist": "language_dist.json",
        "top_repos": "top_repos.json",
        "star_velocity": "star_velocity.json",
        "emerging_topics": "emerging_topics.json",
        "cross_source": "cross_source.json"
    }

    has_gold = False
    for key, filename in gold_files.items():
        filepath = os.path.join(GOLD_JSON_DIR, filename)
        data = load_json(filepath, default_value=None)
        if data is not None:
            gold_result[key] = data
            has_gold = True
        else:
            gold_result[key] = []

    # Metadata
    gold_result["source"] = "gold_delta" if has_gold else "not_available"
    gold_result["message"] = (
        "Data dari Gold Delta Lake layer"
        if has_gold
        else "Gold layer belum di-generate. Jalankan: python lakehouse/03_gold.py"
    )

    return jsonify(gold_result)

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)