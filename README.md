## 🚀 Menjalankan Kafka Producer (GitHub API)

### 📌 Prasyarat

Pastikan sudah tersedia:

* Docker & Docker Compose
* Python 3.x

---

## ⚙️ 1. Setup Environment

Install dependency:

```bash
pip install requests kafka-python python-dotenv
```

---

## 🐳 2. Menjalankan Kafka

Dari root project:

```bash
docker-compose -f docker-compose-kafka.yml up -d
```

Cek container:

```bash
docker ps
```

Pastikan ada:

* `zookeeper`
* `kafka-broker`

---

## ▶️ 3. Menjalankan Producer

Masuk ke folder kafka:

```bash
cd kafka
```

Jalankan:

```bash
python producer_api.py
```

Jika berhasil, akan muncul log:

```text
GitHub API Producer dimulai
Berhasil fetch 30 repo
Berhasil kirim 30/30 event ke topic 'github-api'
```

---

## 🧪 4. Verifikasi Data di Kafka

Jalankan perintah berikut (1 baris, PowerShell compatible):

```bash
docker exec -it kafka-broker kafka-console-consumer --topic github-api --from-beginning --bootstrap-server localhost:9092
```

Jika berhasil, akan muncul data JSON seperti:

```json
{
  "full_name": "repo-name",
  "stargazers_count": 123
}
```

