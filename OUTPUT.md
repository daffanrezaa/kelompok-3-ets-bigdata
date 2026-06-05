(venv311) linnaeauss@yolo:/mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata$ python lakehouse/01_bronze.py
============================================================
  🥉 BRONZE LAYER — Ingest Raw Data ke Delta Lake
============================================================

✅ delta-spark ditemukan, menggunakan configure_spark_with_delta_pip
26/06/04 09:45:30 WARN Utils: Your hostname, Deefen resolves to a loopback address: 127.0.1.1; using 10.255.255.254 instead (on interface lo)
26/06/04 09:45:30 WARN Utils: Set SPARK_LOCAL_IP if you need to bind to another address
:: loading settings :: url = jar:file:/mnt/d/Kuliah/SEMESTER%204/BIG%20DATA/ETS/kelompok-3-ets-bigdata/venv311/lib/python3.11/site-packages/pyspark/jars/ivy-2.5.1.jar!/org/apache/ivy/core/settings/ivysettings.xml
Ivy Default Cache set to: /home/deefen/.ivy2/cache
The jars for the packages stored in: /home/deefen/.ivy2/jars
io.delta#delta-spark_2.12 added as a dependency
:: resolving dependencies :: org.apache.spark#spark-submit-parent-ce5bc360-79b4-4c03-9504-e5afa6b066fa;1.0
        confs: [default]
        found io.delta#delta-spark_2.12;3.1.0 in central
        found io.delta#delta-storage;3.1.0 in central
        found org.antlr#antlr4-runtime;4.9.3 in central
:: resolution report :: resolve 149ms :: artifacts dl 5ms
        :: modules in use:
        io.delta#delta-spark_2.12;3.1.0 from central in [default]
        io.delta#delta-storage;3.1.0 from central in [default]
        org.antlr#antlr4-runtime;4.9.3 from central in [default]
        ---------------------------------------------------------------------
        |                  |            modules            ||   artifacts   |
        |       conf       | number| search|dwnlded|evicted|| number|dwnlded|
        ---------------------------------------------------------------------
        |      default     |   3   |   0   |   0   |   0   ||   3   |   0   |
        ---------------------------------------------------------------------
:: retrieving :: org.apache.spark#spark-submit-parent-ce5bc360-79b4-4c03-9504-e5afa6b066fa
        confs: [default]
        0 artifacts copied, 3 already retrieved (0kB/5ms)
26/06/04 09:45:31 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
Setting default log level to "WARN".
To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).
   Spark version: 3.5.3

📂 [1/4] Membaca data GitHub API...
   ✅ Berhasil baca dari HDFS: 210 records

📂 [2/4] Membaca data RSS...
   ✅ Berhasil baca dari HDFS: 20 records

💾 [3/4] Menambahkan metadata dan menyimpan ke Bronze Delta...
26/06/04 09:45:44 WARN GarbageCollectionMetrics: To enable non-built-in garbage collector(s) List(G1 Concurrent GC), users should configure it(them) to spark.eventLog.gcMetrics.youngGenerationGarbageCollectors or spark.eventLog.gcMetrics.oldGenerationGarbageCollectors
26/06/04 09:45:46 WARN SparkStringUtils: Truncated the string representation of a plan since it was too large. This behavior can be adjusted by setting 'spark.sql.debug.maxToStringFields'.
   ✅ Bronze API disimpan: /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/bronze/github_api
   ✅ Bronze RSS disimpan: /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/bronze/github_rss

📊 [4/4] Verifikasi Bronze Layer...

============================================================
  ✅ BRONZE LAYER SELESAI
============================================================
  📦 Bronze API : 210 records (sumber: HDFS (hdfs://namenode:8020/data/github/api/))
  📦 Bronze RSS : 20 records (sumber: HDFS (hdfs://namenode:8020/data/github/rss/))
  📁 Output     : /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/bronze/
============================================================

📋 Schema Bronze API:
root
 |-- created_at: string (nullable = true)
 |-- description: string (nullable = true)
 |-- forks_count: long (nullable = true)
 |-- full_name: string (nullable = true)
 |-- html_url: string (nullable = true)
 |-- ingested_at: string (nullable = true)
 |-- language: string (nullable = true)
 |-- license: string (nullable = true)
 |-- open_issues_count: long (nullable = true)
 |-- owner: string (nullable = true)
 |-- pushed_at: string (nullable = true)
 |-- size: long (nullable = true)
 |-- source: string (nullable = true)
 |-- stargazers_count: long (nullable = true)
 |-- topics: array (nullable = true)
 |    |-- element: string (containsNull = true)
 |-- watchers_count: long (nullable = true)
 |-- _ingested_at: timestamp (nullable = true)
 |-- _source: string (nullable = true)

📋 Sample Bronze API (5 baris):
+-----------------------------+----------+----------------+--------------------------+--------------------------+-------+
|                    full_name|  language|stargazers_count|               ingested_at|              _ingested_at|_source|
+-----------------------------+----------+----------------+--------------------------+--------------------------+-------+
|pewdiepie-archdaemon/odysseus|JavaScript|           41640|2026-06-04T01:55:50.037909|2026-06-04 09:45:41.635901|    api|
|      Gloridust/WechatOnCloud|TypeScript|            1900|2026-06-04T01:55:50.341920|2026-06-04 09:45:41.635901|    api|
|                b-nnett/goose|      Rust|            1380|2026-06-04T01:55:50.344772|2026-06-04 09:45:41.635901|    api|
|    asz798838958/aBaiAutoplus|    Python|            1360|2026-06-04T01:55:50.346629|2026-06-04 09:45:41.635901|    api|
|       ClaudioDrews/memory-os|    Python|             732|2026-06-04T01:55:50.348694|2026-06-04 09:45:41.635901|    api|
+-----------------------------+----------+----------------+--------------------------+--------------------------+-------+
only showing top 5 rows

📋 Schema Bronze RSS:
root
 |-- author: string (nullable = true)
 |-- ingested_at: string (nullable = true)
 |-- link: string (nullable = true)
 |-- published: string (nullable = true)
 |-- source: string (nullable = true)
 |-- source_url: string (nullable = true)
 |-- summary: string (nullable = true)
 |-- tags: array (nullable = true)
 |    |-- element: string (containsNull = true)
 |-- title: string (nullable = true)
 |-- _ingested_at: timestamp (nullable = true)
 |-- _source: string (nullable = true)

📋 Sample Bronze RSS (5 baris):
+----------------------------------------+-----------------------------+--------------------------+-------------------------+-------+
|                                   title|                       author|               ingested_at|             _ingested_at|_source|
+----------------------------------------+-----------------------------+--------------------------+-------------------------+-------+
|Ultrahuman says hackers accessed cust...|                Jagmeet Singh|2026-06-04T01:56:04.692783|2026-06-04 09:45:48.47097|    rss|
|Carvana ties up with Bezos-backed Sla...|                  Sean O'Kane|2026-06-04T01:56:04.810606|2026-06-04 09:45:48.47097|    rss|
|Instagram is alerting users who were ...|Lorenzo Franceschi-Bicchierai|2026-06-04T01:56:04.812730|2026-06-04 09:45:48.47097|    rss|
|Amazon will show AI product images wh...|                  Sarah Perez|2026-06-04T01:56:04.814375|2026-06-04 09:45:48.47097|    rss|
|Still facing copyright lawsuits, AI m...|            Amanda Silberling|2026-06-04T01:56:04.815979|2026-06-04 09:45:48.47097|    rss|
+----------------------------------------+-----------------------------+--------------------------+-------------------------+-------+
only showing top 5 rows


🏁 Spark session ditutup. Bronze layer selesai!
(venv311) linnaeauss@yolo:/mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata$ python lakehouse/01_silver.py
python: can't open file '/mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/01_silver.py': [Errno 2] No such file or directory
(venv311) linnaeauss@yolo:/mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata$ python lakehouse/02_silver.py
============================================================
  🥈 SILVER LAYER — Cleaning & Transformasi
============================================================
26/06/04 09:46:36 WARN Utils: Your hostname, Deefen resolves to a loopback address: 127.0.1.1; using 10.255.255.254 instead (on interface lo)
26/06/04 09:46:36 WARN Utils: Set SPARK_LOCAL_IP if you need to bind to another address
:: loading settings :: url = jar:file:/mnt/d/Kuliah/SEMESTER%204/BIG%20DATA/ETS/kelompok-3-ets-bigdata/venv311/lib/python3.11/site-packages/pyspark/jars/ivy-2.5.1.jar!/org/apache/ivy/core/settings/ivysettings.xml
Ivy Default Cache set to: /home/deefen/.ivy2/cache
The jars for the packages stored in: /home/deefen/.ivy2/jars
io.delta#delta-spark_2.12 added as a dependency
:: resolving dependencies :: org.apache.spark#spark-submit-parent-69065376-8fc2-44c9-aea5-a1c3d075ee38;1.0
        confs: [default]
        found io.delta#delta-spark_2.12;3.1.0 in central
        found io.delta#delta-storage;3.1.0 in central
        found org.antlr#antlr4-runtime;4.9.3 in central
:: resolution report :: resolve 145ms :: artifacts dl 5ms
        :: modules in use:
        io.delta#delta-spark_2.12;3.1.0 from central in [default]
        io.delta#delta-storage;3.1.0 from central in [default]
        org.antlr#antlr4-runtime;4.9.3 from central in [default]
        ---------------------------------------------------------------------
        |                  |            modules            ||   artifacts   |
        |       conf       | number| search|dwnlded|evicted|| number|dwnlded|
        ---------------------------------------------------------------------
        |      default     |   3   |   0   |   0   |   0   ||   3   |   0   |
        ---------------------------------------------------------------------
:: retrieving :: org.apache.spark#spark-submit-parent-69065376-8fc2-44c9-aea5-a1c3d075ee38
        confs: [default]
        0 artifacts copied, 3 already retrieved (0kB/4ms)
26/06/04 09:46:37 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
Setting default log level to "WARN".
To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).

📂 Membaca Bronze API...
26/06/04 09:46:46 WARN SparkStringUtils: Truncated the string representation of a plan since it was too large. This behavior can be adjusted by setting 'spark.sql.debug.maxToStringFields'.
   📦 Bronze API: 210 records                                                   
26/06/04 09:46:52 WARN GarbageCollectionMetrics: To enable non-built-in garbage collector(s) List(G1 Concurrent GC), users should configure it(them) to spark.eventLog.gcMetrics.youngGenerationGarbageCollectors or spark.eventLog.gcMetrics.oldGenerationGarbageCollectors
   ✅ T1 — Drop duplikat (full_name + ingested_at): 210 → 210 (+0 baris, 0.0% dihapus)
   ✅ T2 — Parse timestamps (ingested_at, created_at, pushed_at): 210 → 210 (+0 baris, 0.0% dihapus)
   ✅ T3 — Handle null (language → 'Unknown', filter full_name null): 210 → 210 (+0 baris, 0.0% dihapus)
   ✅ T4 — Ekstrak jam (_hour dari ingested_at): 210 → 210 (+0 baris, 0.0% dihapus)
   ✅ T5 — Standarisasi (trim full_name, description): 210 → 210 (+0 baris, 0.0% dihapus)

   📊 API Total: 210 → 210 (0 baris dihapus)

📂 Membaca Bronze RSS...
   📦 Bronze RSS: 20 records
   ✅ T1 — Drop duplikat (link): 20 → 20 (+0 baris, 0.0% dihapus)
   ✅ T2 — Parse timestamps (ingested_at, published RFC2822): 20 → 20 (+0 baris, 0.0% dihapus)
   ✅ T3 — Handle null (filter title/link null): 20 → 20 (+0 baris, 0.0% dihapus)

   📊 RSS Total: 20 → 20 (0 baris dihapus)

💾 Menyimpan ke Silver Delta...
   ✅ Silver RSS disimpan: /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/silver/github_rss

🧬 Demo Schema Evolution (Bonus +2)...
   📦 Batch 1 (sebelum 2026-06-04 01:59:07.808131): 120 records
   📦 Batch 2 (sesudah 2026-06-04 01:59:07.808131): 90 records
   ✅ Batch 1 ditulis (v0, tanpa _desc_length)

   📋 Schema Silver API v0:
      Kolom: ['created_at', 'description', 'forks_count', 'full_name', 'html_url', 'ingested_at', 'language', 'license', 'open_issues_count', 'owner', 'pushed_at', 'size', 'source', 'stargazers_count', 'topics', 'watchers_count', '_ingested_at', '_source', '_hour']
   ✅ Batch 2 ditulis dengan mergeSchema (v1, dengan _desc_length)

   📋 Schema Silver API v1 (setelah Schema Evolution):
      Kolom: ['created_at', 'description', 'forks_count', 'full_name', 'html_url', 'ingested_at', 'language', 'license', 'open_issues_count', 'owner', 'pushed_at', 'size', 'source', 'stargazers_count', 'topics', 'watchers_count', '_ingested_at', '_source', '_hour', '_desc_length']
      🆕 Kolom baru: ['_desc_length']

============================================================
  ✅ SILVER LAYER SELESAI
============================================================
  📦 Silver API : 210 records
  📦 Silver RSS : 20 records
  🧬 Schema Evolution: kolom _desc_length ditambahkan via mergeSchema
  📁 Output     : /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/silver/
============================================================

📋 Sample Silver API (5 baris):
+------------------------------+----------+----------------+--------------------------+-----+------------+
|                     full_name|  language|stargazers_count|               ingested_at|_hour|_desc_length|
+------------------------------+----------+----------------+--------------------------+-----+------------+
|             AITabby/opencodex|TypeScript|             215| 2026-06-04 02:00:13.74579|    2|          74|
|             AITabby/opencodex|TypeScript|             215|2026-06-04 02:01:19.765716|    2|          74|
|             AITabby/opencodex|TypeScript|             215|2026-06-04 02:02:25.578354|    2|          74|
|BarneyD66/open-warehouse-sy...|TypeScript|             249|2026-06-04 02:00:13.736782|    2|         127|
|BarneyD66/open-warehouse-sy...|TypeScript|             249|2026-06-04 02:01:19.757069|    2|         127|
+------------------------------+----------+----------------+--------------------------+-----+------------+
only showing top 5 rows

📋 Sample Silver RSS (5 baris):
+----------------------------------------+-----------------+-------------------+--------------------------+
|                                   title|           author|          published|               ingested_at|
+----------------------------------------+-----------------+-------------------+--------------------------+
|Cyberdecks are having a moment, rejec...|Amanda Silberling|2026-06-03 03:20:00|2026-06-04 01:56:04.836647|
|Cyera eyes $12B valuation at 80x ARR ...|    Marina Temkin|2026-06-03 05:50:56|2026-06-04 01:56:04.835351|
|New Microsoft tool lets devs spin up ...|         Ram Iyer|2026-06-03 02:02:21|2026-06-04 01:56:04.839678|
|Squishmallows, dentures, and an ‘I He...|  Kirsten Korosec|2026-06-03 06:25:20|2026-06-04 01:56:04.833976|
|Uber caps employee AI spending after ...|      Lucas Ropek|2026-06-03 02:11:48|2026-06-04 01:56:04.838047|
+----------------------------------------+-----------------+-------------------+--------------------------+
only showing top 5 rows


🏁 Spark session ditutup. Silver layer selesai!
(venv311) linnaeauss@yolo:/mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata$ python lakehouse/03_gold.py
Remove-Item -Recurse -Force "lakehouse\lakehouse_data\bronze"============================================================
  🥇 GOLD LAYER — Agregasi, Analisis & Time Travel
============================================================
26/06/04 09:47:44 WARN Utils: Your hostname, Deefen resolves to a loopback address: 127.0.1.1; using 10.255.255.254 instead (on interface lo)
26/06/04 09:47:44 WARN Utils: Set SPARK_LOCAL_IP if you need to bind to another address
:: loading settings :: url = jar:file:/mnt/d/Kuliah/SEMESTER%204/BIG%20DATA/ETS/kelompok-3-ets-bigdata/venv311/lib/python3.11/site-packages/pyspark/jars/ivy-2.5.1.jar!/org/apache/ivy/core/settings/ivysettings.xml
Ivy Default Cache set to: /home/deefen/.ivy2/cache
The jars for the packages stored in: /home/deefen/.ivy2/jars
io.delta#delta-spark_2.12 added as a dependency
:: resolving dependencies :: org.apache.spark#spark-submit-parent-a2b0ee5e-f5e0-433e-8be1-ff75d3a0f412;1.0
        confs: [default]
        found io.delta#delta-spark_2.12;3.1.0 in central
        found io.delta#delta-storage;3.1.0 in central
        found org.antlr#antlr4-runtime;4.9.3 in central
:: resolution report :: resolve 142ms :: artifacts dl 4ms
        :: modules in use:
        io.delta#delta-spark_2.12;3.1.0 from central in [default]
        io.delta#delta-storage;3.1.0 from central in [default]
        org.antlr#antlr4-runtime;4.9.3 from central in [default]
        ---------------------------------------------------------------------
        |                  |            modules            ||   artifacts   |
        |       conf       | number| search|dwnlded|evicted|| number|dwnlded|
        ---------------------------------------------------------------------
        |      default     |   3   |   0   |   0   |   0   ||   3   |   0   |
        ---------------------------------------------------------------------
:: retrieving :: org.apache.spark#spark-submit-parent-a2b0ee5e-f5e0-433e-8be1-ff75d3a0f412
        confs: [default]
        0 artifacts copied, 3 already retrieved (0kB/5ms)
26/06/04 09:47:45 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
Setting default log level to "WARN".
To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).

📂 Membaca Silver Delta tables...
26/06/04 09:47:56 WARN SparkStringUtils: Truncated the string representation of a plan since it was too large. This behavior can be adjusted by setting 'spark.sql.debug.maxToStringFields'.
   📦 Silver API: 210 records                                                   
   📦 Silver RSS: 20 records

────────────────────────────────────────────────────────────
📊 Gold 1: Distribusi Bahasa Pemrograman (Repro ETS)
────────────────────────────────────────────────────────────
26/06/04 09:48:00 WARN GarbageCollectionMetrics: To enable non-built-in garbage collector(s) List(G1 Concurrent GC), users should configure it(them) to spark.eventLog.gcMetrics.youngGenerationGarbageCollectors or spark.eventLog.gcMetrics.oldGenerationGarbageCollectors
+----------+----------+---------+-----------+----------+                        
|language  |repo_count|avg_stars|total_forks|percentage|
+----------+----------+---------+-----------+----------+
|Python    |12        |430.4    |1235       |40.0      |
|TypeScript|7         |605.9    |682        |23.3      |
|Unknown   |3         |441.0    |180        |10.0      |
|Rust      |2         |933.5    |401        |6.7       |
|JavaScript|1         |41675.0  |4849       |3.3       |
|C++       |1         |339.0    |27         |3.3       |
|Swift     |1         |230.0    |9          |3.3       |
|HTML      |1         |227.0    |0          |3.3       |
|PHP       |1         |227.0    |5          |3.3       |
|Shell     |1         |333.0    |9          |3.3       |
+----------+----------+---------+-----------+----------+

   ✅ Gold 1 disimpan: /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold/language_dist

────────────────────────────────────────────────────────────
⭐ Gold 2: Top 10 Repositori Berdasarkan Bintang (Repro ETS)
────────────────────────────────────────────────────────────
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
+----+--------------------------------------+----------+----------------+-----------+
|rank|full_name                             |language  |stargazers_count|forks_count|
+----+--------------------------------------+----------+----------------+-----------+
|1   |pewdiepie-archdaemon/odysseus         |JavaScript|41688           |4849       |
|2   |Gloridust/WechatOnCloud               |TypeScript|1900            |530        |
|3   |b-nnett/goose                         |Rust      |1381            |395        |
|4   |asz798838958/aBaiAutoplus             |Python    |1361            |644        |
|5   |ClaudioDrews/memory-os                |Python    |732             |71         |
|6   |cpaczek/skylight                      |TypeScript|590             |31         |
|7   |zgwl/chinese-buy-us-stock-guide       |Unknown   |561             |106        |
|8   |SenhorH/tab-labeler                   |TypeScript|519             |37         |
|9   |qiuqiubuchongle-cloud/chokepoint-atlas|Python    |510             |113        |
|10  |liyue-aigc/female-portrait-director   |Unknown   |503             |74         |
+----+--------------------------------------+----------+----------------+-----------+

26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:06 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:08 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:08 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:08 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:08 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:08 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
26/06/04 09:48:08 WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.
   ✅ Gold 2 disimpan: /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold/top_repos

────────────────────────────────────────────────────────────
🚀 Gold 3: Star Velocity — Deteksi Repo Viral (Enhanced)
────────────────────────────────────────────────────────────
+-------------------------------+----------+---------------+---------+------------+
|full_name                      |language  |total_star_gain|max_stars|observations|
+-------------------------------+----------+---------------+---------+------------+
|pewdiepie-archdaemon/odysseus  |JavaScript|48             |41688    |6           |
|cpaczek/skylight               |TypeScript|4              |590      |6           |
|zgwl/chinese-buy-us-stock-guide|Unknown   |2              |561      |6           |
|BarneyD66/open-warehouse-system|TypeScript|1              |250      |6           |
|SenhorH/tab-labeler            |TypeScript|1              |519      |6           |
|VAST-AI-Research/TripoSplat    |Python    |1              |309      |6           |
|anomalyco/rift                 |Rust      |1              |486      |6           |
|asz798838958/aBaiAutoplus      |Python    |1              |1361     |6           |
|b-nnett/goose                  |Rust      |1              |1381     |6           |
|c0deJedi/nbd-vram              |Shell     |1              |333      |6           |
+-------------------------------+----------+---------------+---------+------------+
only showing top 10 rows

   ✅ Gold 3 disimpan: /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold/star_velocity

────────────────────────────────────────────────────────────
🌱 Gold 4: Emerging Topics — Kata Kunci Baru (Enhanced)
────────────────────────────────────────────────────────────
   📅 Rentang data: 2026-06-04 01:55:50.037909 → 2026-06-04 02:02:25.578354 (0.1 jam)
   ✂️  Data < 3 jam — menggunakan median split (cutoff: 2026-06-04 01:59:07.808131)

   🌱 0 kata baru ditemukan di data terbaru:
+----+---------+
|word|frequency|
+----+---------+
+----+---------+

   ℹ️  Tidak ada kata benar-benar baru — menyimpan trending words sebagai fallback
   ✅ Gold 4 disimpan: /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold/emerging_topics

────────────────────────────────────────────────────────────
🔗 Gold 5: Cross-Source Topics — API ↔ RSS (Bonus +3)
────────────────────────────────────────────────────────────
   📦 API topics (exploded): 504 entries
   📦 RSS tags (exploded): 107 entries

   🔗 1 keyword yang overlap antara API topics dan RSS tags:
+-------+----------+-------------+---------+
|keyword|repo_count|article_count|max_stars|
+-------+----------+-------------+---------+
|ai     |1         |9            |230      |
+-------+----------+-------------+---------+

   ✅ Gold 5 disimpan: /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold/cross_source

============================================================
  🕐 TIME TRAVEL DEMO
============================================================

📜 Step 1: Delta Table History (sebelum update)
   Versi yang ada saat ini (dari 02_silver.py):
   • v0 = Batch 1 (overwrite, tanpa _desc_length)
   • v1 = Batch 1 + Batch 2 (append, dengan _desc_length via mergeSchema)
+-------+-----------------------+---------+--------------------------------------------------------------+
|version|timestamp              |operation|operationMetrics                                              |
+-------+-----------------------+---------+--------------------------------------------------------------+
|1      |2026-06-04 09:47:08.263|WRITE    |{numFiles -> 1, numOutputRows -> 90, numOutputBytes -> 15007} |
|0      |2026-06-04 09:47:06.223|WRITE    |{numFiles -> 1, numOutputRows -> 120, numOutputBytes -> 14991}|
+-------+-----------------------+---------+--------------------------------------------------------------+

📊 Step 2: Distribusi language SEBELUM update (v1 — data lengkap):
+----------+-----+
|language  |count|
+----------+-----+
|Python    |84   |
|TypeScript|49   |
|Unknown   |21   |
|Rust      |14   |
|JavaScript|7    |
|C++       |7    |
|Swift     |7    |
|HTML      |7    |
|PHP       |7    |
|Shell     |7    |
+----------+-----+

   📦 Total records (v1): 210
   📦 Records dengan language='Unknown': 21

✏️  Step 3: UPDATE language 'Unknown' → 'Not Specified'
   ✅ Update selesai — versi baru dibuat (v2)

📜 Step 4: Delta Table History (setelah update)
   • v0 = Batch 1 (overwrite)
   • v1 = Batch 1 + Batch 2 (append + mergeSchema)
   • v2 = UPDATE language 'Unknown' → 'Not Specified'
+-------+-----------------------+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|version|timestamp              |operation|operationMetrics                                                                                                                                                                                                                                                                                                                 |
+-------+-----------------------+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|2      |2026-06-04 09:48:26.241|UPDATE   |{numRemovedFiles -> 2, numRemovedBytes -> 29998, numCopiedRows -> 189, numDeletionVectorsAdded -> 0, numDeletionVectorsRemoved -> 0, numAddedChangeFiles -> 0, executionTimeMs -> 662, numDeletionVectorsUpdated -> 0, scanTimeMs -> 366, numAddedFiles -> 2, numUpdatedRows -> 21, numAddedBytes -> 30245, rewriteTimeMs -> 295}|
|1      |2026-06-04 09:47:08.263|WRITE    |{numFiles -> 1, numOutputRows -> 90, numOutputBytes -> 15007}                                                                                                                                                                                                                                                                    |
|0      |2026-06-04 09:47:06.223|WRITE    |{numFiles -> 1, numOutputRows -> 120, numOutputBytes -> 14991}                                                                                                                                                                                                                                                                   |
+-------+-----------------------+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

📊 Step 5: Distribusi language SETELAH update (v2 — terbaru):
+-------------+-----+
|language     |count|
+-------------+-----+
|Python       |84   |
|TypeScript   |49   |
|Not Specified|21   |
|Rust         |14   |
|JavaScript   |7    |
|C++          |7    |
|Swift        |7    |
|HTML         |7    |
|PHP          |7    |
|Shell        |7    |
+-------------+-----+

📊 Step 6: PERBANDINGAN Time Travel
   Metrik                                   v1 (sebelum)    v2 (sesudah)   
   ──────────────────────────────────────────────────────────────────────
   Total records                            210             210            
   language = Unknown                       21              0              
   language = Not Specified                 0               21             

   ✅ Time Travel berhasil! Data versi lama (v1) tetap bisa diakses
      menggunakan spark.read.format('delta').option('versionAsOf', 1)

============================================================
  ✅ GOLD LAYER SELESAI
============================================================
  📊 Gold 1 — language_dist    : /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold/language_dist
  ⭐ Gold 2 — top_repos        : /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold/top_repos
  🚀 Gold 3 — star_velocity    : /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold/star_velocity
  🌱 Gold 4 — emerging_topics  : /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold/emerging_topics
  🔗 Gold 5 — cross_source     : /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold/cross_source
  📁 JSON exports              : /mnt/d/Kuliah/SEMESTER 4/BIG DATA/ETS/kelompok-3-ets-bigdata/lakehouse/lakehouse_data/gold_json
  🕐 Time Travel               : v1 vs v2 berhasil ditampilkan
============================================================

🏁 Spark session ditutup. Gold layer selesai!