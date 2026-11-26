-- SQL*Loader control file for DIM_PRODUCT
OPTIONS (SKIP=1, ERRORS=0)
LOAD DATA
INFILE '../../data/star/dim_product.csv'
APPEND INTO TABLE dim_product
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' TRAILING NULLCOLS
(
  product_id, product_name, category, sub_category
)
