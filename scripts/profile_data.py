import duckdb # type: ignore
from pathlib import Path
from datetime import datetime, timezone

DB_PATH   = Path("db/urg_migration.duckdb")
DOCS_PATH = Path("docs/dq_report.md")
DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)


def profile_table(conn, table):
    total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    cols  = conn.execute(f"DESCRIBE {table}").fetchdf()["column_name"].tolist()
    cols  = [c for c in cols if c not in ("ingested_at", "source_file", "batch_id")]

    profiles = []
    for col in cols:
        nulls    = conn.execute(f'SELECT COUNT(*) FROM {table} WHERE "{col}" IS NULL').fetchone()[0]
        distinct = conn.execute(f'SELECT COUNT(DISTINCT "{col}") FROM {table} WHERE "{col}" IS NOT NULL').fetchone()[0]
        samples  = conn.execute(f'SELECT DISTINCT "{col}" FROM {table} WHERE "{col}" IS NOT NULL LIMIT 5').fetchdf().iloc[:, 0].astype(str).tolist()
        profiles.append({
            "column":   col,
            "total":    total,
            "nulls":    nulls,
            "null_pct": round(nulls / total * 100, 1) if total else 0,
            "distinct": distinct,
            "samples":  samples,
        })
    return total, profiles


def md_table(profiles):
    lines = [
        "| Column | Rows | Nulls | Null % | Distinct | Sample values |",
        "|--------|------|-------|--------|----------|---------------|"
    ]
    for p in profiles:
        samples = ", ".join(f"`{v}`" for v in p["samples"])
        lines.append(
            f"| {p['column']} | {p['total']:,} | {p['nulls']:,} | "
            f"{p['null_pct']}% | {p['distinct']:,} | {samples} |"
        )
    return "\n".join(lines)


def run_profiling():
    conn = duckdb.connect(str(DB_PATH))
    ts   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    tables = {
        "bronze_customers":    "customers_legacy_large.csv",
        "bronze_orders":       "orders_legacy_large.csv",
        "bronze_transactions": "transactions_legacy_large.csv",
        "bronze_products":     "products_legacy_large.csv",
    }

    sections = []
    for tbl, src in tables.items():
        total, profiles = profile_table(conn, tbl)
        sections.append((tbl, src, total, profiles))
    conn.close()

    lines = [
        "# Data Quality Report",
        "",
        f"**Project:** UbuntuRetailGroup_Migration",
        f"**Generated:** {ts}",
        f"**Engine:** DuckDB",
        "",
        "---",
        "",
        "## Known quality issues in System A",
        "",
        "| # | Issue | Resolution in Silver |",
        "|---|-------|----------------------|",
        "| 1 | Duplicate records | ROW_NUMBER() OVER (PARTITION BY pk) |",
        "| 2 | Null values | Retain as NULL; quarantine if on PK |",
        "| 3 | Inconsistent date formats | TRY_STRPTIME with multiple formats |",
        "| 4 | Broken referential integrity | INNER JOIN to parent removes orphans |",
        "| 5 | Inconsistent category values | UPPER first char + LOWER rest |",
        "| 6 | Mixed data types | All Bronze VARCHAR; TRY_CAST in Silver |",
        "| 7 | Currency formatting | REGEXP_REPLACE strips R prefix |",
        "",
        "---",
        "",
        "## Column profile by source file",
        "",
    ]

    for tbl, src, total, profiles in sections:
        lines += [
            f"### {src}",
            f"Table: `{tbl}` | Total rows: {total:,}",
            "",
            md_table(profiles),
            "",
        ]

    DOCS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"DQ report written to: {DOCS_PATH}")


if __name__ == "__main__":
    run_profiling()