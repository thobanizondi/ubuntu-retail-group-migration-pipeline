# Source to Target Mapping

**Project:** UbuntuRetailGroup_Migration
**Generated:** 2026-05-10 14:06 UTC
**Source:** System A (Legacy ERP — CSV exports)
**Target:** System B (DuckDB — Bronze / Silver / Gold)
**Architecture:** Bronze -> Silver -> Gold (dim/fact)

---

## Overview

| Layer | Purpose |
|-------|---------|
| Bronze | Raw ingestion — data loaded exactly as received from System A |
| Silver | Cleanse and conform — types cast, dates parsed, values normalised |
| Gold   | Target model — dim and fact tables ready for analytics |

---

## Customers

**Source (System A):** `urg_migration_duckdb.bronze_customers`
**Silver:** `urg_migration.main_silver.silver_customers`
**Gold (System B):** `urg_migration.main_gold.dim_customers`

| Source column | Source type | Target column | Target type | Transformation applied |
|---------------|-------------|---------------|-------------|------------------------|
| customer_id | VARCHAR | customer_id | INTEGER | TRY_CAST to INTEGER. Null or non-numeric rows quarantined. |
| full_name | VARCHAR | first_name | VARCHAR | Split on first space. Everything before = first_name. |
| full_name | VARCHAR | last_name | VARCHAR | Split on first space. Everything after = last_name. |
| email | VARCHAR | email | VARCHAR | LOWER and TRIM applied. Nulls retained as NULL. |
| phone_number | VARCHAR | phone_number | VARCHAR | TRIM applied. No further transformation. |
| signup_date | VARCHAR | signup_date | DATE | TRY_STRPTIME tried: YYYY-MM-DD, DD/MM/YYYY, MM-DD-YYYY. Unparseable dates quarantined. |
| status | VARCHAR | status | VARCHAR | ACTIVE/ACT -> Active. INACTIVE -> Inactive. Unresolvable values quarantined. |

---

## Orders

**Source (System A):** `urg_migration_duckdb.bronze_orders`
**Silver:** `urg_migration.main_silver.silver_orders`
**Gold (System B):** `urg_migration.main_gold.fact_orders`

| Source column | Source type | Target column | Target type | Transformation applied |
|---------------|-------------|---------------|-------------|------------------------|
| order_id | VARCHAR | order_id | INTEGER | TRY_CAST to INTEGER. Null rows quarantined. |
| customer_id | VARCHAR | customer_id | INTEGER | TRY_CAST to INTEGER. Rows with no matching customer removed via INNER JOIN. |
| order_date | VARCHAR | order_date | DATE | TRY_STRPTIME tried: YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY. Literals like invalid_date quarantined. |
| total_amount | VARCHAR | total_amount | DOUBLE | REGEXP_REPLACE strips R prefix. Comma decimal replaced with period. TRY_CAST to DOUBLE. |
| status | VARCHAR | status | VARCHAR | Done/C -> Completed. Cancelled -> Cancelled. Pending/P -> Pending. |
| channel | VARCHAR | channel | VARCHAR | LOWER and TRIM applied. |

---

## Transactions

**Source (System A):** `urg_migration_duckdb.bronze_transactions`
**Silver:** `urg_migration.main_silver.silver_transactions`
**Gold (System B):** `urg_migration.main_gold.fact_transactions`

| Source column | Source type | Target column | Target type | Transformation applied |
|---------------|-------------|---------------|-------------|------------------------|
| transaction_id | VARCHAR | transaction_id | INTEGER | TRY_CAST to INTEGER. Null rows quarantined. |
| order_id | VARCHAR | order_id | INTEGER | TRY_CAST to INTEGER. Rows with no matching order removed via INNER JOIN. |
| payment_method | VARCHAR | payment_method | VARCHAR | Card/CC -> Credit Card. Cash -> Cash. Crypto and unknowns quarantined. |
| transaction_amount | VARCHAR | transaction_amount | DOUBLE | TRY_CAST to DOUBLE. Nulls retained as NULL. |
| transaction_date | VARCHAR | transaction_date | DATE | TRY_STRPTIME tried: YYYY-MM-DD, DD/MM/YYYY. Impossible dates quarantined. |
| success_flag | VARCHAR | success_flag | BOOLEAN | Y/YES/1/TRUE -> TRUE. N/NO/0/FALSE -> FALSE. maybe and unknowns quarantined. |

---

## Products

**Source (System A):** `urg_migration_duckdb.bronze_products`
**Silver:** `urg_migration.main_silver.silver_products`
**Gold (System B):** `urg_migration.main_gold.dim_products`

| Source column | Source type | Target column | Target type | Transformation applied |
|---------------|-------------|---------------|-------------|------------------------|
| product_id | VARCHAR | product_id | INTEGER | TRY_CAST to INTEGER. Null rows quarantined. Deduplicated with QUALIFY ROW_NUMBER(). |
| product_name | VARCHAR | product_name | VARCHAR | TRIM applied. |
| category | VARCHAR | category | VARCHAR | Title Case: UPPER first char + LOWER rest. Null categories quarantined. |
| unit_price | VARCHAR | unit_price | DOUBLE | TRY_CAST to DOUBLE. Text values like invalid quarantined. |
| supplier_code | VARCHAR | supplier_code | VARCHAR | TRIM applied. Empty strings converted to NULL with NULLIF. |

---

## Bad records

| Source file | Records quarantined |
|-------------|---------------------|
| customers_legacy_large.csv | 2,863 |
| orders_legacy_large.csv | 1,797 |
| transactions_legacy_large.csv | 3,606 |
| products_legacy_large.csv | 487 |
| **TOTAL** | **8,753** |

---

## Validation results

| Check | Result |
|-------|--------|
| Row count reconciliation | PASS |
| Duplicate PK check | PASS |
| Null check on mandatory columns | PASS |
| Referential integrity | PASS |