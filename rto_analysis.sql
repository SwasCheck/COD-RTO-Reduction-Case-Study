-- COD RTO Reduction: diagnostic SQL (SQLite / PostgreSQL compatible)
-- Table: orders (loaded from data/orders.csv)

-- 1. Headline KPIs
SELECT
    COUNT(*)                                        AS total_orders,
    ROUND(AVG(is_rto) * 100, 1)                     AS rto_rate_pct,
    ROUND(SUM(CASE WHEN payment_mode = 'COD' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS cod_share_pct,
    ROUND(SUM(is_rto * order_value) / 100000.0, 1)  AS gmv_lost_to_rto_lakh
FROM orders;

-- 2. RTO rate by city tier x payment mode
SELECT city_tier, payment_mode,
       COUNT(*) AS orders,
       ROUND(AVG(is_rto) * 100, 1) AS rto_rate_pct
FROM orders
GROUP BY city_tier, payment_mode
ORDER BY city_tier, payment_mode;

-- 3. Category view: where is RTO concentrated?
SELECT category,
       COUNT(*) AS orders,
       ROUND(AVG(is_rto) * 100, 1) AS rto_rate_pct,
       SUM(is_rto) AS rto_orders,
       ROUND(SUM(is_rto) * 100.0 / (SELECT SUM(is_rto) FROM orders), 1) AS share_of_all_rto_pct
FROM orders
GROUP BY category
ORDER BY rto_rate_pct DESC;

-- 4. Customer history: repeat RTO behaviour
SELECT CASE WHEN prior_orders = 0 THEN '0 New customer'
            WHEN prior_rto = 0   THEN '1 Repeat, clean history'
            WHEN prior_rto = 1   THEN '2 Repeat, 1 past RTO'
            ELSE                      '3 Repeat, 2+ past RTOs' END AS customer_segment,
       COUNT(*) AS orders,
       ROUND(AVG(is_rto) * 100, 1) AS rto_rate_pct
FROM orders
GROUP BY customer_segment
ORDER BY customer_segment;

-- 5. Address quality bands
SELECT CASE WHEN address_quality < 0.5 THEN '1 Low (<0.5)'
            WHEN address_quality < 0.75 THEN '2 Medium (0.5-0.75)'
            ELSE '3 High (0.75+)' END AS address_band,
       COUNT(*) AS orders,
       ROUND(AVG(is_rto) * 100, 1) AS rto_rate_pct
FROM orders
GROUP BY address_band
ORDER BY address_band;

-- 6. Courier performance on COD orders
SELECT courier,
       COUNT(*) AS cod_orders,
       ROUND(AVG(is_rto) * 100, 1) AS cod_rto_rate_pct,
       ROUND(AVG(delivery_attempts), 2) AS avg_attempts
FROM orders
WHERE payment_mode = 'COD'
GROUP BY courier
ORDER BY cod_rto_rate_pct DESC;

-- 7. RTO reasons mix
SELECT rto_reason,
       COUNT(*) AS rto_orders,
       ROUND(COUNT(*) * 100.0 / (SELECT SUM(is_rto) FROM orders), 1) AS pct_of_rto
FROM orders
WHERE is_rto = 1
GROUP BY rto_reason
ORDER BY rto_orders DESC;

-- 8. Monthly trend
SELECT SUBSTR(order_date, 1, 7) AS month,
       COUNT(*) AS orders,
       ROUND(AVG(is_rto) * 100, 1) AS rto_rate_pct
FROM orders
GROUP BY month
ORDER BY month;
