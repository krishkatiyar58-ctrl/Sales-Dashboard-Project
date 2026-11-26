-- SQL*Loader control file for FACT_SALES
OPTIONS (SKIP=1, ERRORS=0)
LOAD DATA
INFILE '../../data/star/fact_sales.csv'
APPEND INTO TABLE fact_sales
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' TRAILING NULLCOLS
(
  sales_line_id, order_id, order_date_key, ship_date_key, customer_id, product_id, quantity, unit_price, discount, sales, profit
)
