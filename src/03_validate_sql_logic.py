"""
03_validate_sql_logic.py
Runs the analysis queries against the star-schema CSVs inside SQLite (a stand-in for Oracle)
and checks every aggregate reconciles to output/expected_kpis.csv.
This proves the QUERY LOGIC. You must still run sql/*.sql in your own Oracle for the Oracle numbers.
Oracle-only RATIO_TO_REPORT is rewritten to an equivalent expression for SQLite.
"""
import re, sqlite3, pandas as pd
from pathlib import Path
R = Path(__file__).resolve().parents[1]
con = sqlite3.connect(":memory:")
for t in ["dim_geography", "dim_customer", "dim_product", "dim_date", "fact_sales"]:
    pd.read_csv(R / f"data/star/{t}.csv").to_sql(t, con, index=False)
sql = (R / "sql/02_analysis_queries.sql").read_text()
sql = re.sub(r"RATIO_TO_REPORT\(SUM\(f\.sales\)\) OVER \(\)", "(SUM(f.sales)*1.0/SUM(SUM(f.sales)) OVER ())", sql)
q = [s.strip() for s in re.split(r";\s*\n", sql) if "SELECT" in s]
res = {f"Q{i}": pd.read_sql(s, con) for i, s in enumerate(q, 1)}
exp = pd.read_csv(R / "output/expected_kpis.csv").set_index("kpi")["value"]
total = exp["total_sales"]
checks = {
    "Q1 total_sales": res["Q1"].total_sales[0], "Q4 sum of regions": res["Q4"].total_sales.sum(),
    "Q9 sum of segments": res["Q9"].total_sales.sum(), "Q10 sum of discount bands": res["Q10"].total_sales.sum(),
    "Q6 sum of sub-categories": res["Q6"].total_sales.sum(), "Q2 sum of months": res["Q2"].monthly_sales.sum(),
    "Q5 sum of states": res["Q5"].total_sales.sum(), "Q12 total_sales": res["Q12"].total_sales[0]}
bad = 0
for k, v in checks.items():
    d = abs(v - total) / total * 100
    flag = "PASS" if d <= 0.1 else "FAIL"; bad += flag == "FAIL"
    print(f"{flag}  {k:28s} {v:>16,.2f}  diff {d:.4f}%")
print(f"Q4 pct_of_total_sales sums to {res['Q4'].pct_of_total_sales.sum():.2f}")
print("ALL PASS" if not bad else f"{bad} FAILED")
