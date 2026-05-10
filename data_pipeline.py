import subprocess
import sys
import logging
from pathlib import Path
from prefect import flow, task, get_run_logger # type: ignore

PROJECT_ROOT = Path(".")
DBT_DIR      = PROJECT_ROOT / "dbt_project"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


@task(name="Bronze Ingestion", retries=1)
def bronze_ingestion():
    logger = get_run_logger()
    logger.info("Starting Bronze ingestion...")
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from bronze_ingestion import run_bronze_ingestion # type: ignore
    result = run_bronze_ingestion()
    logger.info(f"Bronze complete. Counts: {result['counts']}")
    return result


@task(name="Bad Records Quarantine", retries=1)
def bad_records():
    logger = get_run_logger()
    logger.info("Starting bad records quarantine...")
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from bad_records import run_bad_records # type: ignore
    result = run_bad_records()
    logger.info(f"Bad records complete. Summary: {result}")
    return result


@task(name="Data Profiling", retries=1)
def profile_data():
    logger = get_run_logger()
    logger.info("Starting data profiling...")
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from profile_data import run_profiling # type: ignore
    result = run_profiling()
    logger.info(f"Profiling complete. Report written to: {result}")
    return result


@task(name="dbt Silver Models", retries=1)
def dbt_silver():
    logger = get_run_logger()
    logger.info("Running dbt Silver models...")
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", ".", "--select", "silver.*"],
        cwd=str(DBT_DIR),
        capture_output=True,
        text=True
    )
    logger.info(result.stdout[-2000:])
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError("dbt Silver run failed")
    logger.info("Silver models complete.")
    return {"status": "success", "layer": "silver"}


@task(name="dbt Gold Models", retries=1)
def dbt_gold():
    logger = get_run_logger()
    logger.info("Running dbt Gold models...")
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", ".", "--select", "gold.*"],
        cwd=str(DBT_DIR),
        capture_output=True,
        text=True
    )
    logger.info(result.stdout[-2000:])
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError("dbt Gold run failed")
    logger.info("Gold models complete.")
    return {"status": "success", "layer": "gold"}


@task(name="Validation")
def validate():
    logger = get_run_logger()
    logger.info("Running validation checks...")
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from validate import run_validation # type: ignore
    result = run_validation()
    if result is None:
        result = {}
    all_passed = all(result.values()) if result else False
    if all_passed:
        logger.info("All validation checks PASSED.")
    else:
        logger.warning("Some validation checks FAILED.")
    return result if result else {"status": "completed"}


@flow(name="UbuntuRetailGroup Migration Pipeline")
def migration_pipeline():
    print("")
    print("=" * 60)
    print("  UbuntuRetailGroup Migration Pipeline")
    print("  Ubuntu Retail Group | System A -> System B")
    print("=" * 60)
    print("")

    bronze_result  = bronze_ingestion()
    bad_result     = bad_records(wait_for=[bronze_result])
    profile_result = profile_data(wait_for=[bad_result])
    silver_result  = dbt_silver(wait_for=[profile_result])
    gold_result    = dbt_gold(wait_for=[silver_result])
    val_result     = validate(wait_for=[gold_result])

    print("")
    print("=" * 60)
    print("  Pipeline Complete")
    print("=" * 60)
    print("")

    return {
        "bronze":      bronze_result,
        "bad_records": bad_result,
        "profiling":   profile_result,
        "silver":      silver_result,
        "gold":        gold_result,
        "validation":  val_result,
    }


if __name__ == "__main__":
    migration_pipeline()