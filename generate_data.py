"""
Generate a synthetic order dataset for an Indian value-ecommerce marketplace.

All data is SIMULATED. Rates and costs are illustrative assumptions chosen to
resemble a Tier 2/3, COD-heavy marketplace; they are not real company figures.

Output: data/orders.csv (~60,000 orders)
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
N = 60_000

# ---- Dimensions -----------------------------------------------------------
city_tier = rng.choice(["Tier 1", "Tier 2", "Tier 3+"], N, p=[0.20, 0.32, 0.48])
region = rng.choice(["North", "South", "East", "West", "Central"], N,
                    p=[0.26, 0.20, 0.18, 0.20, 0.16])
category = rng.choice(
    ["Women Ethnic", "Women Western", "Men Fashion", "Kids", "Home & Kitchen",
     "Beauty", "Electronics Acc."], N,
    p=[0.26, 0.14, 0.15, 0.10, 0.15, 0.10, 0.10])

base_price = {"Women Ethnic": 420, "Women Western": 380, "Men Fashion": 360,
              "Kids": 300, "Home & Kitchen": 340, "Beauty": 250,
              "Electronics Acc.": 290}
order_value = np.array([rng.gamma(4, base_price[c] / 4) for c in category]).round(0)
order_value = np.clip(order_value, 99, 3000)

# Customer history: number of prior delivered orders, and prior RTOs
prior_orders = rng.poisson(np.where(city_tier == "Tier 1", 4.0, 2.5))
prior_rto = rng.binomial(prior_orders, 0.12)
is_new_customer = (prior_orders == 0).astype(int)

# Address quality score 0-1 (landmark, pincode match, phone verified etc.)
addr_quality = np.clip(rng.beta(5, 2, N) - np.where(city_tier == "Tier 3+", 0.08, 0), 0, 1).round(2)

# Payment mode: COD share higher in smaller towns and for new users
p_cod = 0.62 + 0.10 * (city_tier == "Tier 3+") - 0.12 * (city_tier == "Tier 1") \
        + 0.08 * is_new_customer
payment_mode = np.where(rng.random(N) < p_cod, "COD", "Prepaid")

courier = rng.choice(["Courier A", "Courier B", "Courier C"], N, p=[0.45, 0.35, 0.20])
promised_days = rng.integers(3, 9, N)
order_hour = rng.integers(0, 24, N)
order_date = pd.Timestamp("2026-01-01") + pd.to_timedelta(rng.integers(0, 180, N), unit="D")

# ---- Outcome model (latent RTO propensity) ---------------------------------
logit = (
    -3.1
    + 1.55 * (payment_mode == "COD")
    + 0.35 * (city_tier == "Tier 2") + 0.65 * (city_tier == "Tier 3+")
    + 0.55 * is_new_customer
    + 0.9 * np.minimum(prior_rto, 3)
    - 0.10 * np.minimum(prior_orders - prior_rto, 8)
    - 1.6 * (addr_quality - 0.7)
    + 0.0007 * (order_value - 400)
    + 0.10 * (promised_days - 5)
    + 0.25 * np.isin(category, ["Women Western", "Electronics Acc."])
    + 0.30 * ((order_hour >= 0) & (order_hour <= 4))   # late-night impulse orders
    + 0.20 * (courier == "Courier C")
)
p_rto = 1 / (1 + np.exp(-logit))
is_rto = (rng.random(N) < p_rto).astype(int)

delivery_attempts = np.where(is_rto == 1, rng.choice([1, 2, 3], N, p=[0.35, 0.35, 0.30]),
                             rng.choice([1, 2], N, p=[0.88, 0.12]))
rto_reason = np.where(
    is_rto == 1,
    rng.choice(["Customer refused", "Customer unreachable", "Address issue",
                "Changed mind / ordered elsewhere"], N, p=[0.38, 0.27, 0.17, 0.18]),
    "")

df = pd.DataFrame({
    "order_id": [f"ORD{100000 + i}" for i in range(N)],
    "order_date": order_date.date,
    "order_hour": order_hour,
    "city_tier": city_tier,
    "region": region,
    "category": category,
    "order_value": order_value,
    "payment_mode": payment_mode,
    "is_new_customer": is_new_customer,
    "prior_orders": prior_orders,
    "prior_rto": prior_rto,
    "address_quality": addr_quality,
    "courier": courier,
    "promised_days": promised_days,
    "delivery_attempts": delivery_attempts,
    "is_rto": is_rto,
    "rto_reason": rto_reason,
})

out = Path(__file__).parent / "orders.csv"
df.to_csv(out, index=False)
print(f"Wrote {len(df):,} rows to {out}")
print(f"Overall RTO rate: {df.is_rto.mean():.1%}")
print(df.groupby("payment_mode").is_rto.mean().round(3))
