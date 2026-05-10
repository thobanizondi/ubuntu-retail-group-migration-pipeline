# Data Quality Report

**Project:** UbuntuRetailGroup_Migration
**Generated:** 2026-05-10 15:03 UTC
**Engine:** DuckDB

---

## Known quality issues in System A

| # | Issue | Resolution in Silver |
|---|-------|----------------------|
| 1 | Duplicate records | ROW_NUMBER() OVER (PARTITION BY pk) |
| 2 | Null values | Retain as NULL; quarantine if on PK |
| 3 | Inconsistent date formats | TRY_STRPTIME with multiple formats |
| 4 | Broken referential integrity | INNER JOIN to parent removes orphans |
| 5 | Inconsistent category values | UPPER first char + LOWER rest |
| 6 | Mixed data types | All Bronze VARCHAR; TRY_CAST in Silver |
| 7 | Currency formatting | REGEXP_REPLACE strips R prefix |

---

## Column profile by source file

### customers_legacy_large.csv
Table: `bronze_customers` | Total rows: 5,000

| Column | Rows | Nulls | Null % | Distinct | Sample values |
|--------|------|-------|--------|----------|---------------|
| customer_id | 5,000 | 236 | 4.7% | 4,764 | `2.0`, `21.0`, `23.0`, `39.0`, `40.0` |
| full_name | 5,000 | 0 | 0.0% | 4,817 | `Christopher Reyes`, `Diane Hickman`, `William West`, `Daniel Wright`, `Jeff Howell` |
| email | 5,000 | 487 | 9.7% | 4,503 | `justin98@yahoo.com`, `jeffersonfrederick@gmail.com`, `udunlap@hotmail.com`, `ilawson@yahoo.com`, `chavezkathryn@yahoo.com` |
| phone_number | 5,000 | 0 | 0.0% | 4,485 | `invalid`, `+1-287-989-9908x3763`, `001-725-838-9397x10611`, `(484)039-8607`, `+1-372-451-9284x793` |
| signup_date | 5,000 | 991 | 19.8% | 2,947 | `1987-12-16`, `1994/01/02`, `03-02-1997`, `2012-07-05`, `2003/05/03` |
| status | 5,000 | 827 | 16.5% | 5 | `Act`, `active`, `Active`, `inactive`, `ACTIVE` |

### orders_legacy_large.csv
Table: `bronze_orders` | Total rows: 5,000

| Column | Rows | Nulls | Null % | Distinct | Sample values |
|--------|------|-------|--------|----------|---------------|
| order_id | 5,000 | 252 | 5.0% | 4,748 | `2.0`, `21.0`, `23.0`, `39.0`, `40.0` |
| customer_id | 5,000 | 483 | 9.7% | 2,955 | `4126.0`, `629.0`, `135.0`, `2185.0`, `1876.0` |
| order_date | 5,000 | 961 | 19.2% | 2,911 | `invalid_date`, `1997-10-14`, `24/08/2022`, `2000/06/08`, `1987/12/13` |
| total_amount | 5,000 | 1,016 | 20.3% | 2,767 | `R 1777`, `4585`, `R -200`, `R1269,89`, `R 4614` |
| status | 5,000 | 982 | 19.6% | 4 | `CANCELLED`, `Done`, `Completed`, `completed` |
| channel | 5,000 | 1,255 | 25.1% | 3 | `app`, `store`, `web` |

### transactions_legacy_large.csv
Table: `bronze_transactions` | Total rows: 5,000

| Column | Rows | Nulls | Null % | Distinct | Sample values |
|--------|------|-------|--------|----------|---------------|
| transaction_id | 5,000 | 231 | 4.6% | 4,769 | `6.0`, `13.0`, `16.0`, `19.0`, `22.0` |
| order_id | 5,000 | 0 | 0.0% | 2,982 | `999999`, `3035`, `3464`, `1073`, `2941` |
| payment_method | 5,000 | 838 | 16.8% | 5 | `Card`, `Crypto`, `Cash`, `CASH`, `card` |
| transaction_amount | 5,000 | 0 | 0.0% | 3,082 | `1969.248210572845`, `1925.439004018081`, `691.4783085463232`, `4308`, `2992` |
| transaction_date | 5,000 | 1,240 | 24.8% | 2,421 | `06/04/1977`, `25/02/1978`, `2005-06-07`, `26/12/1981`, `2016-12-20` |
| success_flag | 5,000 | 1,256 | 25.1% | 3 | `N`, `Y`, `maybe` |

### products_legacy_large.csv
Table: `bronze_products` | Total rows: 1,000

| Column | Rows | Nulls | Null % | Distinct | Sample values |
|--------|------|-------|--------|----------|---------------|
| product_id | 1,000 | 47 | 4.7% | 953 | `0.0`, `17.0`, `30.0`, `36.0`, `46.0` |
| product_name | 1,000 | 0 | 0.0% | 629 | `Money`, `Personal`, `Themselves`, `Crime`, `Method` |
| category | 1,000 | 203 | 20.3% | 4 | `electronics`, `Electronics`, `Home`, `HOME` |
| unit_price | 1,000 | 295 | 29.5% | 441 | `846`, `invalid`, `359.70827590154295`, `947`, `733.837816105733` |
| supplier_code | 1,000 | 346 | 34.6% | 2 | `SUP1`, `SUP2` |
