# Data

**Source:** UCI Machine Learning Repository — [Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) (dataset id 502).

**License:** CC BY 4.0 — verified on the UCI dataset page. Redistribution with attribution is permitted, but the source file (43.5 MB `.xlsx`) is over this project's 10 MB commit budget, so it is downloaded on demand rather than committed.

**Citation:**
> Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D

**Getting the data:** `make data` downloads the source `.xlsx` from UCI, combines its two sheets ("Year 2009-2010", "Year 2010-2011") into `data/raw/online_retail_ii.parquet`, then runs the cleaning rules in `sql/00_clean.sql` and writes `data/processed/online_retail_clean.parquet`. Both are gitignored — regenerate with `make data`.

**Columns (raw):** `Invoice` (invoice number; a `C` prefix marks a cancellation), `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price` (GBP), `Customer ID`, `Country`. A UK-based online gift retailer, transactions from 2009-12-01 to 2011-12-09, ~1.07M line items across both sheets. No direct customer-identifying data beyond a numeric ID.

**Fixture (committed, <1 MB):** `data/fixtures/online_retail_ii_sample.csv` — a deterministic, stratified sample (seed `20260101`) of ~3,000 rows from the real data, built to guarantee coverage of every cleaning-rule edge case (cancelled invoices, missing customer IDs, non-product stock codes) alongside normal rows, so tests exercise real data shapes without needing the full download. See `sql/00_clean.sql` for what each edge case is and why it's excluded.
