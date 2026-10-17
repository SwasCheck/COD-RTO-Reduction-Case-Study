# Cutting COD Return-to-Origin (RTO) in Value E-commerce
**A business case study on Tier 2/3 cash-on-delivery orders | SQL · Python · Logistic Regression · Unit Economics**

> All data in this project is **synthetic**. I generated it with `data/generate_data.py`, and the cost inputs are illustrative assumptions, not any company's real figures. The point is the method: how to diagnose a business problem, size it and prioritise fixes.

---

## 1. The business problem
On value e-commerce platforms that serve Bharat, most orders are Cash on Delivery. A share of these orders is never accepted: the buyer refuses the parcel, can't be reached, or has already bought elsewhere. The parcel then travels back to the seller. This is **RTO (Return to Origin)**.

Every RTO burns money with zero revenue:

| Cost line (per RTO, assumed) | Rs |
|---|---|
| Forward shipping | 55 |
| Reverse shipping | 45 |
| Packaging | 8 |
| COD handling | 15 |
| Lost marketplace margin (12% of order value) | ~45 |
| **Total cost of one RTO** | **~170** |

RTO also hurts sellers, who lose working capital and stock gets stuck in transit, and it slows delivery for everyone else.

**Key question:** *Which orders are most likely to RTO, and what is the most cost-effective way to cut RTO without hurting genuine COD buyers?*

## 2. Dataset
60,000 simulated orders over 6 months (Jan–Jun 2026), with 17 fields: city tier, region, category, order value, payment mode, new vs repeat customer, prior orders, prior RTOs, address quality score, courier, promised delivery days, order hour, outcome and RTO reason.

## 3. Diagnosis (SQL: `sql/rto_analysis.sql`)

| Headline | Value |
|---|---|
| Overall RTO rate | **25.0%** |
| COD share of orders | 64.8% |
| COD RTO vs Prepaid RTO | **33.3% vs 9.7%** (3.4x) |
| GMV lost to RTO (6 months) | Rs 55 lakh |

![RTO by tier and payment](outputs/rto_by_tier_payment.png)

**What the data says:**
1. **COD is the biggest single driver.** Tier 3+ COD orders RTO at 38%, against 13% for Tier 3+ prepaid orders.
2. **Past behaviour predicts future behaviour.** Customers with 2+ past RTOs RTO again **50%** of the time, against 19% for repeat customers with a clean history. New customers sit at 36%.
3. **Address quality matters.** Orders with a low address-quality score RTO at 34%, against 20% for high-quality addresses.
4. **Category:** Women Western (29%) and Electronics Accessories (26%) have the highest rates, but Women Ethnic contributes the **most RTO volume** (26% of all RTOs) because it is the biggest category.
5. **Reasons:** "Customer refused" (38%) and "unreachable" (27%) dominate. Both are *intent* problems, which can be addressed before the parcel ships.
6. **Courier C** has a higher COD RTO rate (37% vs 32%), which is worth raising in the courier SLA review.

## 4. Predicting RTO at checkout (`analysis/rto_analysis.py`)
I trained a logistic-regression risk score using **only information available at order time**: no delivery attempts and no outcome data, so there is no leakage. I used a 70/30 train/test split.

- **Test AUC: 0.75**
- The **top 30% riskiest orders capture 57% of all RTOs**
- Top-decile orders RTO at **59%**, against 4% for the bottom decile

![Decile lift](outputs/risk_decile_lift.png)

This is what makes targeting possible. Instead of adding friction for every COD buyer, we act only on the riskiest slice.

## 5. Interventions and their economics
I simulated three levers on the 18,000-order test set:

| Lever | Who | How it works | Key assumption |
|---|---|---|---|
| **A. Prepaid nudge** | Top-30% risk COD | Rs 20 off to switch to UPI | 18% take the offer |
| **B. Order confirmation (IVR/WhatsApp)** | Top-30% risk COD | Confirm intent and address before shipping | Rs 3 per call; 8% cancel before shipping; 25% fewer RTOs among confirmed orders |
| **C. COD off** | Top-5% risk COD | Only prepaid allowed | 40% still buy prepaid, 60% drop off |

**Results (scaled per 1 lakh orders):**

| Lever | RTOs avoided (test set) | ROI | Net saving per lakh orders |
|---|---|---|---|
| A. Prepaid nudge | 290 | 3.3x | Rs 2.4 L |
| **B. Order confirmation** | **914** | **9.1x** | **Rs 7.6 L** |
| C. COD off (top 5%) | 489 | 9.7x | Rs 4.2 L |

![Intervention savings](outputs/intervention_savings.png)

**Combined plan:** the estimated RTO rate drops from **25.0% to ~17%**. This is a directional estimate that discounts overlap between the levers.

## 6. Recommendation
1. **Start with order confirmation (B)** for the top-30% risk COD orders. It saves the most and adds the least friction, because genuine buyers just tap "Confirm" on WhatsApp.
2. **Apply COD-off (C) only to the top ~5%**, mainly repeat-RTO customers. ROI is high, but it costs some genuine orders, so keep the threshold tight and review it monthly.
3. **Run the prepaid nudge (A) as an A/B test.** The discount is only paid when someone switches, so each switch earns about 3x its cost, but the total saving grows with the real conversion rate. The test should also check that the discount doesn't train buyers to wait for offers.
4. **Fix the inputs:** add address auto-complete and landmark prompts in Tier 3+ towns, and take the Courier C gap into the SLA review.

**Metrics to track:** RTO % (overall, COD, by tier), COD-to-prepaid conversion, confirmation response rate, order cancellation rate, and cost per delivered order. **Guardrail:** total delivered orders must not fall.

## 7. Limitations
- The data is synthetic, so the size of the effects is illustrative.
- The intervention effects are assumptions. In reality each lever should be validated through an A/B test before scaling.
- The model is deliberately simple (logistic regression) so it is easy to explain to ops and category teams. Gradient boosting would likely lift AUC.

## Repo structure
```
COD-RTO-Reduction/
├── data/generate_data.py      # synthetic data generator (seeded, reproducible)
├── data/orders.csv            # 60k orders
├── sql/rto_analysis.sql       # 8 diagnostic queries
├── analysis/rto_analysis.py   # SQL run + risk model + intervention economics + charts
└── outputs/                   # charts + auto-generated results_summary.md
```

## How to run
```bash
pip install pandas numpy scikit-learn matplotlib tabulate
python data/generate_data.py
python analysis/rto_analysis.py
```

