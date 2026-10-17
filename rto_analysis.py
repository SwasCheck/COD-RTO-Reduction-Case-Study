"""
COD RTO Reduction case study: risk scoring + intervention economics.

Steps
1. Run the diagnostic SQL against an in-memory SQLite copy of the data.
2. Train a logistic-regression RTO risk score using only order-time features.
3. Simulate three interventions on the test set and compute net savings.
4. Save charts and a results summary to outputs/.

All cost inputs are illustrative assumptions (see ASSUMPTIONS).
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

ASSUMPTIONS = {
    "forward_ship": 55,      # Rs per shipment
    "reverse_ship": 45,      # Rs per RTO return leg
    "packaging": 8,          # Rs per shipment, lost on RTO
    "cod_handling": 15,      # Rs per COD shipment
    "take_rate": 0.12,       # marketplace margin on delivered GMV
    "prepaid_nudge": 20,     # Rs discount to switch COD -> prepaid
    "nudge_conversion": 0.18,
    "ivr_cost": 3,           # Rs per confirmation call/IVR
    "ivr_rto_reduction": 0.25,   # relative reduction in RTO for confirmed orders
    "ivr_precancel": 0.08,       # share of called orders cancelled before shipping
    "cod_block_to_prepaid": 0.40,  # blocked COD users who still buy prepaid
}
A = ASSUMPTIONS

df = pd.read_csv(ROOT / "data" / "orders.csv")

# ---------------------------------------------------------------- 1. SQL
con = sqlite3.connect(":memory:")
df.to_sql("orders", con, index=False)
sql_text = (ROOT / "sql" / "rto_analysis.sql").read_text()
queries = [q.strip() for q in sql_text.split(";") if "SELECT" in q]
sql_results = []
for q in queries:
    title = next((l for l in q.splitlines() if l.startswith("--") and l[3:4].isdigit()), "-- query")
    sql_results.append((title.strip("- "), pd.read_sql(q, con)))

# ---------------------------------------------------------------- 2. Model
features = pd.get_dummies(
    df[["city_tier", "category", "payment_mode", "courier"]], drop_first=True
).astype(int)
features["is_new_customer"] = df.is_new_customer
features["prior_rto"] = df.prior_rto.clip(upper=3)
features["clean_orders"] = (df.prior_orders - df.prior_rto).clip(upper=8)
features["address_quality"] = df.address_quality
features["order_value_100"] = df.order_value / 100
features["promised_days"] = df.promised_days
features["late_night"] = df.order_hour.between(0, 4).astype(int)

X_tr, X_te, y_tr, y_te, idx_tr, idx_te = train_test_split(
    features, df.is_rto, df.index, test_size=0.3, random_state=7, stratify=df.is_rto)
model = LogisticRegression(max_iter=2000).fit(X_tr, y_tr)
p_te = model.predict_proba(X_te)[:, 1]
auc = roc_auc_score(y_te, p_te)

test = df.loc[idx_te].copy()
test["risk"] = p_te
test["decile"] = pd.qcut(test.risk.rank(method="first"), 10, labels=range(1, 11)).astype(int)

# counterfactual risk if the same order were prepaid
X_pre = X_te.copy()
X_pre["payment_mode_Prepaid"] = 1
test["risk_if_prepaid"] = model.predict_proba(X_pre)[:, 1]

decile_tbl = test.groupby("decile").agg(orders=("is_rto", "size"),
                                        rto_rate=("is_rto", "mean"),
                                        rto_orders=("is_rto", "sum")).reset_index()
decile_tbl["cum_share_rto"] = decile_tbl.sort_values("decile", ascending=False).rto_orders.cumsum() \
    / decile_tbl.rto_orders.sum()

# ---------------------------------------------------------------- 3. Economics
def rto_cost(row_value):
    """Cost of one RTO: both shipping legs, packaging, COD handling, lost margin."""
    return A["forward_ship"] + A["reverse_ship"] + A["packaging"] + A["cod_handling"] \
        + A["take_rate"] * row_value

test["rto_cost"] = rto_cost(test.order_value)
test["margin"] = A["take_rate"] * test.order_value
cod = test.payment_mode == "COD"
hi = test.risk >= test.risk.quantile(0.70)      # top 30% risk
top5 = test.risk >= test.risk.quantile(0.95)    # top 5% risk

results = []

# A. Prepaid nudge for medium/high-risk COD orders (top 30% risk)
tgt = test[cod & hi]
conv = tgt.sample(frac=A["nudge_conversion"], random_state=1)
rto_avoided = (conv.risk - conv.risk_if_prepaid).sum()
saving = ((conv.risk - conv.risk_if_prepaid) * conv.rto_cost).sum() + A["cod_handling"] * len(conv)
cost = A["prepaid_nudge"] * len(conv)
results.append(("A. Prepaid nudge (Rs 20 off, top-30% risk COD)", len(tgt), rto_avoided, saving, cost))

# B. IVR / WhatsApp order confirmation for top-30% risk COD
tgt = test[cod & hi]
cancel_n = A["ivr_precancel"] * len(tgt)
# pre-cancelled orders are disproportionately the would-be RTOs: assume their RTO prob is 2x avg
avg_r = tgt.risk.mean()
precancel_rto = cancel_n * min(1, 2 * avg_r)
remaining_rto = tgt.risk.sum() - precancel_rto
rto_avoided_b = precancel_rto + A["ivr_rto_reduction"] * remaining_rto
avg_cost = tgt.rto_cost.mean()
saving_b = rto_avoided_b * avg_cost
lost_margin_b = (cancel_n - precancel_rto) * tgt.margin.mean()   # genuine buyers lost
cost_b = A["ivr_cost"] * len(tgt) + lost_margin_b
results.append(("B. Order confirmation IVR (top-30% risk COD)", len(tgt), rto_avoided_b, saving_b, cost_b))

# C. Disable COD for top-5% risk
tgt = test[cod & top5]
stay = A["cod_block_to_prepaid"]
rto_avoided_c = tgt.risk.sum() - stay * tgt.risk_if_prepaid.sum()
saving_c = (tgt.risk * tgt.rto_cost).sum() - stay * (tgt.risk_if_prepaid * tgt.rto_cost).sum()
lost_margin_c = ((1 - stay) * (1 - tgt.risk) * tgt.margin).sum()
results.append(("C. COD off for top-5% risk", len(tgt), rto_avoided_c, saving_c, lost_margin_c))

res = pd.DataFrame(results, columns=["intervention", "orders_targeted", "rto_avoided",
                                     "gross_saving_rs", "cost_rs"])
res["net_saving_rs"] = res.gross_saving_rs - res.cost_rs
res["roi_x"] = res.gross_saving_rs / res.cost_rs
scale = 100_000 / len(test)
res["net_saving_per_lakh_orders_rs"] = res.net_saving_rs * scale

base_rto = test.is_rto.sum()
# Combined plan: C on top-5%, then A, then B on remaining top-30% (approx, no double count of C pool)
combined_avoided = res.rto_avoided.iloc[2] + 0.8 * (res.rto_avoided.iloc[0] + res.rto_avoided.iloc[1])
combined_rate = (base_rto - combined_avoided) / len(test)

# ---------------------------------------------------------------- 4. Charts
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

pivot = df.pivot_table(index="city_tier", columns="payment_mode", values="is_rto") * 100
ax = pivot.plot(kind="bar", color=["#E4572E", "#4C9F70"], figsize=(6, 4), rot=0)
ax.set_ylabel("RTO rate (%)"); ax.set_xlabel("")
ax.set_title("RTO rate by city tier and payment mode")
for c in ax.containers:
    ax.bar_label(c, fmt="%.0f%%", fontsize=9)
plt.tight_layout(); plt.savefig(OUT / "rto_by_tier_payment.png", dpi=160); plt.close()

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(decile_tbl.decile, decile_tbl.rto_rate * 100, color="#3B6EA8")
ax.axhline(test.is_rto.mean() * 100, ls="--", color="grey", lw=1)
ax.text(1, test.is_rto.mean() * 100 + 1, "average", color="grey", fontsize=9)
ax.set_xlabel("Risk decile (10 = highest predicted risk)"); ax.set_ylabel("Actual RTO rate (%)")
ax.set_title(f"Risk score separates RTO well (AUC {auc:.2f})")
ax.set_xticks(range(1, 11))
plt.tight_layout(); plt.savefig(OUT / "risk_decile_lift.png", dpi=160); plt.close()

fig, ax = plt.subplots(figsize=(7, 3.6))
labels = [r.split(" (")[0] for r in res.intervention]
vals = res.net_saving_per_lakh_orders_rs / 1e5
ax.barh(labels, vals, color=["#4C9F70" if v > 0 else "#E4572E" for v in vals])
for i, v in enumerate(vals):
    ax.text(v, i, f"  Rs {v:.1f} L", va="center", fontsize=9)
ax.set_xlabel("Net saving per 1 lakh orders (Rs lakh)")
ax.set_title("Intervention economics")
ax.invert_yaxis()
plt.tight_layout(); plt.savefig(OUT / "intervention_savings.png", dpi=160); plt.close()

# ---------------------------------------------------------------- 5. Write summary
coefs = pd.Series(model.coef_[0], index=features.columns).sort_values(key=abs, ascending=False)
with open(OUT / "results_summary.md", "w") as f:
    f.write("# Results summary (auto-generated)\n\n")
    for title, tbl in sql_results:
        f.write(f"## {title}\n\n{tbl.to_markdown(index=False)}\n\n")
    f.write(f"## Risk model\n\nTest AUC: **{auc:.3f}**\n\n")
    f.write("Top drivers (logistic coefficients):\n\n")
    f.write(coefs.head(10).round(2).to_frame("coef").to_markdown() + "\n\n")
    f.write("Decile table:\n\n" + decile_tbl.round(3).to_markdown(index=False) + "\n\n")
    f.write("## Interventions (test set, 18,000 orders)\n\n")
    f.write(res.round(1).to_markdown(index=False) + "\n\n")
    f.write(f"Baseline RTO rate (test): {test.is_rto.mean():.1%}  \n")
    f.write(f"Estimated RTO rate with combined plan: {combined_rate:.1%}\n")

print(f"AUC: {auc:.3f}")
print(decile_tbl.round(3).to_string(index=False))
print(res.round(1).to_string(index=False))
print(f"Baseline RTO {test.is_rto.mean():.1%} -> combined {combined_rate:.1%}")
for title, tbl in sql_results:
    print("\n", title); print(tbl.to_string(index=False))
