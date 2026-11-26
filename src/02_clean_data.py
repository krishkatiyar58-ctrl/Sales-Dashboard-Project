"""
02_clean_data.py
----------------
Cleans data/raw_sales.csv and produces:
  data/clean_sales.csv            - one flat clean table (use this in Power BI if you skip Oracle)
  data/rejected_rows.csv          - rows quarantined, with a reject_reason
  data/dq_summary.csv             - counts per data-quality issue
  data/star/*.csv                 - dim_geography, dim_customer, dim_product, dim_date, fact_sales
                                    (load these into Oracle with sql/sqlldr/*.ctl)
  output/expected_kpis.csv        - the numbers Oracle and Power BI must match (reconciliation)

Cleaning rules (all documented in docs/data_quality_report.md):
  R1  Exact duplicate rows                       -> removed
  R2  Mixed date formats                         -> parsed to ISO date (4 formats supported)
  R3  Impossible dates (e.g. 31-Feb)             -> quarantined
  R4  Region casing / extra spaces               -> standardised (Title Case, trimmed)
  R5  Missing region                             -> filled from state (state->region is 1:1)
  R6  Missing customer_id                        -> quarantined (cannot be attributed)
  R7  Missing sub_category                       -> filled from product_id lookup
  R8  Missing discount                           -> derived = 1 - sales / (qty * unit_price)
  R9  Negative sales                             -> quarantined (data-entry error, not a return)
  R10 Sales inconsistent with qty*price*(1-disc) -> quarantined (e.g. extra zero typed)
  R11 ship_date earlier than order_date          -> quarantined

Run:  python src/02_clean_data.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw_sales.csv"
STAR = ROOT / "data" / "star"
STAR.mkdir(parents=True, exist_ok=True)
(ROOT / "output").mkdir(exist_ok=True)

COLUMN_LIST = ["order_id", "order_date", "ship_date", "customer_id", "customer_name", "segment",
               "region", "state", "city", "product_id", "product_name", "category", "sub_category",
               "quantity", "unit_price", "discount", "sales", "profit"]

df = pd.read_csv(RAW, dtype=str)
assert list(df.columns) == COLUMN_LIST, "Column names do not match COLUMN_LIST"
raw_rows = len(df)
dq = []                                   # (rule, issue, rows_affected, action)
rejected = []                             # frames with reject_reason


def log(rule, issue, n, action):
    dq.append(dict(rule=rule, issue=issue, rows_affected=int(n), action=action))


def quarantine(mask, reason, frame):
    if mask.any():
        r = frame[mask].copy()
        r["reject_reason"] = reason
        rejected.append(r)
    return frame[~mask].copy()


log("-", "Raw rows loaded", raw_rows, "baseline")

# ---- R1 duplicates
d = df.duplicated(keep="first")
log("R1", "Exact duplicate rows", d.sum(), "Removed (first occurrence kept)")
df = df[~d].copy()

# ---- numeric typing
for c in ["quantity", "unit_price", "discount", "sales", "profit"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# ---- R2/R3 dates
def parse_dates(s):
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    fmts = ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%b %d, %Y"]
    non_iso = 0
    for i, f in enumerate(fmts):
        parsed = pd.to_datetime(s.where(out.isna()), format=f, errors="coerce")
        if i > 0:
            non_iso += parsed.notna().sum()
        out = out.fillna(parsed)
    return out, non_iso

df["order_date_p"], non_iso = parse_dates(df["order_date"])
df["ship_date_p"], _ = parse_dates(df["ship_date"])
log("R2", "Order dates in non-ISO formats (DD-MM-YYYY, YYYY/MM/DD, Mon DD, YYYY)", non_iso,
    "Parsed and converted to YYYY-MM-DD")
bad_date = df["order_date_p"].isna() | df["ship_date_p"].isna()
log("R3", "Impossible / unparseable dates (e.g. 31-02-2024)", bad_date.sum(), "Quarantined")
df = quarantine(bad_date, "R3 impossible date", df)

# ---- R4 region text
before = df["region"].copy()
df["region"] = df["region"].str.strip().str.title()
log("R4", "Region with wrong casing / extra spaces", (before.notna() & (before != df["region"])).sum(),
    "Trimmed + Title Case")

# ---- R5 region from state
state_region = (df.dropna(subset=["region"]).groupby("state")["region"].agg(lambda x: x.mode()[0]))
miss = df["region"].isna()
df.loc[miss, "region"] = df.loc[miss, "state"].map(state_region)
log("R5", "Missing region", miss.sum(), "Filled from state->region mapping")

# ---- R6 customer id
m = df["customer_id"].isna()
log("R6", "Missing customer_id", m.sum(), "Quarantined")
df = quarantine(m, "R6 missing customer_id", df)

# ---- R7 sub_category
sub_map = df.dropna(subset=["sub_category"]).drop_duplicates("product_id").set_index("product_id")["sub_category"]
m = df["sub_category"].isna()
df.loc[m, "sub_category"] = df.loc[m, "product_id"].map(sub_map)
log("R7", "Missing sub_category", m.sum(), "Filled from product_id lookup")

# ---- R9 negative sales (before R10 so reasons stay distinct)
m = df["sales"] < 0
log("R9", "Negative sales amounts", m.sum(), "Quarantined")
df = quarantine(m, "R9 negative sales", df)

# ---- R8 discount (needs sales > 0)
m = df["discount"].isna()
df.loc[m, "discount"] = (1 - df.loc[m, "sales"] / (df.loc[m, "quantity"] * df.loc[m, "unit_price"])).round(2)
log("R8", "Missing discount", m.sum(), "Derived from sales, quantity, unit_price")

# ---- R10 consistency check
expected = df["quantity"] * df["unit_price"] * (1 - df["discount"])
m = (df["sales"] - expected).abs() / expected > 0.01
log("R10", "Sales inconsistent with quantity x price x (1-discount) (outliers)", m.sum(), "Quarantined")
df = quarantine(m, "R10 sales outlier / inconsistent", df)

# ---- R11 ship before order
m = df["ship_date_p"] < df["order_date_p"]
log("R11", "ship_date earlier than order_date", m.sum(), "Quarantined")
df = quarantine(m, "R11 ship before order", df)

# ---- finalise
df["order_date"] = df["order_date_p"].dt.strftime("%Y-%m-%d")
df["ship_date"] = df["ship_date_p"].dt.strftime("%Y-%m-%d")
df = df.drop(columns=["order_date_p", "ship_date_p"])
df["quantity"] = df["quantity"].astype(int)
df["discount"] = df["discount"].round(2)
df.insert(0, "sales_line_id", np.arange(1, len(df) + 1))
df.to_csv(ROOT / "data" / "clean_sales.csv", index=False)

rej = pd.concat(rejected, ignore_index=True) if rejected else pd.DataFrame()
rej.to_csv(ROOT / "data" / "rejected_rows.csv", index=False)
log("-", "Clean rows delivered", len(df), "data/clean_sales.csv")
log("-", "Rows quarantined (all rules)", len(rej), "data/rejected_rows.csv")
pd.DataFrame(dq).to_csv(ROOT / "data" / "dq_summary.csv", index=False)

# ---------------------------------------------------------------- star schema
geo = df[["city", "state", "region"]].drop_duplicates().sort_values(["region", "state", "city"]).reset_index(drop=True)
geo.insert(0, "geo_id", np.arange(1, len(geo) + 1))
assert geo.duplicated(["city", "state"]).sum() == 0, "A city/state maps to more than one region"
cust = df[["customer_id", "customer_name", "segment", "city", "state"]].drop_duplicates("customer_id")
cust = cust.merge(geo[["geo_id", "city", "state"]], on=["city", "state"])[["customer_id", "customer_name", "segment", "geo_id"]]
prod = df[["product_id", "product_name", "category", "sub_category"]].drop_duplicates("product_id").sort_values("product_id")
dates = pd.date_range(df["order_date"].min(), df["ship_date"].max(), freq="D")
dim_date = pd.DataFrame({
    "date_key": dates.strftime("%Y%m%d").astype(int), "full_date": dates.strftime("%Y-%m-%d"),
    "year": dates.year, "quarter": dates.quarter, "month_no": dates.month,
    "month_name": dates.strftime("%b"), "day_of_week": dates.strftime("%a"),
    "is_weekend": (dates.dayofweek >= 5).astype(int)})
fact = df.assign(order_date_key=df["order_date"].str.replace("-", "").astype(int),
                 ship_date_key=df["ship_date"].str.replace("-", "").astype(int))[
    ["sales_line_id", "order_id", "order_date_key", "ship_date_key", "customer_id", "product_id",
     "quantity", "unit_price", "discount", "sales", "profit"]]
for name, t in [("dim_geography", geo), ("dim_customer", cust), ("dim_product", prod),
                ("dim_date", dim_date), ("fact_sales", fact)]:
    t.to_csv(STAR / f"{name}.csv", index=False)

# ------------------------------------------------------------ reconciliation
truth = float(Path(ROOT / "data" / "_ground_truth_total.txt").read_text()) \
    if (ROOT / "data" / "_ground_truth_total.txt").exists() else None
kpi = {
    "total_sales": df["sales"].sum(), "total_profit": df["profit"].sum(),
    "total_orders": df["order_id"].nunique(), "total_customers": df["customer_id"].nunique(),
    "units_sold": df["quantity"].sum(), "order_lines": len(df),
    "avg_order_value": df["sales"].sum() / df["order_id"].nunique(),
    "profit_margin_pct": 100 * df["profit"].sum() / df["sales"].sum(),
    "avg_discount_pct": 100 * df["discount"].mean(),
}
pd.Series(kpi, name="value").round(2).rename_axis("kpi").to_csv(ROOT / "output" / "expected_kpis.csv")
print(pd.DataFrame(dq).to_string(index=False))
print("\nKPIs:", {k: round(v, 2) for k, v in kpi.items()})
if truth:
    # sales of quarantined rows are corrupted, so compare using row-level truth only when none lost:
    print(f"\nGround-truth total before dirt injection : {truth:,.2f}")
    print(f"Clean total after cleaning               : {kpi['total_sales']:,.2f}")
    print(f"Difference (value of quarantined rows)   : {truth - kpi['total_sales']:,.2f} "
          f"({100 * (truth - kpi['total_sales']) / truth:.2f}%)")
