-- =============================================================================
-- Sample Athena Queries — Energy Invoice Pipeline
-- =============================================================================
-- HOW TO USE:
--   1. Open the AWS Console → Athena
--   2. Select workgroup: invoice-analytics
--   3. Select database:  invoice_db
--   4. Paste any query below and click Run
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 0. VERIFY DATA IS PRESENT
-- -----------------------------------------------------------------------------

SELECT COUNT(*) AS total_invoices
FROM invoice_db.invoices;


-- -----------------------------------------------------------------------------
-- 1. ALL INVOICES — overview
-- -----------------------------------------------------------------------------

SELECT
    vendor,
    invoice_number,
    invoice_date,
    period,
    currency,
    total_amount,
    total_amount_usd,
    total_volume_kwh,
    current_pue,
    pue_cap
FROM invoice_db.invoices
ORDER BY invoice_date DESC;


-- -----------------------------------------------------------------------------
-- 2. SUMMARY KPIs
-- Total spend (USD), average invoice, total energy consumed
-- -----------------------------------------------------------------------------

SELECT
    COUNT(*)                            AS total_invoices,
    ROUND(SUM(total_amount_usd), 2)     AS total_spend_usd,
    ROUND(AVG(total_amount_usd), 2)     AS avg_invoice_usd,
    ROUND(SUM(total_volume_kwh), 2)     AS total_kwh_consumed,
    ROUND(AVG(current_pue), 4)          AS avg_pue
FROM invoice_db.invoices
WHERE total_amount_usd IS NOT NULL;


-- -----------------------------------------------------------------------------
-- 3. SPEND BY VENDOR (USD normalised)
-- Compare vendors on a like-for-like USD basis
-- -----------------------------------------------------------------------------

SELECT
    vendor,
    COUNT(*)                            AS invoice_count,
    ROUND(SUM(total_amount_usd), 2)     AS total_spend_usd,
    ROUND(AVG(total_amount_usd), 2)     AS avg_invoice_usd,
    ROUND(SUM(total_volume_kwh), 2)     AS total_kwh,
    ROUND(AVG(current_pue), 4)          AS avg_pue
FROM invoice_db.invoices
WHERE vendor IS NOT NULL
GROUP BY vendor
ORDER BY total_spend_usd DESC;


-- -----------------------------------------------------------------------------
-- 4. MONTHLY SPEND TREND (USD)
-- Useful for time-series visualisation in QuickSight
-- -----------------------------------------------------------------------------

SELECT
    period,
    COUNT(*)                            AS invoice_count,
    ROUND(SUM(total_amount_usd), 2)     AS total_spend_usd,
    ROUND(SUM(total_volume_kwh), 2)     AS total_kwh
FROM invoice_db.invoices
WHERE period IS NOT NULL
  AND total_amount_usd IS NOT NULL
GROUP BY period
ORDER BY period ASC;


-- -----------------------------------------------------------------------------
-- 5. SPEND BY CURRENCY (before USD conversion)
-- Useful to see original billing currency distribution
-- -----------------------------------------------------------------------------

SELECT
    currency,
    COUNT(*)                            AS invoice_count,
    ROUND(SUM(total_amount), 2)         AS total_local,
    ROUND(SUM(total_amount_usd), 2)     AS total_usd,
    MIN(usd_rate)                       AS usd_rate_used
FROM invoice_db.invoices
WHERE currency IS NOT NULL
GROUP BY currency
ORDER BY total_usd DESC;


-- -----------------------------------------------------------------------------
-- 6. PUE ANALYSIS
-- Monitor actual PUE vs contractual cap per vendor
-- Invoices where PUE exceeded cap are a potential billing dispute
-- -----------------------------------------------------------------------------

SELECT
    vendor,
    invoice_number,
    period,
    current_pue,
    pue_cap,
    ROUND(current_pue - pue_cap, 4)     AS pue_over_cap,
    CASE
        WHEN pue_cap IS NOT NULL AND current_pue > pue_cap THEN 'EXCEEDED'
        WHEN pue_cap IS NOT NULL AND current_pue <= pue_cap THEN 'OK'
        ELSE 'NO_CAP_DATA'
    END                                  AS pue_status
FROM invoice_db.invoices
WHERE current_pue IS NOT NULL
ORDER BY pue_over_cap DESC NULLS LAST;


-- -----------------------------------------------------------------------------
-- 7. ENERGY COST PER KWH (effective rate including PUE and tax)
-- Shows the all-in cost per kWh consumed by IT equipment
-- effective_rate = total_amount_usd / total_volume_kwh
-- -----------------------------------------------------------------------------

SELECT
    vendor,
    period,
    total_volume_kwh,
    base_rate,
    current_pue,
    total_amount_usd,
    CASE
        WHEN total_volume_kwh > 0
        THEN ROUND(total_amount_usd / total_volume_kwh, 6)
        ELSE NULL
    END                                  AS effective_usd_per_kwh
FROM invoice_db.invoices
WHERE total_volume_kwh IS NOT NULL
  AND total_amount_usd IS NOT NULL
ORDER BY period DESC;


-- -----------------------------------------------------------------------------
-- 8. VENDOR PUE TREND OVER TIME
-- Track whether a vendor's PUE is improving or worsening month over month
-- -----------------------------------------------------------------------------

SELECT
    vendor,
    period,
    current_pue,
    pue_cap,
    total_volume_kwh,
    ROUND(total_amount_usd, 2)          AS total_usd
FROM invoice_db.invoices
WHERE vendor IS NOT NULL
  AND period IS NOT NULL
  AND current_pue IS NOT NULL
ORDER BY vendor ASC, period ASC;


-- -----------------------------------------------------------------------------
-- 9. HIGH VALUE INVOICES (USD)
-- -----------------------------------------------------------------------------

SELECT
    vendor,
    invoice_number,
    invoice_date,
    period,
    currency,
    total_amount,
    total_amount_usd,
    total_volume_kwh,
    current_pue
FROM invoice_db.invoices
ORDER BY total_amount_usd DESC NULLS LAST
LIMIT 10;


-- -----------------------------------------------------------------------------
-- 10. DATA QUALITY CHECK
-- Find invoices with missing energy fields
-- -----------------------------------------------------------------------------

SELECT
    invoice_number,
    vendor,
    period,
    source_file,
    processed_at,
    CASE WHEN total_volume_kwh IS NULL THEN 'missing_kwh '    ELSE '' END ||
    CASE WHEN base_rate        IS NULL THEN 'missing_rate '   ELSE '' END ||
    CASE WHEN current_pue      IS NULL THEN 'missing_pue '    ELSE '' END ||
    CASE WHEN total_amount_usd IS NULL THEN 'missing_usd '    ELSE '' END
                                        AS missing_fields,
    CARDINALITY(data_quality_warnings)  AS warning_count
FROM invoice_db.invoices
WHERE
    total_volume_kwh IS NULL
    OR base_rate     IS NULL
    OR current_pue   IS NULL
    OR total_amount_usd IS NULL;


-- -----------------------------------------------------------------------------
-- 11. PERIOD-OVER-PERIOD SPEND CHANGE
-- Compare total USD spend between consecutive months
-- -----------------------------------------------------------------------------

WITH monthly AS (
    SELECT
        period,
        ROUND(SUM(total_amount_usd), 2) AS total_usd
    FROM invoice_db.invoices
    WHERE period IS NOT NULL
      AND total_amount_usd IS NOT NULL
    GROUP BY period
)
SELECT
    period,
    total_usd,
    LAG(total_usd) OVER (ORDER BY period)           AS prev_month_usd,
    ROUND(
        total_usd - LAG(total_usd) OVER (ORDER BY period),
    2)                                               AS change_usd,
    ROUND(
        (total_usd - LAG(total_usd) OVER (ORDER BY period))
        / NULLIF(LAG(total_usd) OVER (ORDER BY period), 0) * 100,
    1)                                               AS change_pct
FROM monthly
ORDER BY period ASC;
