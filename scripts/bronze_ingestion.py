import duckdb # type: ignore
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

LANDING_DIR = Path("data/landing")
DB_PATH     = Path("db/urg_migration.duckdb")
LOG_PATH    = Path("logs/bronze_ingestion.log")

SOURCE_FILES = {
    "bronze_customers":    "customers_legacy_large.csv",
    "bronze_orders":       "orders_legacy_large.csv",
    "bronze_transactions": "transactions_legacy_large.csv",
    "bronze_products":     "products_legacy_large.csv",
}

EXPECTED_COUNTS = {
    "bronze_customers":    5000,
    "bronze_orders":       5000,
    "bronze_transactions": 5000,
    "bronze_products":     1000,
}

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()]
)
log = logging.getLogger(__name__)


def load_csv_to_bronze(conn, table_name, filename, batch_id):
    filepath = LANDING_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Missing source file: {filepath}")
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT
            *,
            '{ts}'       AS ingested_at,
            '{filename}' AS source_file,
            '{batch_id}' AS batch_id
        FROM read_csv(
            '{filepath.as_posix()}',
            all_varchar  = true,
            header       = true,
            null_padding = true
        )
    """)
    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    log.info(f"  Loaded {count:,} rows -> {table_name}")
    return count


def run_bronze_ingestion():
    batch_id  = str(uuid.uuid4())
    run_start = datetime.now(timezone.utc)

    log.info("=" * 60)
    log.info("Bronze Ingestion Started")
    log.info(f"Batch ID  : {batch_id}")
    log.info(f"Start time: {run_start.isoformat()}")
    log.info(f"DB path   : {DB_PATH}")
    log.info("=" * 60)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))

    counts = {}
    try:
        for table_name, filename in SOURCE_FILES.items():
            log.info(f"Loading {filename} ...")
            counts[table_name] = load_csv_to_bronze(conn, table_name, filename, batch_id)

        log.info("")
        log.info("Row Count Reconciliation")
        log.info("-" * 50)
        all_match = True
        for table, expected in EXPECTED_COUNTS.items():
            actual = counts[table]
            status = "OK" if actual == expected else "MISMATCH"
            if actual != expected:
                all_match = False
            log.info(f"  {table:<25} expected={expected:>5,}  loaded={actual:>5,}  [{status}]")
        log.info("-" * 50)
        log.info("All counts match." if all_match else "MISMATCH detected.")

        log.info("")
        log.info("Column Inventory")
        for table in SOURCE_FILES:
            cols = conn.execute(f"DESCRIBE {table}").fetchdf()["column_name"].tolist()
            log.info(f"  {table}: {cols}")

        duration = (datetime.now(timezone.utc) - run_start).total_seconds()
        log.info(f"\nBRONZE INGESTION COMPLETE — {duration:.1f}s")
        log.info("=" * 60)

        return {"status": "success", "batch_id": batch_id, "counts": counts, "duration": duration}

    except Exception as e:
        log.error(f"Bronze ingestion FAILED: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    result = run_bronze_ingestion()
    print("\nSummary:", result)