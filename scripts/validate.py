import duckdb # type: ignore
from pathlib import Path

DB_PATH = Path("db/urg_migration.duckdb")


def header(title):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def result_row(label, value, status):
    icon = "OK" if status == "PASS" else "!!"
    print(f"  [{icon}] {label:<44} {str(value):>4}   [{status}]")


def check_row_counts(conn):
    header("CHECK 1 — Row count reconciliation")
    print(f"  {'Dataset':<15} {'Source':>8} {'Bronze':>8} {'Gold':>8} {'Dropped':>8}")
    print("  " + "-" * 52)

    datasets = [
        ("customers",    5000, "main.bronze_customers",    "main_gold.dim_customers"),
        ("orders",       5000, "main.bronze_orders",       "main_gold.fact_orders"),
        ("transactions", 5000, "main.bronze_transactions", "main_gold.fact_transactions"),
        ("products",     1000, "main.bronze_products",     "main_gold.dim_products"),
    ]

    all_pass = True
    for ds, src, btbl, gtbl in datasets:
        bc = conn.execute(f"SELECT COUNT(*) FROM {btbl}").fetchone()[0]
        gc = conn.execute(f"SELECT COUNT(*) FROM {gtbl}").fetchone()[0]
        if bc != src:
            all_pass = False
        print(f"  {ds:<15} {src:>8,} {bc:>8,} {gc:>8,} {src - gc:>8,}")

    print("  " + "-" * 52)
    print(f"\n  Bronze matches source CSV counts: [{'PASS' if all_pass else 'FAIL'}]")
    print("  Note: Silver/Gold drops are documented in bad_records table.")
    return all_pass


def check_duplicates(conn):
    header("CHECK 2 — Duplicate primary key check")

    checks = [
        ("main_gold.dim_customers",     "customer_id"),
        ("main_gold.dim_products",      "product_id"),
        ("main_gold.fact_orders",       "order_id"),
        ("main_gold.fact_transactions", "transaction_id"),
    ]

    all_pass = True
    for tbl, pk in checks:
        dupes = conn.execute(f"""
            SELECT COUNT(*) FROM (
                SELECT {pk} FROM {tbl}
                GROUP BY {pk}
                HAVING COUNT(*) > 1
            )
        """).fetchone()[0]
        status = "PASS" if dupes == 0 else "FAIL"
        if dupes > 0:
            all_pass = False
        result_row(f"{tbl.split('.')[-1]}.{pk}", dupes, status)

    return all_pass


def check_nulls(conn):
    header("CHECK 3 — Null check on mandatory columns")

    checks = [
        ("main_gold.dim_customers",     ["customer_id", "first_name", "last_name"]),
        ("main_gold.dim_products",      ["product_id", "product_name"]),
        ("main_gold.fact_orders",       ["order_id", "customer_id"]),
        ("main_gold.fact_transactions", ["transaction_id", "order_id"]),
    ]

    all_pass = True
    for tbl, cols in checks:
        tbl_short = tbl.split(".")[-1]
        for col in cols:
            nulls = conn.execute(
                f"SELECT COUNT(*) FROM {tbl} WHERE {col} IS NULL"
            ).fetchone()[0]
            status = "PASS" if nulls == 0 else "FAIL"
            if nulls > 0:
                all_pass = False
            result_row(f"{tbl_short}.{col}", nulls, status)

    return all_pass


def check_referential_integrity(conn):
    header("CHECK 4 — Referential integrity")

    all_pass = True

    n = conn.execute("""
        SELECT COUNT(*) FROM main_gold.fact_orders o
        LEFT JOIN main_gold.dim_customers c ON o.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """).fetchone()[0]
    status = "PASS" if n == 0 else "FAIL"
    if n > 0:
        all_pass = False
    result_row("Orphaned orders (no matching customer)", n, status)

    n = conn.execute("""
        SELECT COUNT(*) FROM main_gold.fact_transactions t
        LEFT JOIN main_gold.fact_orders o ON t.order_id = o.order_id
        WHERE o.order_id IS NULL
    """).fetchone()[0]
    status = "PASS" if n == 0 else "FAIL"
    if n > 0:
        all_pass = False
    result_row("Orphaned transactions (no matching order)", n, status)

    return all_pass


def run_validation():
    print()
    print("Ubuntu Retail Group Migration — Gold Layer Validation Report")
    print("Ubuntu Retail Group | System A -> System B")

    conn = duckdb.connect(str(DB_PATH))

    results = {
        "Row count reconciliation": check_row_counts(conn),
        "Duplicate PK check":       check_duplicates(conn),
        "Null check":               check_nulls(conn),
        "Referential integrity":    check_referential_integrity(conn),
    }

    conn.close()

    header("VALIDATION SUMMARY")
    overall = True
    for check, passed in results.items():
        status = "PASS" if passed else "FAIL"
        if not passed:
            overall = False
        result_row(check, "", status)

    print()
    if overall:
        print("  All checks PASSED. Migration is ready for sign-off.")
    else:
        print("  Some checks FAILED. Review output above.")
    print()


if __name__ == "__main__":
    run_validation()