-- =====================================================================
-- 03_views.sql   |   Oracle SQL / PL/SQL
-- Views that Power BI connects to, plus a small PL/SQL validation block.
-- =====================================================================

-- Flat reporting view: one row per sales line, all attributes attached.
CREATE OR REPLACE VIEW vw_sales_flat AS
SELECT f.sales_line_id, f.order_id,
       od.full_date  AS order_date, od.year, od.quarter, od.month_no, od.month_name, od.day_of_week,
       sd.full_date  AS ship_date,
       (sd.full_date - od.full_date) AS ship_days,
       c.customer_id, c.customer_name, c.segment,
       g.region, g.state, g.city,
       p.product_id, p.product_name, p.category, p.sub_category,
       f.quantity, f.unit_price, f.discount, f.sales, f.profit
FROM   fact_sales f
JOIN   dim_date od       ON od.date_key = f.order_date_key
JOIN   dim_date sd       ON sd.date_key = f.ship_date_key
JOIN   dim_customer c    ON c.customer_id = f.customer_id
JOIN   dim_geography g   ON g.geo_id = c.geo_id
JOIN   dim_product p     ON p.product_id = f.product_id;

CREATE OR REPLACE VIEW vw_kpi_summary AS
SELECT SUM(sales)                         AS total_sales,
       SUM(profit)                        AS total_profit,
       COUNT(DISTINCT order_id)           AS total_orders,
       COUNT(DISTINCT customer_id)        AS total_customers,
       SUM(quantity)                      AS units_sold,
       SUM(sales) / COUNT(DISTINCT order_id)  AS avg_order_value,
       100 * SUM(profit) / SUM(sales)     AS profit_margin_pct
FROM   fact_sales;

CREATE OR REPLACE VIEW vw_monthly_sales AS
SELECT d.year, d.month_no, d.month_name,
       SUM(f.sales) AS monthly_sales, SUM(f.profit) AS monthly_profit,
       COUNT(DISTINCT f.order_id) AS orders
FROM   fact_sales f JOIN dim_date d ON d.date_key = f.order_date_key
GROUP  BY d.year, d.month_no, d.month_name;

CREATE OR REPLACE VIEW vw_top_products AS
SELECT p.product_name, p.category, SUM(f.sales) AS total_sales, SUM(f.profit) AS total_profit,
       RANK() OVER (ORDER BY SUM(f.sales) DESC) AS sales_rank
FROM   fact_sales f JOIN dim_product p ON p.product_id = f.product_id
GROUP  BY p.product_name, p.category;

-- ---------------------------------------------------------------------
-- PL/SQL validation block: compares the database against the expected
-- total from the Python cleaning step and reports PASS / FAIL.
-- Replace v_expected with the total_sales value in output/expected_kpis.csv
-- ---------------------------------------------------------------------
SET SERVEROUTPUT ON
DECLARE
  v_expected  NUMBER := 83017884.76;     -- <-- paste from output/expected_kpis.csv
  v_actual    NUMBER;
  v_diff_pct  NUMBER;
BEGIN
  SELECT SUM(sales) INTO v_actual FROM fact_sales;
  v_diff_pct := ABS(v_actual - v_expected) / v_expected * 100;
  DBMS_OUTPUT.PUT_LINE('Expected : ' || TO_CHAR(v_expected, '999,999,990.99'));
  DBMS_OUTPUT.PUT_LINE('Oracle   : ' || TO_CHAR(v_actual,   '999,999,990.99'));
  DBMS_OUTPUT.PUT_LINE('Diff %   : ' || TO_CHAR(v_diff_pct, '0.0000'));
  IF v_diff_pct <= 0.1 THEN
    DBMS_OUTPUT.PUT_LINE('RESULT   : PASS (within 0.1%)');
  ELSE
    DBMS_OUTPUT.PUT_LINE('RESULT   : FAIL - check the load');
  END IF;
END;
/
