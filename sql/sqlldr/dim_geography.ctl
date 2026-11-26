-- SQL*Loader control file for DIM_GEOGRAPHY
OPTIONS (SKIP=1, ERRORS=0)
LOAD DATA
INFILE '../../data/star/dim_geography.csv'
APPEND INTO TABLE dim_geography
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' TRAILING NULLCOLS
(
  geo_id, city, state, region
)
