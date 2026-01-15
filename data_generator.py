"""
data_generator.py
Promo Pulse – UAE Retail Promotion Simulator & Data Quality Dashboard

Generates synthetic UAE retail datasets with intentional data-quality issues.

Outputs (CSV) into ./data/ :
- products.csv
- stores.csv
- sales_raw.csv
- inventory_snapshot.csv
- campaign_plan.csv

Run:
    python data_generator.py --out data --seed 42
"""
from __future__ import annotations
import argparse
import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

CITIES = ["Dubai", "Abu Dhabi", "Sharjah"]
CITY_DIRTY = ["Dubai", "DUBAI", "dubai", "Dubayy", "Abu Dhabi", "ABU DHABI", "Sharjah", "sharjah"]
CHANNELS = ["App", "Web", "Marketplace"]
FULFILLMENT = ["Own", "3PL"]
CATEGORIES = ["Electronics", "Grocery", "Fashion", "Home", "Beauty"]

# UAE-ish brand pool (simple + recognizable)
BRANDS = [
    "Samsung","Apple","Sony","Xiaomi","Anker","Nike","Adidas","Zara","H&M",
    "Carrefour","Lulu","Almarai","Barakat","Mai Dubai","Masafi",
    "Sephora","MAC","Nivea","Garnier","Home Centre","IKEA","Dettol","Ariel"
]

PAYMENT_STATUS = ["Paid","Failed","Refunded"]

def _seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)

def generate_products(n_products: int = 300, seed: int = 42) -> pd.DataFrame:
    _seed(seed)
    product_ids = [f"P{i:04d}" for i in range(1, n_products+1)]
    category = np.random.choice(CATEGORIES, size=n_products, p=[0.22,0.28,0.18,0.18,0.14])
    brand = np.random.choice(BRANDS, size=n_products)

    # base_price by category
    base_price = []
    for c in category:
        if c == "Electronics":
            p = float(np.random.lognormal(mean=4.2, sigma=0.45))   # ~ 60-2500
            p = min(max(p, 49), 2999)
        elif c == "Fashion":
            p = float(np.random.lognormal(mean=3.3, sigma=0.45))   # ~ 15-800
            p = min(max(p, 9), 999)
        else:
            p = float(np.random.lognormal(mean=2.6, sigma=0.45))   # ~ 4-250
            p = min(max(p, 2.5), 299)
        base_price.append(round(p, 2))

    base_price = np.array(base_price)
    unit_cost = np.round(base_price * np.random.uniform(0.50, 0.82, size=n_products), 2)
    tax_rate = np.full(n_products, 0.05)
    launch_flag = np.random.choice(["New","Regular"], size=n_products, p=[0.18,0.82])

    df = pd.DataFrame({
        "product_id": product_ids,
        "category": category,
        "brand": brand,
        "base_price_aed": base_price,
        "unit_cost_aed": unit_cost,
        "tax_rate": tax_rate,
        "launch_flag": launch_flag
    })

    # Dirty issue: missing unit_cost 1–2%
    m = np.random.rand(n_products) < np.random.uniform(0.01,0.02)
    df.loc[m, "unit_cost_aed"] = np.nan

    # Dirty issue: cost > price ~1%
    m2 = np.random.rand(n_products) < 0.01
    df.loc[m2, "unit_cost_aed"] = df.loc[m2, "base_price_aed"] * np.random.uniform(1.05, 1.25, size=m2.sum())
    df["unit_cost_aed"] = np.round(df["unit_cost_aed"], 2)
    return df

def generate_stores(seed: int = 42) -> pd.DataFrame:
    _seed(seed)
    rows=[]
    idx=1
    for city in CITIES:
        for ch in CHANNELS:
            for f in FULFILLMENT:
                rows.append([f"S{idx:03d}", city, ch, f])
                idx += 1
    return pd.DataFrame(rows, columns=["store_id","city","channel","fulfillment_type"])

def generate_sales_raw(products: pd.DataFrame, stores: pd.DataFrame, n_orders: int = 30000, seed: int = 42) -> pd.DataFrame:
    """
    30-day window: Dec 1–Dec 30, 2025
    """
    _seed(seed)
    start = datetime(2025,12,1)
    end = datetime(2025,12,30,23,59,59)
    total_minutes = int((end-start).total_seconds()//60)

    order_ids = [f"O{i:07d}" for i in range(1, n_orders+1)]
    prod = np.random.choice(products["product_id"], size=n_orders)
    store = np.random.choice(stores["store_id"], size=n_orders)

    qty = np.random.poisson(lam=2.2, size=n_orders) + 1
    qty = np.clip(qty, 1, 12)

    price_map = products.set_index("product_id")["base_price_aed"].to_dict()
    base_price = np.array([price_map[p] for p in prod])

    discount = np.random.choice([0,5,10,15,20,25,30], size=n_orders,
                                p=[0.35,0.1,0.15,0.15,0.12,0.08,0.05]).astype(float)
    selling_price = np.round(base_price * (1 - discount/100), 2)

    pay = np.random.choice(PAYMENT_STATUS, size=n_orders, p=[0.9,0.06,0.04])
    return_flag = np.where(pay=="Refunded", 1, np.random.binomial(1, 0.03, size=n_orders))

    rand_minutes = np.random.randint(0, total_minutes+1, size=n_orders)
    order_time = [(start + timedelta(minutes=int(m))).strftime("%Y-%m-%d %H:%M:%S") for m in rand_minutes]

    df = pd.DataFrame({
        "order_id": order_ids,
        "order_time": order_time,
        "product_id": prod,
        "store_id": store,
        "qty": qty,
        "selling_price_aed": selling_price,
        "discount_pct": discount,
        "payment_status": pay,
        "return_flag": return_flag
    })

    # Dirty issues
    # 1) Inconsistent city values (~5%)
    df["city_raw"] = np.random.choice(CITY_DIRTY, size=n_orders)

    # 2) Missing discount (~2–4%)
    m = np.random.rand(n_orders) < np.random.uniform(0.02,0.04)
    df.loc[m, "discount_pct"] = np.nan

    # 3) Duplicate order_id (~0.5–1%): duplicate random subset
    dup_n = int(n_orders * np.random.uniform(0.005,0.01))
    dup_idx = np.random.choice(df.index, size=dup_n, replace=False)
    dup = df.loc[dup_idx].copy()
    dup["order_time"] = pd.to_datetime(dup["order_time"]) + pd.to_timedelta(np.random.randint(1,240,size=dup_n), unit="m")
    dup["order_time"] = dup["order_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df = pd.concat([df, dup], ignore_index=True)

    # 4) Corrupted timestamps (~0.5–1%)
    m = np.random.rand(len(df)) < np.random.uniform(0.005,0.01)
    df.loc[m, "order_time"] = np.random.choice(["not_a_time","2024-13-45","2023/99/99",""], size=m.sum())

    # 5) Qty outliers (20–30) small %
    m = np.random.rand(len(df)) < 0.004
    df.loc[m, "qty"] = np.random.randint(20,31,size=m.sum())

    # 6) Price outliers (3–5×) small %
    m2 = np.random.rand(len(df)) < 0.004
    df.loc[m2, "selling_price_aed"] = df.loc[m2, "selling_price_aed"] * np.random.uniform(3,5,size=m2.sum())

    # 7) Invalid payment labels tiny %
    m3 = np.random.rand(len(df)) < 0.003
    df.loc[m3, "payment_status"] = np.random.choice(["paid","PAID","unknown"], size=m3.sum())

    return df

def generate_inventory_snapshot(products: pd.DataFrame, stores: pd.DataFrame, days: int = 30, seed: int = 42) -> pd.DataFrame:
    _seed(seed)
    prod_ids = products["product_id"].sample(int(len(products)*0.5), random_state=seed).values
    dates = pd.date_range(start="2025-12-01", periods=days, freq="D")
    rows=[]
    for d in dates:
        for p in prod_ids:
            for s in stores["store_id"].values:
                stock = int(max(0, np.random.normal(loc=35, scale=20)))
                reorder = int(max(5, np.random.normal(loc=15, scale=6)))
                lead = int(np.random.choice([2,3,4,5,7,10], p=[0.1,0.2,0.25,0.2,0.15,0.1]))
                rows.append([d.date().isoformat(), p, s, stock, reorder, lead])
    df = pd.DataFrame(rows, columns=["snapshot_date","product_id","store_id","stock_on_hand","reorder_point","lead_time_days"])

    # Dirty issue: negative stock & extreme stock
    m = np.random.rand(len(df)) < 0.002
    df.loc[m, "stock_on_hand"] = -np.random.randint(1,60,size=m.sum())
    m2 = np.random.rand(len(df)) < 0.002
    df.loc[m2, "stock_on_hand"] = 9999
    return df

def generate_campaign_plan(seed: int = 42) -> pd.DataFrame:
    _seed(seed)
    today = pd.Timestamp("2026-01-01")
    rows=[]
    for i in range(1,11):
        start = today + pd.Timedelta(days=random.choice([1,3,5]))
        end = start + pd.Timedelta(days=random.choice([7,14]))
        rows.append([
            f"C{i:02d}",
            start.date().isoformat(),
            end.date().isoformat(),
            random.choice(CITIES+["All"]),
            random.choice(CHANNELS+["All"]),
            random.choice(CATEGORIES+["All"]),
            random.choice([5,10,15,20,25,30]),
            random.choice([20000,40000,60000,80000,100000])
        ])
    return pd.DataFrame(rows, columns=["campaign_id","start_date","end_date","city","channel","category","discount_pct","promo_budget_aed"])

def write_all(out_dir: str = "data", seed: int = 42) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    products = generate_products(seed=seed)
    stores = generate_stores(seed=seed)
    sales = generate_sales_raw(products, stores, seed=seed)
    inv = generate_inventory_snapshot(products, stores, seed=seed)
    camp = generate_campaign_plan(seed=seed)

    products.to_csv(out / "products.csv", index=False)
    stores.to_csv(out / "stores.csv", index=False)
    sales.to_csv(out / "sales_raw.csv", index=False)
    inv.to_csv(out / "inventory_snapshot.csv", index=False)
    camp.to_csv(out / "campaign_plan.csv", index=False)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data", help="Output folder")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    out = write_all(args.out, seed=args.seed)
    print(f"Wrote datasets to: {out.resolve()}")

if __name__ == "__main__":
    main()
