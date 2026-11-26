-- SQL*Loader control file for DIM_CUSTOMER
OPTIONS (SKIP=1, ERRORS=0)
LOAD DATA
INFILE '../../data/star/dim_customer.csv'
APPEND INTO TABLE dim_customer
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' TRAILING NULLCOLS
(
  customer_id, customer_name, segment, geo_id
)
