"""04_insights_and_charts.py - builds the PNG charts used in the report and prints insight numbers."""
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
R = Path(__file__).resolve().parents[1]; IMG = R / "docs/images"; IMG.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(R / "data/clean_sales.csv", parse_dates=["order_date"])
df["year"] = df.order_date.dt.year; df["month"] = df.order_date.dt.month
BLUE, ORG, GRY = "#1f4e79", "#e07b00", "#8c8c8c"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
cr = lambda x, _: f"₹{x/1e6:.1f}M"
from matplotlib.ticker import FuncFormatter

# 1 monthly trend by year
m = df.groupby(["year", "month"]).sales.sum().unstack(0)
ax = m.plot(figsize=(8, 4), marker="o", color=[GRY, ORG, BLUE]); ax.yaxis.set_major_formatter(FuncFormatter(cr))
ax.set_xticks(range(1, 13)); ax.set_xticklabels(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
ax.set_title("Monthly sales by year"); ax.set_xlabel(""); ax.legend(title="Year", frameon=False)
plt.tight_layout(); plt.savefig(IMG / "monthly_trend.png", dpi=150); plt.close()

# 2 top 10 products
t = df.groupby("product_name").sales.sum().nlargest(10).sort_values()
ax = t.plot.barh(figsize=(8, 4.2), color=BLUE); ax.xaxis.set_major_formatter(FuncFormatter(cr))
ax.set_title("Top 10 products by sales"); ax.set_ylabel("")
plt.tight_layout(); plt.savefig(IMG / "top10_products.png", dpi=150); plt.close()

# 3 region
r = df.groupby("region").sales.sum().sort_values(ascending=False)
ax = r.plot.bar(figsize=(6, 3.8), color=BLUE, rot=0); ax.yaxis.set_major_formatter(FuncFormatter(cr))
ax.set_title("Sales by region"); ax.set_xlabel("")
plt.tight_layout(); plt.savefig(IMG / "region_sales.png", dpi=150); plt.close()

# 4 discount vs margin
b = pd.cut(df.discount, [-.01, 0, .10, .20, .30], labels=["0%", "1-10%", "11-20%", "21-30%"])
g = df.groupby(b, observed=True).agg(s=("sales", "sum"), p=("profit", "sum")); g["margin"] = 100 * g.p / g.s
ax = g.margin.plot.bar(figsize=(6, 3.8), color=[BLUE, BLUE, ORG, "#b22222"], rot=0)
ax.axhline(0, color="black", lw=.8); ax.set_title("Profit margin % by discount band"); ax.set_xlabel("Discount")
for i, v in enumerate(g.margin): ax.text(i, v + (.6 if v >= 0 else -1.8), f"{v:.1f}%", ha="center")
plt.tight_layout(); plt.savefig(IMG / "discount_margin.png", dpi=150); plt.close()

# 5 category margin
c = df.groupby("category").agg(s=("sales", "sum"), p=("profit", "sum")); c["margin"] = 100 * c.p / c.s
fig, ax = plt.subplots(1, 2, figsize=(8, 3.6))
c.s.plot.bar(ax=ax[0], color=BLUE, rot=15); ax[0].yaxis.set_major_formatter(FuncFormatter(cr)); ax[0].set_title("Sales"); ax[0].set_xlabel("")
c.margin.plot.bar(ax=ax[1], color=ORG, rot=15); ax[1].set_title("Profit margin %"); ax[1].set_xlabel("")
plt.tight_layout(); plt.savefig(IMG / "category.png", dpi=150); plt.close()

# 6 ER / star schema diagram
fig, ax = plt.subplots(figsize=(10, 6.2)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 6.4)
def box(x, y, w, h, title, cols, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc="white", ec=color, lw=2))
    ax.add_patch(FancyBboxPatch((x, y + h - .42), w, .42, boxstyle="round,pad=0.02", fc=color, ec=color))
    ax.text(x + w/2, y + h - .21, title, ha="center", va="center", color="white", weight="bold", fontsize=10)
    for i, cname in enumerate(cols): ax.text(x + .1, y + h - .68 - i*.27, cname, fontsize=8, va="center", family="monospace")
box(3.5, 1.2, 3.0, 3.9, "FACT_SALES", ["PK sales_line_id", "   order_id", "FK order_date_key", "FK ship_date_key", "FK customer_id", "FK product_id",
    "   quantity", "   unit_price", "   discount", "   sales", "   profit"], "#1f4e79")
box(0.1, 3.9, 2.6, 1.9, "DIM_CUSTOMER", ["PK customer_id", "   customer_name", "   segment", "FK geo_id"], "#2e7d32")
box(0.1, 0.4, 2.6, 1.6, "DIM_GEOGRAPHY", ["PK geo_id", "   city", "   state", "   region"], "#2e7d32")
box(7.3, 3.9, 2.6, 1.9, "DIM_PRODUCT", ["PK product_id", "   product_name", "   category", "   sub_category"], "#2e7d32")
box(7.3, 0.4, 2.6, 2.4, "DIM_DATE", ["PK date_key (YYYYMMDD)", "   full_date", "   year / quarter", "   month_no / month_name", "   day_of_week", "   is_weekend"], "#2e7d32")
for (x1, y1, x2, y2) in [(3.5, 4.4, 2.7, 4.8), (6.5, 4.4, 7.3, 4.8), (6.5, 2.2, 7.3, 1.8), (1.4, 3.9, 1.4, 2.0)]:
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.4))
ax.text(5, 6.15, "Star schema - Sales Performance Dashboard", ha="center", fontsize=12, weight="bold")
ax.text(5, 0.3, "Arrows point from foreign key to the primary key it references", ha="center", fontsize=8, color="#555")
plt.savefig(IMG / "er_diagram.png", dpi=150, bbox_inches="tight"); plt.close()

# ----- insight numbers
y = df.groupby("year").sales.sum(); print("Yearly sales:\n", y.round(0).to_string(), "\nYoY %:", (y.pct_change()*100).round(1).tolist())
mm = df.groupby("month").sales.sum(); print("Q4 (Oct-Dec) share of sales: %.1f%%" % (100*mm[[10,11,12]].sum()/mm.sum()))
print("Best/worst month:", mm.idxmax(), mm.idxmin())
print("Top product share of sales: %.1f%%" % (100*df.groupby('product_name').sales.sum().max()/df.sales.sum()))
print("Top 3 products share: %.1f%%" % (100*df.groupby('product_name').sales.sum().nlargest(3).sum()/df.sales.sum()))
print("Region share:\n", (100*r/r.sum()).round(1).to_string())
print("Category:\n", c.round(1).to_string())
print("Discount bands:\n", g.round(1).to_string())
ll = df[df.profit < 0]; print("Loss-making lines: %d (%.1f%%), total loss %.0f" % (len(ll), 100*len(ll)/len(df), ll.profit.sum()))
print("Lines with discount>=20%%: %.1f%% of lines" % (100*(df.discount>=.2).mean()))
s = df.groupby("segment").agg(sales=("sales","sum"), cust=("customer_id","nunique")); print(s.assign(pct=100*s.sales/s.sales.sum()).round(1).to_string())
st = df.groupby("state").sales.sum().sort_values(ascending=False); print("Top 3 states:", (100*st/st.sum()).round(1).head(3).to_dict(), " Bottom 2:", (100*st/st.sum()).round(1).tail(2).to_dict())
