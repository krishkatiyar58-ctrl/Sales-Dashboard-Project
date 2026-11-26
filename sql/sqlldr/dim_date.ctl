-- SQL*Loader control file for DIM_DATE
OPTIONS (SKIP=1, ERRORS=0)
LOAD DATA
INFILE '../../data/star/dim_date.csv'
APPEND INTO TABLE dim_date
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' TRAILING NULLCOLS
(
  date_key, full_date DATE 'YYYY-MM-DD', year, quarter, month_no, month_name, day_of_week, is_weekend
)
