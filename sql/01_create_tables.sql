-- =====================================================================
-- 01_create_tables.sql   |   Oracle SQL (11g+ / XE / Live SQL)
-- Star schema for the Sales Performance Dashboard
-- Run as your own user in SQL Developer:  @01_create_tables.sql
-- =====================================================================

-- Re-runnable: drop in dependency order, ignore "table does not exist"
BEGIN
  FOR t IN (SELECT column_value AS n FROM TABLE(sys.odcivarchar2list(
              'FACT_SALES','DIM_CUSTOMER','DIM_PRODUCT','DIM_DATE','DIM_GEOGRAPHY'))) LOOP
    BEGIN EXECUTE IMMEDIATE 'DROP TABLE ' || t.n || ' CASCADE CONSTRAINTS PURGE';
    EXCEPTION WHEN OTHERS THEN NULL; END;
  END LOOP;
END;
/

CREATE TABLE dim_geography (
  geo_id   NUMBER(4)      CONSTRAINT pk_dim_geography PRIMARY KEY,
  city     VARCHAR2(50)   NOT NULL,
  state    VARCHAR2(50)   NOT NULL,
  region   VARCHAR2(20)   NOT NULL
    CONSTRAINT ck_region CHECK (region IN ('North','South','East','West','Central'))
);

CREATE TABLE dim_customer (
  customer_id    VARCHAR2(10)  CONSTRAINT pk_dim_customer PRIMARY KEY,
  customer_name  VARCHAR2(80)  NOT NULL,
  segment        VARCHAR2(20)  NOT NULL
    CONSTRAINT ck_segment CHECK (segment IN ('Consumer','Corporate','Home Office')),
  geo_id         NUMBER(4)     NOT NULL
    CONSTRAINT fk_cust_geo REFERENCES dim_geography(geo_id)
);

CREATE TABLE dim_product (
  product_id    VARCHAR2(10)  CONSTRAINT pk_dim_product PRIMARY KEY,
  product_name  VARCHAR2(100) NOT NULL,
  category      VARCHAR2(30)  NOT NULL,
  sub_category  VARCHAR2(30)  NOT NULL
);

CREATE TABLE dim_date (
  date_key     NUMBER(8)     CONSTRAINT pk_dim_date PRIMARY KEY,   -- YYYYMMDD
  full_date    DATE          NOT NULL,
  year         NUMBER(4)     NOT NULL,
  quarter      NUMBER(1)     NOT NULL,
  month_no     NUMBER(2)     NOT NULL,
  month_name   VARCHAR2(3)   NOT NULL,
  day_of_week  VARCHAR2(3)   NOT NULL,
  is_weekend   NUMBER(1)     NOT NULL CONSTRAINT ck_weekend CHECK (is_weekend IN (0,1))
);

CREATE TABLE fact_sales (
  sales_line_id   NUMBER(8)     CONSTRAINT pk_fact_sales PRIMARY KEY,
  order_id        VARCHAR2(20)  NOT NULL,
  order_date_key  NUMBER(8)     NOT NULL CONSTRAINT fk_fact_odate REFERENCES dim_date(date_key),
  ship_date_key   NUMBER(8)     NOT NULL CONSTRAINT fk_fact_sdate REFERENCES dim_date(date_key),
  customer_id     VARCHAR2(10)  NOT NULL CONSTRAINT fk_fact_cust  REFERENCES dim_customer(customer_id),
  product_id      VARCHAR2(10)  NOT NULL CONSTRAINT fk_fact_prod  REFERENCES dim_product(product_id),
  quantity        NUMBER(3)     NOT NULL CONSTRAINT ck_qty   CHECK (quantity > 0),
  unit_price      NUMBER(12,2)  NOT NULL CONSTRAINT ck_price CHECK (unit_price > 0),
  discount        NUMBER(3,2)   NOT NULL CONSTRAINT ck_disc  CHECK (discount BETWEEN 0 AND 1),
  sales           NUMBER(14,2)  NOT NULL CONSTRAINT ck_sales CHECK (sales > 0),
  profit          NUMBER(14,2)  NOT NULL
);

-- Indexes on the foreign keys used by joins / GROUP BY
CREATE INDEX ix_fact_odate ON fact_sales(order_date_key);
CREATE INDEX ix_fact_cust  ON fact_sales(customer_id);
CREATE INDEX ix_fact_prod  ON fact_sales(product_id);
CREATE INDEX ix_fact_order ON fact_sales(order_id);
