"""Downloads the UCI Online Retail II source file (CC BY 4.0, see
../../data/README.md), combines its two sheets into
data/raw/online_retail_ii.parquet, then runs the cleaning SQL to write
data/processed/online_retail_clean.parquet. Both are gitignored.
"""

from __future__ import annotations

import io
import zipfile

import pandas as pd
import requests

from retail_analytics.engine import PROCESSED_PARQUET, RAW_PARQUET, build_connection

DATASET_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
SHEETS = ("Year 2009-2010", "Year 2010-2011")


def download_raw() -> None:
    if RAW_PARQUET.exists():
        print(f"{RAW_PARQUET} already exists, skipping download")
        return

    print(f"Downloading {DATASET_URL} ...")
    response = requests.get(DATASET_URL, timeout=120)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        xlsx_name = next(name for name in zf.namelist() if name.endswith(".xlsx"))
        xlsx_bytes = zf.read(xlsx_name)

    frames = []
    for sheet in SHEETS:
        df = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name=sheet)
        df.insert(0, "sheet", sheet)
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    for col in ("Invoice", "StockCode", "Description", "Country"):
        combined[col] = combined[col].astype(str)

    RAW_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(RAW_PARQUET, index=False)
    print(f"wrote {len(combined):,} rows to {RAW_PARQUET}")


def write_processed() -> None:
    if PROCESSED_PARQUET.exists():
        print(f"{PROCESSED_PARQUET} already exists, skipping")
        return

    con = build_connection(source_path=RAW_PARQUET)
    PROCESSED_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    con.sql(f"COPY transactions_clean TO '{PROCESSED_PARQUET.as_posix()}' (FORMAT PARQUET)")
    print(f"wrote cleaned transactions to {PROCESSED_PARQUET}")


if __name__ == "__main__":
    download_raw()
    write_processed()
