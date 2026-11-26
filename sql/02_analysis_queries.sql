-- =====================================================================
-- 02_analysis_queries.sql   |   Oracle SQL
-- Each query answers one business question and feeds one dashboard visual.
-- =====================================================================

-- Q1. Headline KPIs (KPI cards) ----------------------------------------
SELECT ROUND(SUM(sales), 2)                                   AS total_sales,
       ROUND(SUM(profit), 2)                                  AS total_profit,
       COUNT(DISTINCT order_id)                               AS total_orders,
       COUNT(DISTINCT customer_id)                            AS total_customers,
       SUM(quantity)                                          AS units_sold,
       ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2)        AS avg_order_value,
       ROUND(100 * SUM(profit) / SUM(sales), 2)               AS profit_margin_pct
FROM   fact_sales;

-- Q2. Monthly sales trend with month-on-month growth (LAG) -------------
SELECT d.year, d.month_no, d.month_name,
       ROUND(SUM(f.sales), 2) AS monthly_sales,
       ROUND(100 * (SUM(f.sales) - LAG(SUM(f.sales)) OVER (ORDER BY d.year, d.month_no))
             / LAG(SUM(f.sales)) OVER (ORDER BY d.year, d.month_no), 2) AS mom_growth_pct
FROM   fact_sales f
JOIN   dim_date d ON d.date_key = f.order_date_key
GROUP  BY d.year, d.month_no, d.month_name
ORDER  BY d.year, d.month_no;

-- Q3. Top 10 products by sales (RANK) ----------------------------------
SELECT *
FROM  (SELECT p.product_name, p.category,
              ROUND(SUM(f.sales), 2)  AS total_sales,
              ROUND(SUM(f.profit), 2) AS total_profit,
              RANK() OVER (ORDER BY SUM(f.sales) DESC) AS sales_rank
       FROM   fact_sales f
       JOIN   dim_product p ON p.product_id = f.product_id
       GROUP  BY p.product_name, p.category)
WHERE  sales_rank <= 10
ORDER  BY sales_rank;

-- Q4. Regional performance and share of total (RATIO_TO_REPORT) --------
SELECT g.region,
       ROUND(SUM(f.sales), 2)  AS total_sales,
       ROUND(SUM(f.profit), 2) AS total_profit,
       ROUND(100 * RATIO_TO_REPORT(SUM(f.sales)) OVER (), 2) AS pct_of_total_sales
FROM   fact_sales f
JOIN   dim_customer c  ON c.customer_id = f.customer_id
JOIN   dim_geography g ON g.geo_id = c.geo_id
GROUP  BY g.region
ORDER  BY total_sales DESC;

-- Q5. State ranking inside each region (DENSE_RANK + PARTITION BY) ------
SELECT region, state, total_sales,
       DENSE_RANK() OVER (PARTITION BY region ORDER BY total_sales DESC) AS rank_in_region
FROM  (SELECT g.region, g.state, ROUND(SUM(f.sales), 2) AS total_sales
       FROM   fact_sales f
       JOIN   dim_customer c  ON c.customer_id = f.customer_id
       JOIN   dim_geography g ON g.geo_id = c.geo_id
       GROUP  BY g.region, g.state)
ORDER  BY region, rank_in_region;

-- Q6. Category / sub-category profitability ----------------------------
SELECT p.category, p.sub_category,
       ROUND(SUM(f.sales), 2)  AS total_sales,
       ROUND(SUM(f.profit), 2) AS total_profit,
       ROUND(100 * SUM(f.profit) / SUM(f.sales), 2) AS margin_pct
FROM   fact_sales f
JOIN   dim_product p ON p.product_id = f.product_id
GROUP  BY p.category, p.sub_category
ORDER  BY margin_pct DESC;

-- Q7. Year-to-date running total (cumulative window) -------------------
SELECT year, month_no, monthly_sales,
       SUM(monthly_sales) OVER (PARTITION BY year ORDER BY month_no
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_sales
FROM  (SELECT d.year, d.month_no, ROUND(SUM(f.sales), 2) AS monthly_sales
       FROM   fact_sales f
       JOIN   dim_date d ON d.date_key = f.order_date_key
       GROUP  BY d.year, d.month_no)
ORDER  BY year, month_no;

-- Q8. Year-over-year growth by month (LAG with PARTITION BY month) ------
SELECT year, month_no, monthly_sales,
       LAG(monthly_sales) OVER (PARTITION BY month_no ORDER BY year) AS same_month_last_year,
       ROUND(100 * (monthly_sales - LAG(monthly_sales) OVER (PARTITION BY month_no ORDER BY year))
             / LAG(monthly_sales) OVER (PARTITION BY month_no ORDER BY year), 2) AS yoy_growth_pct
FROM  (SELECT d.year, d.month_no, ROUND(SUM(f.sales), 2) AS monthly_sales
       FROM   fact_sales f
       JOIN   dim_date d ON d.date_key = f.order_date_key
       GROUP  BY d.year, d.month_no)
ORDER  BY month_no, year;

-- Q9. Customer segment contribution ------------------------------------
SELECT c.segment,
       COUNT(DISTINCT f.customer_id) AS customers,
       ROUND(SUM(f.sales), 2)        AS total_sales,
       ROUND(SUM(f.sales) / COUNT(DISTINCT f.order_id), 2) AS avg_order_value
FROM   fact_sales f
JOIN   dim_customer c ON c.customer_id = f.customer_id
GROUP  BY c.segment
ORDER  BY total_sales DESC;

-- Q10. Does discounting hurt profit? (conditional aggregation) ---------
SELECT CASE WHEN discount = 0      THEN '0%  (none)'
            WHEN discount <= 0.10  THEN '1-10%'
            WHEN discount <= 0.20  THEN '11-20%'
            ELSE                        '21-30%' END AS discount_band,
       COUNT(*)                                       AS order_lines,
       ROUND(SUM(sales), 2)                           AS total_sales,
       ROUND(SUM(profit), 2)                          AS total_profit,
       ROUND(100 * SUM(profit) / SUM(sales), 2)       AS margin_pct,
       SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END)    AS loss_making_lines
FROM   fact_sales
GROUP  BY CASE WHEN discount = 0      THEN '0%  (none)'
               WHEN discount <= 0.10  THEN '1-10%'
               WHEN discount <= 0.20  THEN '11-20%'
               ELSE                        '21-30%' END
ORDER  BY MIN(discount);

-- Q11. Top 3 products inside each category (DENSE_RANK per category) ----
SELECT category, product_name, total_sales, rnk
FROM  (SELECT p.category, p.product_name, ROUND(SUM(f.sales), 2) AS total_sales,
              DENSE_RANK() OVER (PARTITION BY p.category ORDER BY SUM(f.sales) DESC) AS rnk
       FROM   fact_sales f
       JOIN   dim_product p ON p.product_id = f.product_id
       GROUP  BY p.category, p.product_name)
WHERE  rnk <= 3
ORDER  BY category, rnk;

-- Q12. RECONCILIATION - compare these numbers with output/expected_kpis.csv
--      and with the Power BI KPI cards. All three must agree within 0.1%.
SELECT COUNT(*)                    AS row_count,
       ROUND(SUM(sales), 2)        AS total_sales,
       ROUND(SUM(profit), 2)       AS total_profit,
       COUNT(DISTINCT order_id)    AS orders
FROM   fact_sales;
