# Promo Pulse – UAE Retail Promotion Simulator & Data Quality Dashboard

Project Type: University Final Project  
Domain: Retail Analytics & Data Engineering  
Last Updated: January 2026  

---

## Overview
Promo Pulse is a promotional scenario simulator and data quality transparency dashboard designed for UAE omnichannel retailers.
It demonstrates an end-to-end pipeline: **synthetic dirty data generation**, **systematic validation + cleaning with audit logs**, and a **rule-based promotion simulator** under real business constraints.

## Business Scenario (UAE Context)
- Cities: Dubai, Abu Dhabi, Sharjah  
- Channels: App, Web, Marketplace  
- Fulfillment: Own, 3PL  

Marketing wants to run a discount campaign with a **budget cap**, **gross margin floor**, and **inventory constraints** while using messy historical data.

## Data Model (5 tables)
- products
- stores (exactly 18)
- sales_raw (25k–40k rows, duplicates, missing discounts, corrupted timestamps)
- inventory_snapshot (negative/extreme stock)
- campaign_plan (optional)

## Run locally
```bash
pip install -r requirements.txt
python data_generator.py --out data --seed 42
python cleaner.py --data_dir data
streamlit run app.py
```

## Streamlit App
The app includes:
- Data quality issue log (downloadable)
- Executive + Manager views
- What-if promotion simulator with constraints (budget / margin / stock)

