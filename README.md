# UbuntuRetailGroup Migration

Data Engineering project migrating Ubuntu Retail Group (URG) from a
Legacy ERP system (System A) to a modern analytics platform (System B).

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [Data Sources](#5-data-sources)
6. [Data Quality Issues](#6-data-quality-issues)
7. [Medallion Layers](#7-medallion-layers)
8. [Gold Layer Target Model](#8-gold-layer-target-model)
9. [Bad Records Summary](#9-bad-records-summary)
10. [Validation Results](#10-validation-results)
11. [How to Run](#11-how-to-run)
12. [Pipeline Orchestration](#12-pipeline-orchestration)
13. [Deliverables](#13-deliverables)
14. [Author](#14-author)

---

## 1. Project Overview

Ubuntu Retail Group operates three business units — Home and Living,
Electronics and Wholesale. Each unit ran a separate legacy system with
no enforced data standards. Over time these systems diverged — dates
were stored in different formats, currencies had inconsistent prefixes,
categories had mixed casing and referential integrity was never enforced.

This project migrates all historical data from System A into a clean,
validated and analytics-ready System B using a Medallion architecture.
The migration is not complete until the data in System B matches what
was in System A — clean, typed and verified.

---

## 2. Architecture

```
System A (Legacy ERP)
        |
        v
   Landing Zone
   (4 CSV files)
        |
        v
     Bronze
   (raw ingestion)
   No transformations
   Adds metadata columns
        |
        v
     Silver
   (clean and conform)
   Types cast
   Dates parsed
   Values normalised
   Bad records quarantined
        |
        v
      Gold
   (dim and fact tables)
   Analytics ready
   Star Schema
        |
        v
   System B (DuckDB)
   Single source of truth
```

---

## 3. Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12 | Bronze ingestion, bad records, profiling, validation |
| DuckDB | 1.5.2 | Database engine for all 3 layers |
| dbt | 1.11.9 | Silver and Gold transformation models |
| dbt-duckdb | 1.10.1 | dbt adapter for DuckDB |
| Prefect | 3.7.0 | Pipeline orchestration |
| Prefect Cloud | — | Pipeline monitoring and dashboard |
| Git | — | Version control |

---

## 4. Project Structure

```
UbuntuRetailGroup_Migration/
|
|-- data/
|   |-- landing/
|       |-- customers_legacy_large.csv
|       |-- orders_legacy_large.csv
|       |-- transactions_legacy_large.csv
|       |-- products_legacy_large.csv
|
|-- db/
|   |-- urg_migration.duckdb
|
|-- scripts/
|   |-- bronze_ingestion.py
|   |-- bad_records.py
|   |-- profile_data.py
|   |-- validate.py
|   |-- source_to_target_mapping.py
|   |-- sqlquery.py
|
|-- dbt_project/
|   |-- models/
|   |   |-- silver/
|   |   |   |-- silver_customers.sql
|   |   |   |-- silver_orders.sql
|   |   |   |-- silver_transactions.sql
|   |   |   |-- silver_products.sql
|   |   |-- gold/
|   |       |-- dim_customers.sql
|   |       |-- dim_products.sql
|   |       |-- fact_orders.sql
|   |       |-- fact_transactions.sql
|   |-- dbt_project.yml
|   |-- profiles.yml
|   |-- models/schema.yml
|
|-- docs/
|   |-- dq_report.md
|   |-- source_to_target_mapping.md
|
|-- logs/
|   |-- bronze_ingestion.log
|   |-- bad_records.log
|
|-- pipeline.py
|-- requirements.txt
|-- .gitignore
|-- README.md
```

---

## 5. Data Sources

System A exported 4 CSV files covering the Sales, Finance and
Operations ERPs. These files are the starting point of the migration.
They are loaded into the Bronze layer unchanged.

| File | Rows | Source domain | Contents |
|------|------|---------------|---------|
| customers_legacy_large.csv | 5,000 | Sales ERP | Customer records — names, email, phone, signup date, status |
| orders_legacy_large.csv | 5,000 | Sales ERP | Order records — dates, amounts, status, channel |
| transactions_legacy_large.csv | 5,000 | Finance ERP | Payment records — amounts, method, date, success flag |
| products_legacy_large.csv | 1,000 | Operations ERP | Product records — name, category, price, supplier |

---

## 6. Data Quality Issues

The legacy system had no enforced data standards. The following issues
were found across all 4 source files and resolved in the Silver layer.

| # | Issue | Example | Resolution in Silver |
|---|-------|---------|---------------------|
| 1 | Duplicate records | Same customer_id appearing twice | ROW_NUMBER() OVER (PARTITION BY pk) |
| 2 | Null values | Missing emails, null amounts | Retain as NULL. Quarantine if on PK |
| 3 | Inconsistent date formats | 2023-13-01 and 13/12/2022 and invalid_date | TRY_STRPTIME tried across multiple formats |
| 4 | Broken referential integrity | Orders with no matching customer_id | INNER JOIN to parent removes orphans |
| 5 | Inconsistent category values | electronics and Electronics and ELECTRONICS | UPPER first char plus LOWER rest |
| 6 | Mixed data types | customer_id stored as 1.0 not 1 | All Bronze VARCHAR. TRY_CAST in Silver |
| 7 | Currency formatting | R 1777 and R1711,55 and 3608 | REGEXP_REPLACE strips R prefix. Replace comma decimal |

---

## 7. Medallion Layers

### Bronze

- Loads all 4 CSV files exactly as received from System A
- All columns stored as VARCHAR to preserve raw values
- Adds 3 metadata columns to every row

| Metadata column | Description |
|----------------|-------------|
| ingested_at | Timestamp when the record was loaded |
| source_file | Name of the CSV file the record came from |
| batch_id | Unique ID for the ingestion run |

### Silver

- Reads from Bronze tables
- Applies all cleaning and transformation rules
- Quarantines records that cannot be fixed into bad_records table
- Every cleaning decision is documented

### Gold

- Reads from Silver tables
- Writes the 4 final target tables
- Uses dim and fact naming convention for analytics readiness
- All tables pass validation before sign-off

---

## 8. Gold Layer Target Model

The Gold layer follows a Star Schema with 2 dimension tables and
2 fact tables.

| Table | Type | Primary Key | Description |
|-------|------|-------------|-------------|
| dim_customers | Dimension | customer_id | Describes who the customers are |
| dim_products | Dimension | product_id | Describes what the products are |
| fact_orders | Fact | order_id | Records order events with amounts |
| fact_transactions | Fact | transaction_id | Records payment events with amounts |

Relationships:

```
dim_customers
      |
      | customer_id
      |
fact_orders
      |
      | order_id
      |
fact_transactions

dim_products
(standalone dimension)
```

---

## 9. Bad Records Summary

Records that could not be cleaned were quarantined into the
bad_records table. They were not deleted. Each record has a
rejection_reason and rejected_at timestamp.

| Source file | Issue | Count |
|-------------|-------|-------|
| customers_legacy_large.csv | Null or invalid customer_id | 236 |
| customers_legacy_large.csv | Unparseable signup_date | 2,627 |
| orders_legacy_large.csv | Null order_id | 252 |
| orders_legacy_large.csv | Null customer_id | 483 |
| orders_legacy_large.csv | Unparseable order_date | 1,062 |
| transactions_legacy_large.csv | Null transaction_id | 231 |
| transactions_legacy_large.csv | Unparseable transaction_date | 1,267 |
| transactions_legacy_large.csv | Unresolvable payment_method | 827 |
| transactions_legacy_large.csv | Unresolvable success_flag | 1,281 |
| products_legacy_large.csv | Null product_id | 47 |
| products_legacy_large.csv | Unparseable unit_price | 237 |
| products_legacy_large.csv | Null category | 203 |
| **TOTAL** | | **8,753** |

---

## 10. Validation Results

All 4 mandatory validation checks passed before sign-off.

| Check | Description | Result |
|-------|-------------|--------|
| Row count reconciliation | Source CSV vs Bronze vs Gold counts | PASS |
| Duplicate PK check | No duplicate primary keys in Gold tables | PASS |
| Null check | Mandatory columns have no nulls in Gold | PASS |
| Referential integrity | All FK values resolve. Zero orphans | PASS |

Row counts after migration:

| Dataset | Source | Bronze | Gold | Dropped |
|---------|--------|--------|------|---------|
| customers | 5,000 | 5,000 | 4,764 | 236 |
| orders | 5,000 | 5,000 | 4,091 | 909 |
| transactions | 5,000 | 5,000 | 3,519 | 1,481 |
| products | 1,000 | 1,000 | 953 | 47 |

---

## 11. How to Run

### Prerequisites

- Python 3.12
- Git
- Git Bash (Windows)

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/your-username/UbuntuRetailGroup_Migration.git
cd UbuntuRetailGroup_Migration
```

**2. Create virtual environment**

```bash
python -m venv venv
source venv/Scripts/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Add source CSV files**

Place the 4 CSV files into the data/landing/ folder:

```
data/landing/customers_legacy_large.csv
data/landing/orders_legacy_large.csv
data/landing/transactions_legacy_large.csv
data/landing/products_legacy_large.csv
```

**5. Run the full pipeline**

```bash
python pipeline.py
```

### Running steps manually

If you want to run each step individually:

```bash
python scripts/bronze_ingestion.py
python scripts/bad_records.py
python scripts/profile_data.py
cd dbt_project
dbt run --profiles-dir .
cd ..
python scripts/validate.py
```

---

## 12. Pipeline Orchestration

The pipeline is orchestrated with Prefect. Each step is a Prefect task
with automatic retry logic. The flow enforces the correct execution order.

```
Bronze Ingestion
      |
      v
Bad Records Quarantine
      |
      v
Data Profiling
      |
      v
dbt Silver Models
      |
      v
dbt Gold Models
      |
      v
Validation
```

The pipeline is connected to Prefect Cloud for monitoring. Every run
is visible at https://app.prefect.cloud with task status, duration
and logs.

To add a daily schedule replace the last line in pipeline.py with:

```python
migration_pipeline.serve(
    name="daily-migration",
    cron="0 6 * * *"
)
```

---

## 13. Deliverables

| Deliverable | Location |
|-------------|----------|
| Bronze ingestion script | scripts/bronze_ingestion.py |
| Bad records quarantine script | scripts/bad_records.py |
| Data profiling script | scripts/profile_data.py |
| Validation script | scripts/validate.py |
| Silver dbt models | dbt_project/models/silver/ |
| Gold dbt models | dbt_project/models/gold/ |
| Source to target mapping | docs/source_to_target_mapping.md |
| Data quality report | docs/dq_report.md |
| Prefect pipeline | pipeline.py |

---

## 14. Author

**Thobani Zondi**
Data Engineering Portfolio Project
Ubuntu Retail Group — Legacy ERP Migration