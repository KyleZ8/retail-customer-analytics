-- Cleaning rules for the Online Retail II transaction log.
-- Assumes a table/view named `transactions_raw` is already registered in the
-- DuckDB connection (see src/retail_analytics/engine.py), with the raw UCI
-- column names (Invoice, StockCode, Description, Quantity, InvoiceDate,
-- Price, "Customer ID", Country).
--
-- Every row that isn't usable for customer-level analysis (RFM, cohorts,
-- revenue concentration) is excluded here, by an explicit, named, counted
-- rule -- not a silent pandas .dropna(). removed_rows_summary (below) is
-- what notebooks/01_data_quality.ipynb reports.
--
-- Rule 1 -- cancellations: this dataset records a return/cancellation as a
-- brand-new invoice whose number is prefixed with 'C' (not a signed reversal
-- row on the original invoice). These represent stock going back, not a
-- completed sale, so they're excluded from revenue.
-- Rule 2 -- non-product stock codes: postage, bank fees, manual/test entries,
-- carriage adjustments, and gift-card denominations share the StockCode
-- column with real products but aren't merchandise sales. The blocklist
-- below was built by inspecting every non-numeric-pattern StockCode by hand
-- (68 distinct values) -- codes that are genuine (if unusually formatted)
-- products, e.g. the "DCGS####" Dotcom Gift Shop line and two-letter colour
-- suffixes like "15056BL", are deliberately NOT excluded.
-- Rule 3 -- missing customer ID: ~23% of rows have no Customer ID (likely
-- guest/unregistered checkouts). Every downstream table in this project is
-- customer-level, so these rows can't be attributed and are excluded.
-- Rule 4 -- non-positive quantity or price: residual manual/adjustment rows
-- not already caught by rules 1-3 -- not a real product sale at a real price.

CREATE OR REPLACE VIEW non_product_codes AS
SELECT unnest([
    'POST', 'DOT', 'M', 'm', 'C2', 'C3', 'D', 'S', 'BANK CHARGES', 'ADJUST',
    'ADJUST2', 'PADS', 'TEST001', 'TEST002', 'B', 'GIFT', 'CRUK'
]) AS stock_code;

CREATE OR REPLACE VIEW transactions_flagged AS
SELECT
    *,
    Invoice LIKE 'C%' AS is_cancelled,
    (
        StockCode IN (SELECT stock_code FROM non_product_codes)
        OR StockCode LIKE 'gift\_%' ESCAPE '\'
        OR StockCode LIKE '%FEE'
    ) AS is_non_product,
    "Customer ID" IS NULL AS is_missing_customer,
    (Quantity <= 0 OR Price <= 0) AS is_non_positive
FROM transactions_raw;

-- Data-quality accounting: each row lands in exactly one bucket, by the
-- first rule (in this priority order) it fails; "kept" rows are what
-- transactions_clean below carries forward.
CREATE OR REPLACE VIEW removed_rows_summary AS
SELECT
    CASE
        WHEN is_cancelled THEN 'cancelled_invoice'
        WHEN is_non_product THEN 'non_product_stock_code'
        WHEN is_missing_customer THEN 'missing_customer_id'
        WHEN is_non_positive THEN 'non_positive_quantity_or_price'
        ELSE 'kept'
    END AS removal_reason,
    COUNT(*) AS n_rows,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
FROM transactions_flagged
GROUP BY 1
ORDER BY n_rows DESC;

CREATE OR REPLACE VIEW transactions_clean AS
SELECT
    Invoice AS invoice,
    StockCode AS stock_code,
    Description AS description,
    Quantity AS quantity,
    InvoiceDate AS invoice_date,
    Price AS unit_price,
    CAST("Customer ID" AS BIGINT) AS customer_id,
    Country AS country,
    Quantity * Price AS revenue
FROM transactions_flagged
WHERE NOT is_cancelled
  AND NOT is_non_product
  AND NOT is_missing_customer
  AND NOT is_non_positive;
