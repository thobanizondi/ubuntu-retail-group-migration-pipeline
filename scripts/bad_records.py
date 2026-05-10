import duckdb # type: ignore
import logging
from datetime import datetime, timezone
from pathlib import Path

DB_PATH  = Path("db/urg_migration.duckdb")
LOG_PATH = Path("logs/bad_records.log")

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()]
)
log = logging.getLogger(__name__)


def setup_table(conn):
    conn.execute("DROP SEQUENCE IF EXISTS seq_bad_records")
    conn.execute("CREATE SEQUENCE seq_bad_records START 1")
    conn.execute("""
        CREATE OR REPLACE TABLE bad_records (
            id               INTEGER,
            source_file      VARCHAR NOT NULL,
            rejection_reason VARCHAR NOT NULL,
            rejected_at      VARCHAR NOT NULL,
            raw_record       VARCHAR NOT NULL
        )
    """)
    log.info("bad_records table ready")


def quarantine(conn, query, source_file, reason):
    ts    = datetime.now(timezone.utc).isoformat()
    count = conn.execute(f"SELECT COUNT(*) FROM ({query}) t").fetchone()[0]
    if count > 0:
        conn.execute(f"""
            INSERT INTO bad_records (id, source_file, rejection_reason, rejected_at, raw_record)
            SELECT
                nextval('seq_bad_records'),
                '{source_file}',
                '{reason}',
                '{ts}',
                CAST(t AS VARCHAR)
            FROM ({query}) t
        """)
    return count


def check_customers(conn):
    log.info("--- Checking bronze_customers ---")
    total = 0
    src   = "customers_legacy_large.csv"

    n = quarantine(conn,
        "SELECT * FROM bronze_customers WHERE customer_id IS NULL OR TRY_CAST(customer_id AS DOUBLE) IS NULL",
        src, "Null or non-numeric customer_id")
    log.info(f"  Null or invalid customer_id: {n}")
    total += n

    n = quarantine(conn,
        """SELECT * FROM bronze_customers
           WHERE signup_date IS NOT NULL
             AND TRY_STRPTIME(signup_date, '%Y-%m-%d') IS NULL
             AND TRY_STRPTIME(signup_date, '%d/%m/%Y') IS NULL
             AND TRY_STRPTIME(signup_date, '%m-%d-%Y') IS NULL""",
        src, "Unparseable signup_date")
    log.info(f"  Unparseable signup_date: {n}")
    total += n

    n = quarantine(conn,
        """SELECT * FROM bronze_customers
           WHERE UPPER(TRIM(status)) NOT IN ('ACTIVE','INACTIVE','ACT')
             AND status IS NOT NULL""",
        src, "Unresolvable status value")
    log.info(f"  Unresolvable status: {n}")
    total += n

    log.info(f"  Total customers quarantined: {total}")
    return total


def check_orders(conn):
    log.info("--- Checking bronze_orders ---")
    total = 0
    src   = "orders_legacy_large.csv"

    n = quarantine(conn,
        "SELECT * FROM bronze_orders WHERE order_id IS NULL",
        src, "Null order_id")
    log.info(f"  Null order_id: {n}")
    total += n

    n = quarantine(conn,
        "SELECT * FROM bronze_orders WHERE customer_id IS NULL",
        src, "Null customer_id")
    log.info(f"  Null customer_id: {n}")
    total += n

    n = quarantine(conn,
        """SELECT * FROM bronze_orders
           WHERE order_date IS NOT NULL
             AND order_date NOT SIMILAR TO '[0-9]{4}-[0-9]{2}-[0-9]{2}'
             AND order_date NOT SIMILAR TO '[0-9]{4}/[0-9]{2}/[0-9]{2}'
             AND order_date NOT SIMILAR TO '[0-9]{2}/[0-9]{2}/[0-9]{4}'""",
        src, "Unparseable order_date")
    log.info(f"  Unparseable order_date: {n}")
    total += n

    n = quarantine(conn,
        """SELECT * FROM bronze_orders
           WHERE UPPER(TRIM(status)) NOT IN ('COMPLETED','DONE','C','CANCELLED','CANCELED','PENDING','P')
             AND status IS NOT NULL""",
        src, "Unresolvable order status")
    log.info(f"  Unresolvable status: {n}")
    total += n

    log.info(f"  Total orders quarantined: {total}")
    return total


def check_transactions(conn):
    log.info("--- Checking bronze_transactions ---")
    total = 0
    src   = "transactions_legacy_large.csv"

    n = quarantine(conn,
        "SELECT * FROM bronze_transactions WHERE transaction_id IS NULL",
        src, "Null transaction_id")
    log.info(f"  Null transaction_id: {n}")
    total += n

    n = quarantine(conn,
        """SELECT * FROM bronze_transactions
           WHERE transaction_date IS NOT NULL
             AND TRY_STRPTIME(transaction_date, '%Y-%m-%d') IS NULL
             AND TRY_STRPTIME(transaction_date, '%d/%m/%Y') IS NULL""",
        src, "Unparseable or impossible transaction_date")
    log.info(f"  Unparseable transaction_date: {n}")
    total += n

    n = quarantine(conn,
        """SELECT * FROM bronze_transactions
           WHERE UPPER(TRIM(payment_method)) NOT IN
                 ('CARD','CC','CREDIT CARD','CASH','EFT','DEBIT CARD')
             AND payment_method IS NOT NULL""",
        src, "Unresolvable payment_method")
    log.info(f"  Unresolvable payment_method: {n}")
    total += n

    n = quarantine(conn,
        """SELECT * FROM bronze_transactions
           WHERE UPPER(TRIM(success_flag)) NOT IN ('Y','YES','1','TRUE','N','NO','0','FALSE')
             AND success_flag IS NOT NULL""",
        src, "Unresolvable success_flag")
    log.info(f"  Unresolvable success_flag: {n}")
    total += n

    log.info(f"  Total transactions quarantined: {total}")
    return total


def check_products(conn):
    log.info("--- Checking bronze_products ---")
    total = 0
    src   = "products_legacy_large.csv"

    n = quarantine(conn,
        "SELECT * FROM bronze_products WHERE product_id IS NULL",
        src, "Null product_id")
    log.info(f"  Null product_id: {n}")
    total += n

    n = quarantine(conn,
        """SELECT * FROM bronze_products
           WHERE unit_price IS NOT NULL
             AND TRY_CAST(unit_price AS DOUBLE) IS NULL""",
        src, "Unparseable unit_price")
    log.info(f"  Unparseable unit_price: {n}")
    total += n

    n = quarantine(conn,
        "SELECT * FROM bronze_products WHERE category IS NULL",
        src, "Null category")
    log.info(f"  Null category: {n}")
    total += n

    log.info(f"  Total products quarantined: {total}")
    return total


def run_bad_records():
    log.info("=" * 60)
    log.info("Bad Records Quarantine Started")
    log.info(f"DB: {DB_PATH}")
    log.info("=" * 60)

    conn = duckdb.connect(str(DB_PATH))
    setup_table(conn)

    totals = {}
    try:
        totals["customers"]    = check_customers(conn)
        totals["orders"]       = check_orders(conn)
        totals["transactions"] = check_transactions(conn)
        totals["products"]     = check_products(conn)

        log.info("")
        log.info("QUARANTINE SUMMARY")
        log.info("-" * 40)
        grand = 0
        for ds, n in totals.items():
            log.info(f"  {ds:<15}: {n:>5,} records quarantined")
            grand += n
        log.info("-" * 40)
        log.info(f"  {'TOTAL':<15}: {grand:>5,} records quarantined")
        log.info("BAD RECORDS QUARANTINE COMPLETE")
        log.info("=" * 60)

    except Exception as e:
        log.error(f"FAILED: {e}")
        raise
    finally:
        conn.close()

    return totals


if __name__ == "__main__":
    result = run_bad_records()
    print("\nSummary:", result)