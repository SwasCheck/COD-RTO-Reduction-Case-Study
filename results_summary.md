# Results summary (auto-generated)

## 1. Headline KPIs

|   total_orders |   rto_rate_pct |   cod_share_pct |   gmv_lost_to_rto_lakh |
|---------------:|---------------:|----------------:|-----------------------:|
|          60000 |             25 |            64.8 |                     55 |

## 2. RTO rate by city tier x payment mode

| city_tier   | payment_mode   |   orders |   rto_rate_pct |
|:------------|:---------------|---------:|---------------:|
| Tier 1      | COD            |     6009 |           24.4 |
| Tier 1      | Prepaid        |     5988 |            6.7 |
| Tier 2      | COD            |    11988 |           29.4 |
| Tier 2      | Prepaid        |     7091 |            8.7 |
| Tier 3+     | COD            |    20878 |           38.1 |
| Tier 3+     | Prepaid        |     8046 |           12.8 |

## 3. Category view: where is RTO concentrated?

| category         |   orders |   rto_rate_pct |   rto_orders |   share_of_all_rto_pct |
|:-----------------|---------:|---------------:|-------------:|-----------------------:|
| Women Western    |     8332 |           28.9 |         2412 |                   16.1 |
| Electronics Acc. |     6030 |           26.1 |         1575 |                   10.5 |
| Women Ethnic     |    15704 |           24.9 |         3912 |                   26.1 |
| Home & Kitchen   |     8983 |           24.3 |         2180 |                   14.5 |
| Men Fashion      |     8966 |           23.8 |         2130 |                   14.2 |
| Kids             |     5991 |           23.3 |         1394 |                    9.3 |
| Beauty           |     5994 |           23.1 |         1382 |                    9.2 |

## 4. Customer history: repeat RTO behaviour

| customer_segment        |   orders |   rto_rate_pct |
|:------------------------|---------:|---------------:|
| 0 New customer          |     4196 |           36.2 |
| 1 Repeat, clean history |    38932 |           18.8 |
| 2 Repeat, 1 past RTO    |    14131 |           33.7 |
| 3 Repeat, 2+ past RTOs  |     2741 |           50.4 |

## 5. Address quality bands

| address_band        |   orders |   rto_rate_pct |
|:--------------------|---------:|---------------:|
| 1 Low (<0.5)        |     8893 |           33.7 |
| 2 Medium (0.5-0.75) |    27996 |           26.2 |
| 3 High (0.75+)      |    23111 |           20.2 |

## 6. Courier performance on COD orders

| courier   |   cod_orders |   cod_rto_rate_pct |   avg_attempts |
|:----------|-------------:|-------------------:|---------------:|
| Courier C |         7740 |               37   |           1.42 |
| Courier B |        13583 |               32.4 |           1.39 |
| Courier A |        17552 |               32.4 |           1.39 |

## 7. RTO reasons mix

| rto_reason                       |   rto_orders |   pct_of_rto |
|:---------------------------------|-------------:|-------------:|
| Customer refused                 |         5701 |         38   |
| Customer unreachable             |         4061 |         27.1 |
| Changed mind / ordered elsewhere |         2655 |         17.7 |
| Address issue                    |         2568 |         17.1 |

## 8. Monthly trend

| month   |   orders |   rto_rate_pct |
|:--------|---------:|---------------:|
| 2026-01 |    10291 |           24.4 |
| 2026-02 |     9195 |           24.9 |
| 2026-03 |    10458 |           25.4 |
| 2026-04 |    10075 |           24.9 |
| 2026-05 |    10302 |           25   |
| 2026-06 |     9679 |           25.2 |

## Risk model

Test AUC: **0.751**

Top drivers (logistic coefficients):

|                           |   coef |
|:--------------------------|-------:|
| address_quality           |  -1.63 |
| payment_mode_Prepaid      |  -1.58 |
| prior_rto                 |   0.89 |
| city_tier_Tier 3+         |   0.62 |
| is_new_customer           |   0.51 |
| late_night                |   0.33 |
| city_tier_Tier 2          |   0.31 |
| category_Women Western    |   0.26 |
| courier_Courier C         |   0.19 |
| category_Electronics Acc. |   0.19 |

Decile table:

|   decile |   orders |   rto_rate |   rto_orders |   cum_share_rto |
|---------:|---------:|-----------:|-------------:|----------------:|
|        1 |     1800 |      0.042 |           75 |           1     |
|        2 |     1800 |      0.076 |          136 |           0.983 |
|        3 |     1800 |      0.108 |          195 |           0.953 |
|        4 |     1800 |      0.153 |          276 |           0.91  |
|        5 |     1800 |      0.189 |          340 |           0.848 |
|        6 |     1800 |      0.247 |          445 |           0.773 |
|        7 |     1800 |      0.269 |          485 |           0.674 |
|        8 |     1800 |      0.379 |          682 |           0.566 |
|        9 |     1800 |      0.442 |          796 |           0.414 |
|       10 |     1800 |      0.592 |         1066 |           0.237 |

## Interventions (test set, 18,000 orders)

| intervention                                   |   orders_targeted |   rto_avoided |   gross_saving_rs |   cost_rs |   net_saving_rs |   roi_x |   net_saving_per_lakh_orders_rs |
|:-----------------------------------------------|------------------:|--------------:|------------------:|----------:|----------------:|--------:|--------------------------------:|
| A. Prepaid nudge (Rs 20 off, top-30% risk COD) |              5271 |         289.5 |           63043.2 |   18980   |         44063.2 |     3.3 |                          244795 |
| B. Order confirmation IVR (top-30% risk COD)   |              5271 |         913.8 |          154448   |   17032.7 |        137415   |     9.1 |                          763417 |
| C. COD off for top-5% risk                     |               893 |         489   |           84771.4 |    8784.1 |         75987.3 |     9.7 |                          422152 |

Baseline RTO rate (test): 25.0%  
Estimated RTO rate with combined plan: 16.9%
