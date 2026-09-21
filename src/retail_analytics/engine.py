"""DuckDB connection builder: registers the transaction source, then runs
the cleaning and business-question SQL files (sql/*.sql) in order.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = PROJECT_ROOT / "sql"
RAW_PARQUET = PROJECT_ROOT / "data" / "raw" / "online_retail_ii.parquet"
PROCESSED_PARQUET = PROJECT_ROOT / "data" / "processed" / "online_retail_clean.parquet"
FIXTURE_CSV = PROJECT_ROOT / "data" / "fixtures" / "online_retail_ii_sample.csv"

SQL_FILES = (
    "00_clean.sql",
    "01_customer_base.sql",
    "02_rfm_scores.sql",
    "03_cohort_retention.sql",
    "04_revenue_concentration.sql",
    "05_rfm_segments.sql",
)


def build_connection(source_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    """Registers `transactions_raw` from `source_path` (defaults to the full
    downloaded raw parquet if present, else the committed fixture) and runs
    every SQL file in sql/ in order, building the full view chain."""
    if source_path is None:
        source_path = RAW_PARQUET if RAW_PARQUET.exists() else FIXTURE_CSV

    con = duckdb.connect()
    if source_path.suffix == ".parquet":
        con.sql(
            "CREATE VIEW transactions_raw AS "
            f"SELECT * FROM read_parquet('{source_path.as_posix()}')"
        )
    else:
        con.sql(
            "CREATE VIEW transactions_raw AS "
            f"SELECT * FROM read_csv_auto('{source_path.as_posix()}')"
        )

    for filename in SQL_FILES:
        con.sql((SQL_DIR / filename).read_text())

    return con


if __name__ == "__main__":
    connection = build_connection()
    print(connection.sql("SELECT * FROM removed_rows_summary").df())
    print(connection.sql("SELECT * FROM revenue_concentration_summary").df())
