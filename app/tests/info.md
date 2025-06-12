# ✅ MVP1 – API & Document Processing KPI Table

| **KPI**                                | **Description**                                                                 | **Target / Baseline**                     |
|----------------------------------------|----------------------------------------------------------------------------------|-------------------------------------------|
| **API Availability**                   | % of time APIs (Search, Ingestion, Result) are available (6:30–23:00)           | ≥ 99.9%                                   |
| **Search API P95 Latency**             | Time to return search results for a given query or chunk ID                     | ≤ 250 ms                                  |
| **Ingestion API P95 Latency**          | Time to accept and acknowledge a file upload request                            | ≤ 500 ms                                  |
| **Daily Document Ingestion Volume**    | Total number of documents uploaded/processed per day                            | Target: 1,000–10,000 docs/day             |
| **Peak TPS (Transactions Per Second)** | Peak transactions (uploads or queries) during highest traffic window            | ≥ 10 TPS                                  |
| **Average TPS (Daily)**                | Average transactions per second across the 6:30–23:00 window                     | 2–4 TPS (depending on load profile)       |
| **Inference Latency (Parsing)**        | Time to parse and chunk document (PDF/DOCX/Image) per page                      | ≤ 3 sec per page                          |
| **Inference Latency (Translation)**    | Time to translate one chunk using Gemini/OpenAI                                 | ≤ 1.5 sec per chunk                       |
| **Extraction Result Latency (API)**    | Time to return structured extraction/translation results via API                | ≤ 800 ms                                  |
| **Concurrent Uploads Supported**       | Number of uploads that can be processed concurrently                            | 25–50 concurrent jobs                     |
| **Concurrency - Translation Threads**  | Number of simultaneous LLM translation jobs allowed                             | 10–20 (scale with autoscaling)            |
| **Traffic Window Definition**          | Core window during which load is monitored and autoscaled                       | 06:30 to 23:00 IST (Mon–Sat)              |
| **Document Processing Mode**           | Mode of execution per document type                                             | Realtime for ≤5 pages, Batch >5, NR fallback |
| **Error Rate (API/Processing)**        | % of failed requests (timeout, 5xx, unsupported format)                         | ≤ 1%                                      |
| **Document Re-ingestion Rate**         | % of documents retried due to failure or correction                             | ≤ 2%                                      |


