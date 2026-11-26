"""
01_generate_raw_data.py
-----------------------
Creates data/raw_sales.csv - a retail sales dataset (India, INR) with
realistic seasonality AND deliberately injected data-quality problems
(duplicates, nulls, negative amounts, mixed date formats, messy text).

NOTE: If you want to use a real Kaggle dataset (e.g. "Superstore Sales"),
skip this script, put the CSV in data/raw_sales.csv, and rename its columns
to match COLUMN LIST in 02_clean_data.py. Everything downstream is unchanged.

Run:  python src/01_generate_raw_data.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
OUT = Path(__file__).resolve().parents[1] / "data" / "raw_sales.csv"

# ------------------------------------------------------------------ masters
STATE_REGION = {
    "Delhi": "North", "Haryana": "North", "Uttar Pradesh": "North", "Punjab": "North",
    "Maharashtra": "West", "Gujarat": "West", "Rajasthan": "West",
    "Karnataka": "South", "Tamil Nadu": "South", "Telangana": "South", "Kerala": "South",
    "West Bengal": "East", "Odisha": "East", "Bihar": "East",
    "Madhya Pradesh": "Central", "Chhattisgarh": "Central",
}
STATE_CITIES = {
    "Delhi": ["New Delhi"], "Haryana": ["Gurugram", "Faridabad"],
    "Uttar Pradesh": ["Ghaziabad", "Noida", "Lucknow"], "Punjab": ["Ludhiana", "Amritsar"],
    "Maharashtra": ["Mumbai", "Pune"], "Gujarat": ["Ahmedabad", "Surat"],
    "Rajasthan": ["Jaipur", "Jodhpur"], "Karnataka": ["Bengaluru", "Mysuru"],
    "Tamil Nadu": ["Chennai", "Coimbatore"], "Telangana": ["Hyderabad"],
    "Kerala": ["Kochi"], "West Bengal": ["Kolkata"], "Odisha": ["Bhubaneswar"],
    "Bihar": ["Patna"], "Madhya Pradesh": ["Bhopal", "Indore"], "Chhattisgarh": ["Raipur"],
}
# state popularity weights (bigger metros sell more)
STATE_W = {"Maharashtra": 14, "Delhi": 11, "Karnataka": 11, "Tamil Nadu": 9, "Uttar Pradesh": 9,
           "Haryana": 7, "Gujarat": 7, "Telangana": 6, "West Bengal": 6, "Rajasthan": 4,
           "Punjab": 3, "Kerala": 3, "Madhya Pradesh": 3, "Odisha": 2, "Bihar": 2, "Chhattisgarh": 2}

# category -> sub_category -> list of (product name, base unit price INR)
CATALOG = {
    "Technology": {
        "Laptops": [("Aster Pro 14 Laptop", 62000), ("Nimbus Air 13 Laptop", 48000), ("Vertex Gaming 15", 89000)],
        "Phones": [("Zenith X5 Smartphone", 28000), ("Orbit Lite Smartphone", 14500), ("Pulse Max Smartphone", 41000)],
        "Accessories": [("Wireless Mouse W20", 899), ("Mechanical Keyboard K8", 3499),
                        ("USB-C Hub 7-in-1", 2199), ("Noise-Cancelling Headset", 5999)],
    },
    "Furniture": {
        "Chairs": [("ErgoMesh Office Chair", 8999), ("Executive Leather Chair", 15999), ("Visitor Chair Set of 2", 6499)],
        "Tables": [("Standing Desk 140cm", 18999), ("Compact Study Table", 5499), ("Conference Table 8-seat", 32999)],
        "Storage": [("Steel Filing Cabinet", 7499), ("Wooden Bookshelf 5-tier", 6999)],
    },
    "Office Supplies": {
        "Paper": [("A4 Copier Paper 500 sheets", 349), ("Premium Notebook Pack of 5", 499)],
        "Stationery": [("Gel Pen Box of 50", 450), ("Desk Organizer Set", 799), ("Whiteboard Markers Pack", 299)],
        "Printers & Ink": [("LaserJet Mono Printer", 11999), ("Ink Cartridge Black", 1299), ("Ink Cartridge Colour", 1599)],
    },
}
MARGIN = {"Technology": 0.18, "Furniture": 0.22, "Office Supplies": 0.30}
CAT_W = {"Technology": 0.40, "Furniture": 0.20, "Office Supplies": 0.40}

products = []
pid = 1000
for cat, subs in CATALOG.items():
    for sub, items in subs.items():
        for name, price in items:
            pid += 1
            products.append(dict(product_id=f"P{pid}", product_name=name, category=cat,
                                 sub_category=sub, base_price=price))
prod = pd.DataFrame(products)
# purchase weight: cheap items sell far more often than expensive ones
prod["w"] = 1.0 / np.sqrt(prod["base_price"])
prod["w"] *= prod["category"].map(CAT_W)
prod["w"] /= prod["w"].sum()

SEGMENTS = ["Consumer", "Corporate", "Home Office"]
first = ["Aarav", "Vivaan", "Aditya", "Ananya", "Diya", "Ishaan", "Kavya", "Rohan", "Saanvi", "Arjun",
         "Meera", "Rahul", "Priya", "Karan", "Neha", "Siddharth", "Pooja", "Aman", "Riya", "Vikram"]
last = ["Sharma", "Verma", "Gupta", "Singh", "Iyer", "Reddy", "Nair", "Patel", "Das", "Mehta",
        "Khan", "Joshi", "Kapoor", "Bose", "Malhotra"]

N_CUST = 900
customers = pd.DataFrame({
    "customer_id": [f"C{10000 + i}" for i in range(N_CUST)],
    "customer_name": [f"{rng.choice(first)} {rng.choice(last)}" for _ in range(N_CUST)],
    "segment": rng.choice(SEGMENTS, N_CUST, p=[0.52, 0.30, 0.18]),
})
states = list(STATE_W)
sw = np.array([STATE_W[s] for s in states], dtype=float); sw /= sw.sum()
customers["state"] = rng.choice(states, N_CUST, p=sw)
customers["city"] = [rng.choice(STATE_CITIES[s]) for s in customers["state"]]
customers["region"] = customers["state"].map(STATE_REGION)

# ------------------------------------------------------------------ orders
START, END = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-12-31")
days = pd.date_range(START, END, freq="D")
# seasonality: festive Oct-Dec peak, mild Mar spike (fiscal year end), yearly growth
month_w = {1: 0.85, 2: 0.80, 3: 1.05, 4: 0.90, 5: 0.90, 6: 0.85, 7: 0.90, 8: 1.00, 9: 1.00,
           10: 1.25, 11: 1.45, 12: 1.30}
year_w = {2023: 1.0, 2024: 1.18, 2025: 1.35}
dw = np.array([month_w[d.month] * year_w[d.year] * (1.1 if d.dayofweek >= 5 else 1.0) for d in days])
dw /= dw.sum()

N_ORDERS = 7200
order_dates = rng.choice(days, N_ORDERS, p=dw)
rows = []
for i, od in enumerate(order_dates):
    oid = f"ORD-{od.astype('datetime64[Y]').astype(int) + 1970}-{i + 1:05d}"
    cust = customers.iloc[rng.integers(0, N_CUST)]
    n_lines = int(rng.choice([1, 2, 3, 4], p=[0.50, 0.30, 0.14, 0.06]))
    chosen = rng.choice(len(prod), n_lines, replace=False, p=prod["w"].values)
    ship = pd.Timestamp(od) + pd.Timedelta(days=int(rng.integers(1, 8)))
    for ci in chosen:
        p = prod.iloc[ci]
        qty = int(rng.choice([1, 2, 3, 4, 5], p=[0.55, 0.22, 0.12, 0.07, 0.04]))
        if p.base_price > 20000:
            qty = int(rng.choice([1, 2], p=[0.9, 0.1]))
        unit = round(p.base_price * rng.uniform(0.95, 1.05), 2)
        disc = float(rng.choice([0, 0.05, 0.10, 0.20, 0.30], p=[0.50, 0.18, 0.17, 0.10, 0.05]))
        sales = round(qty * unit * (1 - disc), 2)
        # margin shrinks as discount rises; heavy discount => loss
        margin = MARGIN[p.category] - disc * 0.9 + rng.normal(0, 0.02)
        profit = round(sales * margin, 2)
        rows.append([oid, pd.Timestamp(od), ship, cust.customer_id, cust.customer_name, cust.segment,
                     cust.region, cust.state, cust.city, p.product_id, p.product_name, p.category,
                     p.sub_category, qty, unit, disc, sales, profit])

cols = ["order_id", "order_date", "ship_date", "customer_id", "customer_name", "segment", "region",
        "state", "city", "product_id", "product_name", "category", "sub_category", "quantity",
        "unit_price", "discount", "sales", "profit"]
df = pd.DataFrame(rows, columns=cols)
clean_total = df["sales"].sum()
print(f"Generated {len(df):,} order lines | {df['order_id'].nunique():,} orders | "
      f"true total sales = {clean_total:,.2f}")

# ------------------------------------------------------- inject dirty data
n = len(df)
# 1) mixed date formats (stored as text)
def fmt_dates(series):
    out = series.dt.strftime("%Y-%m-%d").astype(object)
    idx = rng.choice(len(series), int(0.04 * len(series)), replace=False)
    for k, ix in enumerate(idx):
        d = series.iloc[ix]
        out.iloc[ix] = [d.strftime("%d-%m-%Y"), d.strftime("%Y/%m/%d"), d.strftime("%b %d, %Y")][k % 3]
    bad = rng.choice(len(series), 6, replace=False)       # a few impossible dates
    for ix in bad:
        out.iloc[ix] = "31-02-2024"
    return out
df["order_date"] = fmt_dates(df["order_date"])
df["ship_date"] = df["ship_date"].dt.strftime("%Y-%m-%d")

# 2) region typos / casing / whitespace
idx = rng.choice(n, int(0.03 * n), replace=False)
def mangle(r):
    return rng.choice([r.lower(), r.upper(), " " + r, r + "  ", r.lower() + " "])
df.loc[idx, "region"] = [mangle(r) for r in df.loc[idx, "region"]]   # same region, messy spelling
# 3) missing values
for col, frac in [("region", 0.012), ("customer_id", 0.004), ("sub_category", 0.005), ("discount", 0.006)]:
    df.loc[rng.choice(n, int(frac * n), replace=False), col] = np.nan
# 4) negative / zero amounts (data-entry errors, not returns)
neg = rng.choice(n, int(0.006 * n), replace=False)
df.loc[neg, "sales"] = -df.loc[neg, "sales"].abs()
# 5) extreme outliers (extra zero typed)
out = rng.choice(n, 8, replace=False)
df.loc[out, "sales"] = df.loc[out, "sales"] * 100
# 6) exact duplicate rows
dups = df.sample(int(0.015 * n), random_state=7)
df = pd.concat([df, dups], ignore_index=True).sample(frac=1, random_state=3).reset_index(drop=True)

OUT.parent.mkdir(exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Wrote {OUT}  ({len(df):,} rows incl. injected issues)")
# keep the ground truth so we can prove the cleaning worked
Path(OUT.parent / "_ground_truth_total.txt").write_text(f"{clean_total:.2f}")
