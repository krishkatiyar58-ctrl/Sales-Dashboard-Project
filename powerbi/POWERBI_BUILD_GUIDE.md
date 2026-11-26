# Power BI Build Guide (about 45-60 minutes)

> **Important:** a `.pbix` file can only be created inside Power BI Desktop (Windows). It could not be generated here, so this guide gives every step, plus ready-made DAX (`measures.dax`) and a theme (`theme.json`). Your finished `.pbix` is a required deliverable that you must build and save yourself.

## Step 1 - Load the data (choose ONE)
**Option A (fastest, no Oracle needed):** Home > Get Data > Text/CSV. Load the five files in `data/star/` (fact_sales, dim_date, dim_product, dim_customer, dim_geography).
**Option B (uses Oracle, matches the project brief):** run `sql/01_create_tables.sql`, load with `sql/sqlldr/`, then Get Data > Oracle database > server `localhost/XE` > select the five tables (or `VW_SALES_FLAT`). Install the Oracle client / ODP.NET if Power BI asks.

## Step 2 - Model
Model view > confirm these one-to-many relationships (dimension side = 1):
- DIM_DATE[DATE_KEY] -> FACT_SALES[ORDER_DATE_KEY] (**active**)
- DIM_DATE[DATE_KEY] -> FACT_SALES[SHIP_DATE_KEY] (inactive)
- DIM_CUSTOMER[CUSTOMER_ID] -> FACT_SALES[CUSTOMER_ID]
- DIM_PRODUCT[PRODUCT_ID] -> FACT_SALES[PRODUCT_ID]
- DIM_GEOGRAPHY[GEO_ID] -> DIM_CUSTOMER[GEO_ID]

Mark DIM_DATE as a date table (Table tools > Mark as date table > FULL_DATE). Sort DIM_DATE[MONTH_NAME] by MONTH_NO.

## Step 3 - Measures
Paste everything from `measures.dax`. Format Total Sales / Profit / AOV as currency (Rs), margin and growth as %.

## Step 4 - Theme
View > Themes > Browse for themes > `theme.json`.

## Step 5 - Page 1: "Executive Overview"
| Position | Visual | Fields |
|---|---|---|
| Top row | 6 KPI cards | Total Sales, Total Profit, Profit Margin %, Total Orders, Avg Order Value, Active Customers |
| Left | Line chart | X: DIM_DATE[MONTH_NAME], Legend: DIM_DATE[YEAR], Y: Total Sales |
| Right | Bar chart | Y: PRODUCT_NAME, X: Total Sales, filter Top N = 10 by Total Sales |
| Bottom left | Clustered bar | Region by Total Sales (drill: Region > State > City) |
| Bottom right | Donut | Customer SEGMENT by Total Sales |
| Left edge | 4 slicers | YEAR, REGION, CATEGORY, SEGMENT |

## Step 6 - Page 2: "Profitability and Discounts"
- Matrix: CATEGORY > SUB_CATEGORY (drill-down) with Total Sales, Total Profit, Profit Margin %.
- Column chart: Discount Band (axis) vs Profit Margin % - the headline finding.
- Card: Loss-making Lines.
- Scatter: Sales (x) vs Profit (y) by product.

## Step 7 - Acceptance checklist
- [ ] At least 5 KPI cards (you have 6)
- [ ] At least 3 slicers (you have 4)
- [ ] Drill-down on category, region and date hierarchies
- [ ] Top 10 products match SQL Q3
- [ ] Monthly trend matches SQL Q2
- [ ] **Total Sales card = 83,017,884.76** (matches `output/expected_kpis.csv`, within 0.1%)

## Step 8 - Reconciliation screenshot
Put the Power BI Total Sales card, the Oracle Q12 result and `expected_kpis.csv` side by side in one screenshot and add it to your report.

## Step 9 - Demo video (2-3 minutes)
Problem statement (15s) > data pipeline (30s) > dashboard walkthrough with slicers and drill-down (90s) > two insights and recommendations (30s).
