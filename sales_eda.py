import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ----- PATHS (tailored to your machine) -----
PROJECT_DIR = Path(r"C:\Users\Santhosh\OneDrive\Desktop\projects\Global Sales Performance Dashboard")
DATA_FILE   = PROJECT_DIR / r"dataset\Global_Superstore2.csv"
OUT_DIR     = PROJECT_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ----- READ DATA -----
# If you hit a UnicodeDecodeError, change to: encoding="utf-8-sig"
df = pd.read_csv(DATA_FILE, encoding="latin1")


# ----- COLUMN COMPATIBILITY LAYER -----
# Many Superstore variants use slightly different capitalization/spacing.
# We normalize names to lower-case and map common variants.
orig_cols = df.columns.tolist()
lower = {c.lower().strip(): c for c in df.columns}

def pick(*cands):
    """Return the first existing column from candidate names (lowercase comparison)."""
    for c in cands:
        if c in lower:
            return lower[c]
    raise KeyError(f"Missing required column. Tried: {cands}")

# Map required columns with common fallbacks
col_order_id   = pick("order id", "order_id")
col_order_date = pick("order date", "order_date")
col_ship_date  = pick("ship date", "ship_date")
col_country    = pick("country")
col_region     = pick("region")
col_segment    = pick("segment")
col_category   = pick("category")
col_subcat     = pick("sub-category", "sub_category", "subcategory")
col_product    = pick("product name", "product_name")
col_sales      = pick("sales")
col_qty        = pick("quantity", "qty")
col_discount   = pick("discount")
col_profit     = pick("profit")

# Parse dates safely
for dcol in [col_order_date, col_ship_date]:
    df[dcol] = pd.to_datetime(df[dcol], errors="coerce", dayfirst=True)


# Basic cleaning
df = df.dropna(subset=[col_sales, col_profit, col_order_date]).copy()

# Derived time columns
df["year"]  = df[col_order_date].dt.year
df["month"] = df[col_order_date].dt.to_period("M").astype(str)

# ----- KPIs -----
kpis = {
    "total_sales": float(df[col_sales].sum()),
    "total_profit": float(df[col_profit].sum()),
    "avg_discount": float(df[col_discount].mean()) if col_discount in df else None,
    "orders": int(df[col_order_id].nunique()),
}
pd.Series(kpis).to_json(OUT_DIR / "kpis.json", indent=2)

# ----- AGGREGATIONS -----
sales_by_region = (
    df.groupby([col_region], as_index=False)[col_sales].sum()
    .rename(columns={col_region: "region", col_sales: "sales"})
)

sales_by_month = (
    df.groupby(["month"], as_index=False)[col_sales].sum()
    .rename(columns={col_sales: "sales"})
    .sort_values("month")
)

top_products = (
    df.groupby([col_product], as_index=False)[col_profit].sum()
      .rename(columns={col_product: "product_name", col_profit: "profit"})
      .sort_values("profit", ascending=False).head(10)
)

cat_profit = (
    df.groupby([col_category], as_index=False)[[col_sales, col_profit]].sum()
      .rename(columns={col_category: "category", col_sales: "sales", col_profit: "profit"})
)

seg_sales = (
    df.groupby([col_segment], as_index=False)[col_sales].sum()
      .rename(columns={col_segment: "segment", col_sales: "sales"})
)

# ----- EXPORTS -----
sales_by_region.to_csv(OUT_DIR / "sales_by_region.csv", index=False)
sales_by_month.to_csv(OUT_DIR / "sales_by_month.csv", index=False)
top_products.to_csv(OUT_DIR / "top10_products_by_profit.csv", index=False)
cat_profit.to_csv(OUT_DIR / "category_sales_profit.csv", index=False)
seg_sales.to_csv(OUT_DIR / "segment_sales.csv", index=False)

# ----- REFERENCE PLOT -----
plt.figure()
sales_by_month.plot(x="month", y="sales")
plt.title("Sales by Month")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(OUT_DIR / "sales_by_month.png", dpi=160)

print("✅ Done. Outputs folder:", OUT_DIR)
print("📄 Files:", [p.name for p in OUT_DIR.glob('*')])
