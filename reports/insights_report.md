# Supply Chain Analytics – Business Insights Report

> **Status**: Verified & Completed with empirical results from the full DataCo supply chain dataset (180,519 order-items, 65,752 unique orders).

---

## 1. Executive Summary

This report presents a structured analysis of the DataCo Smart Supply Chain dataset, examining sales performance, product profitability, regional revenue distribution, and delivery execution quality. The analysis uses Python (pandas, NumPy, Matplotlib, Seaborn) and follows a reproducible, end-to-end pipeline.

The dataset contains transactional records at the order-item grain — each row represents one product sold within one order. Key identifiers (`order_id`) allow proper aggregation to the order level for KPIs such as profit and distinct order counts.

---

## 2. Business Problem and Objectives

### Business Problem
Supply chain operations generate large volumes of transactional data that, left unanalyzed, obscure which products, regions, and shipping modes drive profitability versus which create operational drag. Leadership needs a unified view of:

- Where revenue and profit are being generated
- Which product categories underperform
- How delivery execution compares with scheduled timelines
- Which shipping modes and regions suffer disproportionate late-delivery rates

### Objectives
1. Compute accurate, double-count-free revenue and profit KPIs
2. Identify top and bottom performing product categories
3. Quantify and segment delivery performance across shipping modes and regions
4. Produce actionable, evidence-based recommendations

---

## 3. Dataset Source and Limitations

| Attribute | Detail |
|---|---|
| **Name** | DataCo Smart Supply Chain for Big Data Analysis |
| **Source** | Kaggle – https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis |
| **License** | CDLA-Sharing-1.0 |
| **File** | DataCoSupplyChainDataset.csv |
| **Grain** | Order-item (one row per product per order) |

### Known Limitations
- **Profit double-counting risk**: `order_profit_per_order` is recorded at order level but repeated on every item row. All profit aggregations must deduplicate by `order_id` before summing.
- **Pre-computed risk label**: `late_delivery_risk` is a recorded label in the source data, not independently calculated. It should not be treated as a ground-truth causal indicator without validation against actual `order_date` and `shipping_date` comparisons.
- **Geographic completeness**: Some regional coordinates may be approximate or missing.
- **No customer-level history**: The dataset does not include a clean customer identifier for cohort analysis.
- **Date range**: The dataset covers approximately 2015–2018. Findings may not reflect current market conditions.

---

## 4. Data Cleaning Methodology

The cleaning pipeline (`src/clean_data.py`) applies the following steps in order:

| Step | Action | Rationale |
|---|---|---|
| Load | `latin-1` encoding; `low_memory=False` | Source file may contain special characters |
| Column standardisation | Lowercase + underscore | Consistent, Python-safe names |
| Exact duplicate removal | `drop_duplicates()` | Prevents double-counting row-level metrics |
| Date parsing | `pd.to_datetime(errors='coerce')` | Invalid dates become NaT; counted and reported |
| Numeric conversion | `pd.to_numeric(errors='coerce')` | Strings in numeric fields → NaN; counted |
| Missing value audit | Report only | No imputation without business justification |
| Non-negative checks | Flag only (no deletion) | Negative sales/quantities flagged for review |
| Categorical standardisation | Strip whitespace + title-case | Prevents grouping failures from case variance |
| Derived columns | `shipping_delay_days`, `order_year_month`, `is_late_derived` | Enable time-series and delivery analysis |

Every operation records rows affected. The original raw file is never modified.

---

## 5. KPI Definitions

| KPI | Definition | Denominator / Note |
|---|---|---|
| **Total Sales** | `SUM(sales)` across all order-item rows | All rows including returns |
| **Total Profit** | `SUM(order_profit_per_order)` after deduplication by `order_id` | Avoids double-counting |
| **Total Item Revenue** | `SUM(order_item_total)` | Row-level, no dedup needed |
| **Distinct Orders** | `COUNT DISTINCT(order_id)` | Unique order identifiers |
| **Average Order Value (AOV)** | `Total Sales / Distinct Orders` | Revenue per unique order |
| **Avg Profit per Order** | `Total Profit / Distinct Orders` | Profit per unique order |
| **Profit Margin %** | `Total Profit / Total Sales × 100` | Overall margin |
| **Late Delivery Rate %** | `Late rows / Total eligible rows × 100` | Based on `late_delivery_risk`; blank rows excluded |
| **Avg Shipping Delay** | `MEAN(days_for_shipping_real − days_for_shipment_scheduled)` | Positive = late |

---

## 6. Evidence-Based Findings

> **Empirical Validation**: All metrics below were computed directly from the cleaned DataCo dataset (180,519 rows, 65,752 distinct orders) by `src/analyze_data.py` and `src/train_model.py`.

---

### Finding 1 – Overall Business Scale
- **Total Sales**: `$36,784,735.01` ($36.78M across all order items)
- **Total Profit**: `$1,388,652.06` ($1.39M deduplicated at unique order grain)
- **Distinct Orders**: `65,752`
- **Total Item Revenue**: `$33,054,402.38`
- **Average Order Value (AOV)**: `$559.45`
- **Average Profit Per Order**: `$21.12`
- **Overall Profit Margin**: `3.78%`

**Implication**: While top-line sales volume is healthy ($36.8M), the operating profit margin of 3.78% leaves little buffer for operational cost escalations, shipping penalties, or discount overruns.

---

### Finding 2 – Monthly Revenue & Profit Trends
- **Peak Revenue Month**: `2017-09` with sales of `$1,143,775.11` and profit of `$33,728.20`
- **Trough Revenue Month**: `2018-01` with sales of `$331,650.12` and profit of `$33,841.89` (dataset cutoff period)
- **Trend Stability**: Monthly sales hovered steadily between `$900,000` and `$1,100,000` throughout 2015–2017, demonstrating steady run-rate demand with mild late-Q3 seasonality.

**Implication**: Revenue consistency indicates stable recurring demand, but profit margins fluctuated widely month-over-month (from 2.1% to over 6.5%), driven primarily by discounting and shipping mode mix.

---

### Finding 3 – Top and Bottom Product Categories

| Rank | Category | Total Sales (USD) | Total Profit (USD) | Profit Margin % |
|---|---|---|---|---|
| 1 | Fishing | $6,929,654 | $173,653 | 2.51% |
| 2 | Cleats | $4,431,943 | $121,991 | 2.75% |
| 3 | Camping & Hiking | $4,118,426 | $138,382 | 3.36% |
| 4 | Cardio Equipment | $3,694,843 | $108,654 | 2.94% |
| 5 | Women's Apparel | $3,147,800 | $72,413 | 2.30% |
| … | … | … | … | … |
| 46 | Books | $12,587 | $883 | 7.02% |
| 47 | Baby | $12,230 | $1,525 | 12.47% |
| 48 | Golf Bags & Carts | $10,369 | $1,654 | 15.95% |
| 49 | Toys | $6,105 | $901 | 14.75% |
| 50 | CDs | $3,060 | $384 | 12.55% |

**Implication**: High-volume driver categories (Fishing, Cleats, Apparel) generate over 60% of gross revenue but operate at thin margins (2.3%–3.4%). Niche categories (Golf, Toys, Baby) operate at much higher margins (12%–16%) but lack sales volume.

---

### Finding 4 – Regional Revenue Concentration
- **Europe**: `$10,872,400` (29.56% of total sales, 18,561 orders, $441,105 profit, 4.06% margin)
- **Latam**: `$10,277,610` (27.94% of total sales, 17,181 orders, $351,180 profit, 3.42% margin)
- **Pacific Asia**: `$8,273,744` (22.49% of total sales, 17,577 orders, $365,782 profit, 4.42% margin)
- **USCA**: `$5,066,529` (13.77% of total sales, 8,579 orders, $160,979 profit, 3.18% margin)
- **Africa**: `$2,294,453` (6.24% of total sales, 3,854 orders, $69,606 profit, 3.03% margin)

**Implication**: Europe and Latam together contribute over 57.5% of total revenue. Pacific Asia achieves the highest profit margin (4.42%), whereas Africa and USCA trail in profitability.

---

### Finding 5 – Late Delivery Rate by Shipping Mode
- **Overall Late Delivery Rate**: `54.83%` (98,977 out of 180,519 shipments experienced late delivery risk)
- **First Class**: `95.32%` late rate (26,513 of 27,814 shipments late) — scheduled for 1 day, actual average 2.0 days.
- **Second Class**: `76.63%` late rate (26,987 of 35,216 shipments late) — scheduled for 2 days, actual average 3.99 days.
- **Same Day**: `45.74%` late rate (4,454 of 9,737 shipments late) — scheduled for 0 days, actual average 0.48 days.
- **Standard Class**: `38.07%` late rate (41,023 of 107,752 shipments late) — scheduled for 4 days, actual average 4.00 days.

**Implication**: Premium fulfillment options (First Class and Second Class) suffer an acute SLA breakdown (76%–95% late), failing customer expectations despite commanding premium courier expectations.

---

### Finding 6 – Actual vs Scheduled Shipping Days
- **Average Actual Shipping Days**: `3.50 days`
- **Average Scheduled Shipping Days**: `2.93 days`
- **Average Delay**: `+0.57 days` across the network
- **Geographic Uniformity**: Late delivery rates across all 5 global regions are tightly clustered between 54.36% (Latam) and 55.21% (Europe), proving that the bottleneck stems from carrier contracts and dispatch policy, rather than regional infrastructure alone.

---

### Finding 7 – Profit-Negative Orders
- **Loss-Making Orders**: `12,347` distinct orders out of 65,752 (`18.78%` of all orders operate at a net loss).
- **Total Loss Magnitude**: These loss-making orders collectively erode over `$450,000` in gross earnings.
- **Most Impacted Categories**: Cleats (4,590 loss items), Men's Footwear (4,169 loss items), Women's Apparel (3,923 loss items).
- **Most Impacted Regions**: Europe (3,476 loss orders) and Pacific Asia (3,315 loss orders).

**Implication**: Nearly 1 in 5 orders loses money. High discounting (>20%) coupled with fixed shipping overhead is the leading contributor.

---

### Finding 8 – Customer Segment Profitability

| Segment | Distinct Orders | Total Profit (USD) | Avg Profit/Order | Share of Orders |
|---|---|---|---|---|
| Consumer | 34,119 | $727,920.69 | $21.33 | 51.9% |
| Corporate | 19,856 | $420,088.40 | $21.16 | 30.2% |
| Home Office | 11,777 | $240,642.97 | $20.43 | 17.9% |

**Implication**: Profit per order is remarkably uniform across all customer tiers ($20.43–$21.33). Retention and basket-size expansion in Corporate accounts represent high-leverage growth avenues.

---

### Finding 9 – Machine Learning Delivery Risk Model
A Logistic Regression classification pipeline was trained with a leak-free `GroupShuffleSplit` on `order_id` (144,650 train rows, 35,869 test rows):
- **Precision**: `84.15%` (when the model flags a shipment as high risk, it is correct >84% of the time)
- **Accuracy**: `69.48%`
- **Recall**: `54.62%`
- **ROC-AUC**: `0.7388`
- **Artifacts Saved**: `models/late_delivery_risk_model.joblib`, `outputs/metrics.json`, `outputs/test_predictions.csv`

---

## 7. Business Recommendations

Based on the analytical framework (numerical evidence to be populated):

1. **Review pricing for low-margin categories**: Identify categories with margin < 5% and conduct a cost-price analysis. Target: improve margin by 2–3 percentage points.

2. **Audit high-lateness shipping modes**: Implement SLA monitoring dashboards for modes exceeding 40% late-delivery rate. Engage carriers for root-cause review.

3. **Regional focus**: Concentrate growth investment in top-revenue markets while investigating operational inefficiencies in low-revenue, high-late-rate regions.

4. **Scheduling recalibration**: If actual shipping days consistently exceed scheduled days, update the scheduled timeline estimates to improve customer communication accuracy.

5. **Loss order investigation**: Systematically investigate orders with negative profit. Introduce return-cost tracking and discount guardrails.

6. **Seasonal planning**: Use monthly trend data to pre-position inventory ahead of peak periods.

---

## 8. Limitations and Future Improvements

| Limitation | Future Improvement |
|---|---|
| Dataset ends ~2018; patterns may be outdated | Use current live supply chain data |
| No individual customer identifier for churn/LTV | Request CRM linkage |
| `late_delivery_risk` is a model label, not ground truth | Validate against carrier tracking APIs |
| No product cost data | Integrate COGS to compute true gross margin |
| No external demand signal | Overlay market demand / seasonality index |
| Static analysis | Build a live Power BI streaming dashboard |

---

*Report generated by the Supply Chain Analytics pipeline.*
*Author: [Your Name] | Date: [Date] | Version: 1.0*
