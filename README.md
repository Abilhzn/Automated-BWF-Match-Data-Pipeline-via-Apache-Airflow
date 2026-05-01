# Automated-BWF-Match-Data-Pipeline-via-Apache-Airflow

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.9.0-017CEE?logo=apache-airflow)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Manipulation-150458?logo=pandas)

An end-to-end automated Data Engineering pipeline designed to extract, transform, and load (ETL) historical Badminton World Federation (BWF) match data from undocumented live-score APIs. Orchestrated fully with **Apache Airflow** and containerized using **Docker**.

---

## **Architecture Diagram**
- ``` mermaid
  graph TD
    subgraph Data Source
        API[Flashscore Live-Score API]
    end

    subgraph Config & OPSEC
        CFG((config_dag.py)) -.->|Injects X-Fsign Header & URL| EXT
    end

    subgraph Apache Airflow Environment
        EXT(PythonOperator: Data Ingestion) -->|Raw Cryptic Payload| TRF{Pandas DataFrame}
        API -->|HTTPS GET Request| EXT
        TRF -->|String Splitting ~ and ¬| CLN[Custom Data Cleansing]
        CLN -->|Filter: Empty Payload Detection| VLD{Is Data Valid?}
    end

    subgraph Local Storage
        VLD -->|Yes| CSV[(Local CSV Partitioned by Date)]
        VLD -->|No Match / ZONK| SKIP[Skip Task / Graceful Degradation]
    end
>

---

## **The Engineering Challenges & Solutions**
This project isn't just a simple web scraper. It tackles several real-world data extraction and pipeline orchestration hurdles:

1. **OPSEC & Secret Management (Hardcoded Secrets Avoidance)**
   - **Problem:** Storing sensitive API cryptographic headers (`X-Fsign`) and base URLs inside the main executable DAG exposes the project to security breaches and DMCA risks when pushed to public repositories.
   - **Solution:** Implemented module isolation by decoupling secrets into a local config_dag.py file, strictly tracked by `.gitignore`. The DAG dynamically injects these configurations at runtime via Python's `sys.path` injection.

2. **Undocumented API & Cryptographic Bypass (Security by Obscurity)**
   - **Problem:** The target data source protects its CDN endpoints with dynamic cryptographic headers to prevent bot scraping.
   - **Solution:** Reverse-engineered the network requests to isolate the hidden payload endpoint and injected the required authentication headers directly into the Python `requests` session.

3. **Custom String Delimiter Parsing (Non-Standard JSON)**
   - **Problem:** The API payload is highly compressed and does not use standard JSON formatting. Instead, it uses custom nested delimiters (`~`, `¬`, and `÷`).
   - **Solution:** Engineered a robust, multi-level Python string-parsing algorithm (O(N) complexity) to deconstruct the raw payload into a structured Pandas DataFrame.

4. **Graceful Degradation & Empty Payload Handling**
   - **Problem:** The BWF calendar contains "blank days" with no matches. Blindly scraping these days would result in corrupted 0-dimension DataFrames or empty CSV files, which is fatal for downstream Machine Learning models.
   - **Solution:** Implemented defensive programming logic to detect the absence of target match block codes (e.g., `AA÷`). The pipeline elegantly skips and logs non-match days without failing the DAG execution.

5. **Idempotent Data Ingestion**
   - **Problem:** Running Airflow backfill tasks (`catchup=True`) or manual retries can lead to data duplication.
   - **Solution:** Utilized Airflow's logical date context variables (`kwargs['ds']`) to partition the target storage, ensuring that each task run produces idempotent, partitioned `.csv` output files based on the match date.

---

## **How to Run Locally**

### Prerequisites
- Docker & Docker Compose
- Windows Subsystem for Linux (WSL 2) if running on Windows

### Setup Instructions
1. **Clone this repository:**
   ```bash
   git clone [https://github.com/Abilhzn/Automated-BWF-Match-Data-Pipeline-via-Apache-Airflow.git](https://github.com/Abilhzn/Automated-BWF-Match-Data-Pipeline-via-Apache-Airflow.git)
   cd Automated-BWF-Match-Data-Pipeline-via-Apache-Airflow
2. **Setup OPSEC Condifguration**
   Create a file named `config_dag.py` inside the `dags/` folder and insert your secrets (DO NOT commit this file):
   ```bash
   url = "GET_URL_FROM_WEBSITE"
   xfsign = "YOUR_SECRET_S_FSIGN_TOKEN_HERE"
4. **Initialize Airflow Database:**
   ```bash
   docker compose up airflow-init
5. **Spin up the Cluster:**
   ```bash
   docker compose up -d
6. **Access the Airflow UI:**
   - Open your browser and navigate to http://localhost:8080
   - Username: airflow
   - Password: airflow
7. **Trigger the Pipeline:**
   - Locate the flashscore_badminton_loop_version DAG.
   - Toggle to "Unpause" and hit the "Trigger DAG" (Play) button.
   - Watch the extracted data populate inside the /dags/ folder as structured CSV files!

---

**⚠️ Disclaimer**
This project is developed strictly for **educational** and **portfolio purposes**. The script relies on undocumented APIs which are subject to change without notice. Please respect the data provider's terms of service.
