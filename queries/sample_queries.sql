-- =============================================================================
-- Sample Athena Queries for Invoice Analytics
-- =============================================================================
-- HOW TO USE:
--   1. Open the AWS Console → Athena
--   2. Select workgroup: invoice-analytics
--   3. Select database:  invoice_db
--   4. Paste any query below and click Run
--
-- NOTE: Replace 'invoice_db' if you changed the Glue database name.
-- NOTE: All queries use the invoices table defined in the Glue Data Catalog.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 0. CHECK THE TABLE EXISTS AND HAS DATA
-- Always start here to verify the pipeline is working.
-- -----------------------------------------------------------------------------

SELECT COUNT(*) AS total_invoices
FROM invoice_db.invoices;


-- -----------------------------------------------------------------------------
-- 1. VIEW ALL INVOICES
-- -----------------------------------------------------------------------------

SELECT *
FROM invoice_db.invoices
LIMIT 50;


-- -----------------------------------------------------------------------------
-- 2. TOTAL INVOICE VALUE AND COUNT
-- Useful for a summary KPI card on a dashboard.
-- -----------------------------------------------------------------------------

SELECT
    COUNT(*)                    AS total_invoices,
    SUM(total_amount)           AS total_value,
    AVG(total_amount)           AS average_value,
    MIN(total_amount)           AS min_invoice,
    MAX(total_amount)           AS max_invoice
FROM invoice_db.invoices;


-- -----------------------------------------------------------------------------
-- 3. SPEND BY VENDOR
-- Shows which vendors you spend the most with.
-- -----------------------------------------------------------------------------

SELECT
    vendor_name,
    COUNT(*)            AS invoice_count,
    SUM(total_amount)   AS total_spend,
    AVG(total_amount)   AS avg_invoice_value
FROM invoice_db.invoices
WHERE vendor_name IS NOT NULL
GROUP BY vendor_name
ORDER BY total_spend DESC;


-- -----------------------------------------------------------------------------
-- 4. SPEND BY CURRENCY
-- Useful when working with multiple currencies.
-- -----------------------------------------------------------------------------

SELECT
    currency,
    COUNT(*)            AS invoice_count,
    SUM(total_amount)   AS total_spend
FROM invoice_db.invoices
WHERE currency IS NOT NULL
GROUP BY currency
ORDER BY total_spend DESC;


-- -----------------------------------------------------------------------------
-- 5. MONTHLY SPEND ANALYSIS
-- Groups invoices by year-month for trend analysis.
-- This is the query that powers "spend over time" charts.
-- -----------------------------------------------------------------------------

SELECT
    DATE_FORMAT(CAST(invoice_date AS DATE), '%Y-%m')    AS month,
    COUNT(*)                                             AS invoice_count,
    SUM(total_amount)                                    AS total_spend
FROM invoice_db.invoices
WHERE invoice_date IS NOT NULL
GROUP BY DATE_FORMAT(CAST(invoice_date AS DATE), '%Y-%m')
ORDER BY month DESC;


-- -----------------------------------------------------------------------------
-- 6. INVOICES BY PAYMENT STATUS
-- -----------------------------------------------------------------------------

SELECT
    payment_status,
    COUNT(*)            AS invoice_count,
    SUM(total_amount)   AS total_value
FROM invoice_db.invoices
GROUP BY payment_status
ORDER BY invoice_count DESC;


-- -----------------------------------------------------------------------------
-- 7. OVERDUE INVOICES
-- Find invoices that are unpaid and past their due date.
-- -----------------------------------------------------------------------------

SELECT
    invoice_id,
    vendor_name,
    invoice_date,
    due_date,
    total_amount,
    currency,
    payment_status,
    DATE_DIFF('day', CAST(due_date AS DATE), CURRENT_DATE) AS days_overdue
FROM invoice_db.invoices
WHERE
    payment_status IN ('UNPAID', 'OVERDUE')
    AND due_date IS NOT NULL
    AND CAST(due_date AS DATE) < CURRENT_DATE
ORDER BY days_overdue DESC;


-- -----------------------------------------------------------------------------
-- 8. TOP 10 HIGHEST-VALUE INVOICES
-- -----------------------------------------------------------------------------

SELECT
    invoice_id,
    vendor_name,
    invoice_date,
    total_amount,
    currency,
    payment_status
FROM invoice_db.invoices
ORDER BY total_amount DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- 9. INVOICES IN A DATE RANGE
-- Replace the dates to filter by a specific period.
-- -----------------------------------------------------------------------------

SELECT
    invoice_id,
    vendor_name,
    invoice_date,
    total_amount,
    currency
FROM invoice_db.invoices
WHERE
    invoice_date IS NOT NULL
    AND CAST(invoice_date AS DATE) BETWEEN DATE '2024-01-01' AND DATE '2024-12-31'
ORDER BY invoice_date DESC;


-- -----------------------------------------------------------------------------
-- 10. LINE ITEM ANALYSIS
-- Expands the nested line_items array so you can query individual items.
-- CROSS JOIN UNNEST() "unrolls" the array — one row per line item.
-- -----------------------------------------------------------------------------

SELECT
    i.invoice_id,
    i.vendor_name,
    i.invoice_date,
    li.description     AS line_description,
    li.quantity,
    li.unit_price,
    li.line_total
FROM invoice_db.invoices i
CROSS JOIN UNNEST(i.line_items) AS t(li)
WHERE CARDINALITY(i.line_items) > 0
ORDER BY i.invoice_date DESC, li.line_total DESC;


-- -----------------------------------------------------------------------------
-- 11. TAX RATE ANALYSIS
-- Calculates the effective tax rate per invoice.
-- -----------------------------------------------------------------------------

SELECT
    invoice_id,
    vendor_name,
    subtotal,
    tax_amount,
    total_amount,
    ROUND((tax_amount / NULLIF(subtotal, 0)) * 100, 2) AS tax_rate_pct
FROM invoice_db.invoices
WHERE subtotal IS NOT NULL AND tax_amount IS NOT NULL
ORDER BY tax_rate_pct DESC;


-- -----------------------------------------------------------------------------
-- 12. INVOICES WITH MISSING DATA
-- Useful for data quality monitoring — find invoices where extraction
-- was incomplete. Good to run after first testing the pipeline.
-- -----------------------------------------------------------------------------

SELECT
    invoice_id,
    source_file,
    processed_at,
    CASE WHEN invoice_id        IS NULL THEN 'missing invoice_id '        ELSE '' END ||
    CASE WHEN vendor_name       IS NULL THEN 'missing vendor_name '       ELSE '' END ||
    CASE WHEN invoice_date      IS NULL THEN 'missing invoice_date '      ELSE '' END ||
    CASE WHEN total_amount      IS NULL THEN 'missing total_amount '      ELSE '' END
    AS missing_fields
FROM invoice_db.invoices
WHERE
    invoice_id   IS NULL
    OR vendor_name  IS NULL
    OR invoice_date IS NULL
    OR total_amount IS NULL;
