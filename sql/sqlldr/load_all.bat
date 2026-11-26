REM Run from the sql\sqlldr folder. Replace USER/PASSWORD@XE with your Oracle login.
REM Load order matters (parents before children).
sqlldr USER/PASSWORD@XE control=dim_geography.ctl log=dim_geography.log
sqlldr USER/PASSWORD@XE control=dim_customer.ctl  log=dim_customer.log
sqlldr USER/PASSWORD@XE control=dim_product.ctl   log=dim_product.log
sqlldr USER/PASSWORD@XE control=dim_date.ctl      log=dim_date.log
sqlldr USER/PASSWORD@XE control=fact_sales.ctl    log=fact_sales.log
