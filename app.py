import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="UAE Retail Insights", page_icon="🛒", layout="wide")

# ---------- Helpers ----------
def load_csv(possible_paths):
    for p in possible_paths:
        if Path(p).exists():
            return pd.read_csv(p)
    raise FileNotFoundError(f"None of these files were found: {possible_paths}")

@st.cache_data
def load_data():
    # Load cleaned CSVs (tries multiple possible filenames)
    products = load_csv([
        "data/clean/products_clean.csv",
        "products_clean.csv",
        "clean_product.csv",
        "products.csv",
    ])

    inventory = load_csv([
        "data/clean/inventory_clean.csv",
        "inventory_clean.csv",
        "clean_inventory.csv",
        "inventory.csv",
    ])

    sales = load_csv([
        "data/clean/sales_clean.csv",
        "sales_clean.csv",
        "clean_sales.csv",
        "sales.csv",
    ])

    # Ensure sale_date is datetime
    if "sale_date" in sales.columns:
        sales["sale_date"] = pd.to_datetime(sales["sale_date"], errors="coerce")

    # Create revenue column if missing
    if "revenue_aed" not in sales.columns:
        if "unit_price" in sales.columns and "quantity" in sales.columns:
            sales["revenue_aed"] = sales["unit_price"] * sales["quantity"]
        elif "price" in sales.columns and "quantity" in sales.columns:
            sales["revenue_aed"] = sales["price"] * sales["quantity"]
        else:
            sales["revenue_aed"] = 0

    # Merge category/item/brand into sales (for charts)
    if "product_id" in sales.columns and "product_id" in products.columns:
        keep_cols = [c for c in ["product_id", "category", "item", "brand"] if c in products.columns]
        if keep_cols:
            sales = sales.merge(
                products[keep_cols],
                on="product_id",
                how="left"
            )

    return products, inventory, sales

    products = load_csv([
        "data/clean/products_clean.csv",
        "products_clean.csv",
        "clean_product.csv"
    ])
    inventory = load_csv([
        "data/clean/inventory_clean.csv",
        "inventory_clean.csv",
        "clean_inventory.csv"
    ])
    sales = load_csv([
        "data/clean/sales_clean.csv",
        "sales_clean.csv",
        "clean_sales.csv"
    ])
   # Add category into sales by merging with products

if "product_id" in sales.columns and "product_id" in products.columns:
    sales = sales.merge(
        products[["product_id", "category", "item", "brand"]],
        on="product_id",
        how="left"
    )

# Create revenue column if missing
if "revenue_aed" not in sales.columns:
    if "unit_price" in sales.columns and "quantity" in sales.columns:
        sales["revenue_aed"] = sales["unit_price"] * sales["quantity"]
    elif "price" in sales.columns and "quantity" in sales.columns:
        sales["revenue_aed"] = sales["price"] * sales["quantity"]

# Create revenue column if missing
if "revenue_aed" not in sales.columns:
    if "unit_price" in sales.columns and "quantity" in sales.columns:
        sales["revenue_aed"] = sales["unit_price"] * sales["quantity"]
    elif "price" in sales.columns and "quantity" in sales.columns:
        sales["revenue_aed"] = sales["price"] * sales["quantity"]


# Create revenue column if missing
if "revenue_aed" not in sales.columns:
    if "unit_price" in sales.columns and "quantity" in sales.columns:
        sales["revenue_aed"] = sales["unit_price"] * sales["quantity"]
    elif "price" in sales.columns and "quantity" in sales.columns:
        sales["revenue_aed"] = sales["price"] * sales["quantity"]

    sales = sales.merge(
        # Create revenue column if missing
if "revenue_aed" not in sales.columns:
    if "unit_price" in sales.columns and "quantity" in sales.columns:
        sales["revenue_aed"] = sales["unit_price"] * sales["quantity"]
    elif "price" in sales.columns and "quantity" in sales.columns:
        sales["revenue_aed"] = sales["price"] * sales["quantity"]

        products[["product_id", "category", "item", "brand"]],
        on="product_id",
        how="left"
    )


    # Ensure date column is datetime
    if "sale_date" in sales.columns:
        sales["sale_date"] = pd.to_datetime(sales["sale_date"], errors="coerce")

    return products, inventory, sales

# ---------- Load ----------
st.title("🛒 UAE Retail Insights Dashboard")
st.caption("Clean data → KPIs → Sales, Products, Inventory insights")

try:
    products, inventory, sales = load_data()
except Exception as e:
    st.error("Your app is running, but the data files cannot be loaded.")
    st.code(str(e))
    st.stop()

# ---------- Sidebar Filters ----------
st.sidebar.header("Filters")

# Date filter
if "sale_date" in sales.columns and sales["sale_date"].notna().any():
    min_d = sales["sale_date"].min()
    max_d = sales["sale_date"].max()
    start_date, end_date = st.sidebar.date_input(
        "Sales date range",
        value=(min_d.date(), max_d.date()),
        min_value=min_d.date(),
        max_value=max_d.date(),
    )
    sales_f = sales[(sales["sale_date"].dt.date >= start_date) & (sales["sale_date"].dt.date <= end_date)]
else:
    sales_f = sales.copy()

# Store filter
store_col = "store_name" if "store_name" in sales_f.columns else None
if store_col:
    stores = ["All"] + sorted([s for s in sales_f[store_col].dropna().unique().tolist()])
    store_pick = st.sidebar.selectbox("Store", stores, index=0)
    if store_pick != "All":
        sales_f = sales_f[sales_f[store_col] == store_pick]

# Category filter
cat_col = "category" if "category" in sales_f.columns else None
if cat_col:
    cats = ["All"] + sorted([c for c in sales_f[cat_col].dropna().unique().tolist()])
    cat_pick = st.sidebar.selectbox("Category", cats, index=0)
    if cat_pick != "All":
        sales_f = sales_f[sales_f[cat_col] == cat_pick]

# Channel filter
chan_col = "channel" if "channel" in sales_f.columns else None
if chan_col:
    chans = ["All"] + sorted([c for c in sales_f[chan_col].dropna().unique().tolist()])
    chan_pick = st.sidebar.selectbox("Channel", chans, index=0)
    if chan_pick != "All":
        sales_f = sales_f[sales_f[chan_col] == chan_pick]

# ---------- KPIs ----------
def safe_sum(df, col):
    return float(df[col].sum()) if col in df.columns else 0.0

def safe_mean(df, col):
    return float(df[col].mean()) if col in df.columns else 0.0

revenue = safe_sum(sales_f, "revenue_aed")
profit = safe_sum(sales_f, "gross_profit_aed")
orders = sales_f["sale_id"].nunique() if "sale_id" in sales_f.columns else len(sales_f)
avg_discount = safe_mean(sales_f, "discount_pct") * 100 if "discount_pct" in sales_f.columns else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue (AED)", f"{revenue:,.2f}")
k2.metric("Total Gross Profit (AED)", f"{profit:,.2f}")
k3.metric("Total Orders", f"{orders:,}")
k4.metric("Avg Discount (%)", f"{avg_discount:,.2f}")

st.divider()

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["📈 Sales Insights", "📦 Inventory", "🧾 Products"])

with tab1:
    left, right = st.columns([1.2, 1])

    # Revenue over time
    if "sale_date" in sales_f.columns and sales_f["sale_date"].notna().any() and "revenue_aed" in sales_f.columns:
        tmp = sales_f.dropna(subset=["sale_date"]).copy()
        tmp["day"] = tmp["sale_date"].dt.date
        daily = tmp.groupby("day", as_index=False)["revenue_aed"].sum()
        fig = px.line(daily, x="day", y="revenue_aed", title="Revenue Over Time (Daily)")
        left.plotly_chart(fig, use_container_width=True)
    else:
        left.info("No usable date/revenue columns found to plot revenue over time.")

    # Category revenue
    if "category" in sales_f.columns and "revenue_aed" in sales_f.columns:
        cat_rev = sales_f.groupby("category", as_index=False)["revenue_aed"].sum().sort_values("revenue_aed", ascending=False)
        fig2 = px.bar(cat_rev, x="category", y="revenue_aed", title="Revenue by Category")
        right.plotly_chart(fig2, use_container_width=True)
    else:
        right.info("Category or revenue column missing for category chart.")

    st.subheader("Top Products by Revenue")
    if "product" in sales_f.columns and "revenue_aed" in sales_f.columns:
        top_p = sales_f.groupby("product", as_index=False)["revenue_aed"].sum().sort_values("revenue_aed", ascending=False).head(10)
        st.dataframe(top_p, use_container_width=True)
    else:
        # Try mapping product_id to product name using products table
        if "product_id" in sales_f.columns and "revenue_aed" in sales_f.columns and "product_id" in products.columns:
            merged = sales_f.merge(products[["product_id", "product"]], on="product_id", how="left")
            top_p = merged.groupby("product", as_index=False)["revenue_aed"].sum().sort_values("revenue_aed", ascending=False).head(10)
            st.dataframe(top_p, use_container_width=True)
        else:
            st.info("Could not compute top products (missing product/product_id or revenue).")

with tab2:
    st.subheader("Inventory Snapshot")
    st.dataframe(inventory.head(30), use_container_width=True)

    if "store_name" in inventory.columns and "on_hand_units" in inventory.columns:
        inv_store = inventory.groupby("store_name", as_index=False)["on_hand_units"].sum().sort_values("on_hand_units", ascending=False)
        fig = px.bar(inv_store, x="store_name", y="on_hand_units", title="Total On-Hand Units by Store")
        st.plotly_chart(fig, use_container_width=True)

    if "category" in inventory.columns and "on_hand_units" in inventory.columns:
        inv_cat = inventory.groupby("category", as_index=False)["on_hand_units"].sum().sort_values("on_hand_units", ascending=False)
        fig2 = px.pie(inv_cat, names="category", values="on_hand_units", title="On-Hand Units Share by Category")
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Products Catalog")
    st.dataframe(products.head(50), use_container_width=True)

    if "category" in products.columns and "price_aed" in products.columns:
        fig = px.box(products, x="category", y="price_aed", title="Price Distribution by Category")
        st.plotly_chart(fig, use_container_width=True)

st.caption("✅ If you change any file name/path, update the load_csv() paths in app.py.")




