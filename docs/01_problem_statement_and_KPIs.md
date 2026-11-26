# Problem Statement and KPI Definitions

## Business problem
A mid-sized Indian retailer selling Technology, Furniture and Office Supplies across 16 states has sales data spread over raw transaction exports. Management cannot quickly answer: **How are sales and profit trending? Which products, regions and customer segments drive revenue? Is discounting helping or hurting profit?**

## Objective
Build an end-to-end analytics solution - Python (cleaning) -> Oracle SQL (star schema and analysis) -> Power BI (interactive dashboard) - that answers these questions and whose numbers reconcile across all three tools.

## Scope
- Period: 1 Jan 2023 - 31 Dec 2025 (36 months)
- Grain: one row per order line
- Currency: Indian Rupees (INR)

## KPI definitions

| # | KPI | Definition | Formula |
|---|-----|-----------|---------|
| 1 | Total Sales | Revenue after discount | SUM(sales) |
| 2 | Total Profit | Revenue minus cost | SUM(profit) |
| 3 | Profit Margin % | Profit as a share of sales | SUM(profit) / SUM(sales) x 100 |
| 4 | Total Orders | Distinct orders placed | COUNT(DISTINCT order_id) |
| 5 | Average Order Value (AOV) | Sales per order | SUM(sales) / COUNT(DISTINCT order_id) |
| 6 | Units Sold | Items sold | SUM(quantity) |
| 7 | Active Customers | Distinct buying customers | COUNT(DISTINCT customer_id) |
| 8 | MoM Growth % | Change vs previous month | (this month - last month) / last month x 100 |
| 9 | YoY Growth % | Change vs same month last year | (this - last year) / last year x 100 |
| 10 | Discount Margin Gap | Margin of discounted lines vs undiscounted | margin(discount > 0) - margin(discount = 0) |

## Dashboard questions mapped to visuals

| Business question | Visual | SQL |
|---|---|---|
| Headline performance | 6 KPI cards | Q1 |
| Trend over time | Line chart by month, year as legend | Q2, Q7, Q8 |
| Best products | Top 10 bar chart | Q3, Q11 |
| Where do we sell | Region bar + state map/table | Q4, Q5 |
| Which categories earn | Category/sub-category margin | Q6 |
| Who buys | Segment donut | Q9 |
| Is discounting hurting | Margin by discount band | Q10 |

## Slicers
Year, Region, Category, Customer Segment (4 slicers; requirement is 3). Drill-down: Category -> Sub-category -> Product; Region -> State -> City; Year -> Quarter -> Month.
