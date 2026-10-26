# 📦 Supply Chain Sales, Profitability & Delivery Performance Analytics

> A complete, portfolio-quality end-to-end data analytics project built with Python, pandas, Matplotlib/Seaborn, and Power BI.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Pandas](https://img.shields.io/badge/pandas-3.x-150458?logo=pandas)
![License](https://img.shields.io/badge/License-MIT-green)
![Tests](https://img.shields.io/badge/Tests-28%20Passed-brightgreen)

---

## 📌 Business Problem

Supply chain organizations generate enormous volumes of transactional data daily. Without structured analysis, leadership cannot answer fundamental questions:

- Which products and regions drive the most revenue and profit?
- How many shipments are delivered late, and why?
- Which shipping modes have the worst delivery performance?
- Where are we losing money at the order level?

This project answers these questions using a real-world public supply chain dataset.

---

## 🎯 Project Objectives

1. Build a reproducible Python analytics pipeline from raw data to business insight
2. Perform rigorous data cleaning with a full audit trail
3. Compute accurate, double-count-free KPIs at the correct transaction grain
4. Generate publication-quality charts for trend, product, regional, and delivery analysis
5. Design a Power BI dashboard with correct DAX measures
6. Document findings and recommendations in a structured business report
7. Publish the project publicly on GitHub

---

## 📊 Dataset

| Attribute | Detail |
|---|---|
| **Name** | DataCo Smart Supply Chain for Big Data Analysis |
| **Source** | [Kaggle](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) |
| **File** | `DataCoSupplyChainDataset.csv` |
| **License** | CDLA-Sharing-1.0 |
| **Grain** | Order-item (one row per product line per order) |
| **Size** | ~180,000 rows × 53 columns |
| **Period** | ~2015 – 2018 |

> **Attribution**: Dataset published by Fabian Constante, Fernando Silva, António Pereira on Kaggle. Used under CDLA-Sharing-1.0.

### ⚠️ Dataset Download Instructions

The raw dataset is **not included** in this repository (licensing + file size).

**Option A – Kaggle CLI (recommended)**
```bash
# 1. Install kaggle CLI
pip install kaggle

# 2. Download your Kaggle API key from https://kaggle.com/account → API → Create New Token
# 3. Place kaggle.json in ~/.kaggle/ (macOS/Linux) or C:\Users\<user>\.kaggle\ (Windows)
chmod 600 ~/.kaggle/kaggle.json

# 4. Download the dataset
kaggle datasets download -d shashwatwork/dataco-smart-supply-chain-for-big-data-analysis

# 5. Unzip and move
unzip dataco-smart-supply-chain-for-big-data-analysis.zip
mv DataCoSupplyChainDataset.csv data/raw/
```

**Option B – Browser Download**
1. Visit: https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis
2. Click **Download** (login required)
3. Unzip the archive
4. Copy `DataCoSupplyChainDataset.csv` → `data/raw/DataCoSupplyChainDataset.csv`

---

## 🛠️ Technology Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Core language |
| pandas | 3.x | Data manipulation |
| NumPy | 1.26+ | Numerical computing |
| Matplotlib | 3.8+ | Base charts |
| Seaborn | 0.13+ | Statistical charts |
| Jupyter Notebook | 7.x | Exploratory analysis |
| scikit-learn | 1.3+ | Optional ML extension |
| pytest | 8.x | Automated testing |
| Power BI Desktop | Latest | Interactive dashboard |
| Git / GitHub | — | Version control |

---

## 📁 Project Structure

```
supply-chain-analytics/
├── data/
│   ├── raw/                          # Raw dataset (not committed)
│   └── processed/                    # Cleaned CSV + quality reports
├── notebooks/
│   └── supply_chain_analysis.ipynb   # Full EDA + analysis notebook
├── src/
│   ├── __init__.py
│   ├── clean_data.py                 # Cleaning pipeline
│   ├── analyze_data.py               # Business analysis + charts
│   └── validate_data.py              # Post-cleaning validation
├── outputs/
│   ├── summary_statistics.csv
│   ├── monthly_sales.csv
│   ├── category_performance.csv
│   ├── regional_performance.csv
│   ├── delivery_analysis.csv
│   ├── descriptive_statistics.csv
│   └── charts/                       # All generated PNG charts
├── dashboard/
│   ├── README.md                     # Power BI step-by-step guide
│   └── power_bi_measures.dax         # All DAX measures
├── screenshots/                      # Dashboard screenshots (add after Power BI)
│   └── [PLACEHOLDER - see below]
├── reports/
│   └── insights_report.md            # Evidence-based business report
├── tests/
│   └── test_pipeline.py              # 28 automated tests (all passing)
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## ⚙️ Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/supply-chain-analytics.git
cd supply-chain-analytics

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the dataset (see Dataset section above)
#    Place at: data/raw/DataCoSupplyChainDataset.csv
```

---

## 🔄 How to Reproduce the Analysis

### Option A: One-Command Master Runner (Recommended)

Run the entire end-to-end pipeline (cleaning, validation, analytics, ML model, tests) with a single command:

```bash
python main.py
```

### Option B: Step-by-Step Execution

Run each phase individually from the project root:

```bash
# Phase 1 – Exploratory Notebook
jupyter notebook notebooks/supply_chain_analysis.ipynb

# Phase 2 – Data Cleaning
python src/clean_data.py \
  --input  data/raw/DataCoSupplyChainDataset.csv \
  --output data/processed/supply_chain_clean.csv \
  --report data/processed/cleaning_report.csv

# Phase 3 – Validation
python src/validate_data.py \
  --input  data/processed/supply_chain_clean.csv \
  --report data/processed/validation_report.csv

# Phase 4 – Business Analysis & Charts
python src/analyze_data.py \
  --input      data/processed/supply_chain_clean.csv \
  --output-dir outputs/

# Phase 5 – Machine Learning Model Training
python src/train_model.py

# Phase 6 – Automated Test Suite
python -m pytest tests/test_pipeline.py -v
```

**Configurable path**: All scripts accept a `--input` argument so the project runs on macOS, Windows, or Linux without code changes.

---

## 🧹 Data Cleaning Methodology

| Step | Rows Affected | Action |
|---|---|---|
| Load | All rows | `latin-1` encoding; schema inspection |
| Column standardisation | All columns | Lowercase + underscore naming |
| Exact duplicate removal | Reported in `cleaning_report.csv` | `drop_duplicates()` |
| Date parsing | Reported | `errors='coerce'` → NaT for invalids |
| Numeric conversion | Reported | `errors='coerce'` → NaN for invalids |
| Missing value audit | Reported | Record only; no imputation |
| Non-negative checks | Reported | Flag only; not deleted |
| Categorical standardisation | All categorical cols | Strip + title-case |
| Derived columns | All rows | `shipping_delay_days`, `order_year_month`, `is_late_derived` |

**Key principles**:
- Original raw file never modified
- Negative-profit records preserved (they are valid business events)
- Missing values audited and reported, never silently zeroed
- Every step records number of rows affected

---

## ❓ Analysis Questions Answered

1. What are total sales, total profit, total item revenue, and distinct orders?
2. How do monthly sales and profit trend over time?
3. Which product categories generate the most sales and profit?
4. Which categories have weak or negative profitability?
5. Which markets or regions contribute most revenue and profit?
6. What percentage of shipments are late?
7. How does late-delivery performance vary by shipping mode and region?
8. How do actual shipping durations compare with scheduled durations?

---

## 📐 KPI Definitions

| KPI | Definition |
|---|---|
| **Total Sales** | `SUM(sales)` — all order-item rows |
| **Total Profit** | `SUM(order_profit_per_order)` after `ORDER_ID` deduplication |
| **Distinct Orders** | `COUNT DISTINCT(order_id)` |
| **Avg Order Value (AOV)** | `Total Sales / Distinct Orders` |
| **Late Delivery Rate %** | `Late shipments / Total eligible shipments × 100` |
| **Avg Shipping Delay** | `MEAN(actual_days − scheduled_days)` |
| **Profit Margin %** | `Total Profit / Total Sales × 100` |

---

## 📈 Key Findings

> *Findings below will be populated after running the full pipeline on the downloaded dataset.*
> *See `reports/insights_report.md` for the complete analysis template.*

| Finding | Evidence |
|---|---|
| Total Revenue | `$[run pipeline]` |
| Total Profit | `$[run pipeline]` |
| Distinct Orders | `[run pipeline]` |
| Top Category | `[run pipeline]` |
| Late Delivery Rate | `[run pipeline]%` |
| Worst Shipping Mode | `[run pipeline]` |

---

## 🖥️ Dashboard Screenshots

> **⚠️ PLACEHOLDER** – Screenshots must be captured after building the Power BI dashboard.

**Checklist for dashboard screenshots:**
- [ ] Open Power BI Desktop
- [ ] Load `data/processed/supply_chain_clean.csv`
- [ ] Create Date Table and all DAX measures (see `dashboard/power_bi_measures.dax`)
- [ ] Build all 3 dashboard pages (see `dashboard/README.md`)
- [ ] Take full-page screenshots (Windows: Snipping Tool / Snip & Sketch; macOS: Cmd+Shift+4)
- [ ] Save to `screenshots/` as:
  - `dashboard_page1_overview.png`
  - `dashboard_page2_product.png`
  - `dashboard_page3_delivery.png`
- [ ] Replace placeholders in this README with:

```markdown
![Executive Overview](screenshots/dashboard_page1_overview.png)
![Product & Regional](screenshots/dashboard_page2_product.png)
![Delivery Performance](screenshots/dashboard_page3_delivery.png)
```

---

## 🧪 Testing

```bash
python -m pytest tests/test_pipeline.py -v
```

**Test Results (verified)**:
```
28 passed, 1 warning in 0.41s
```

Tests cover:
- Column standardisation
- Exact duplicate removal
- Date parsing (valid + invalid)
- Numeric conversion
- Missing value audit
- Derived column creation
- Late delivery rate calculation
- Distinct order counting
- Profit aggregation (no double-counting)
- Monthly and category aggregation accuracy
- Schema validation
- Validation module

All tests use **synthetic fixtures** clearly labeled as TEST DATA. No real data is mixed into tests.

---

## ⚠️ Limitations

- Dataset ends ~2018; current supply chain dynamics may differ
- `late_delivery_risk` is a pre-computed label, not independently derived from order vs. shipping dates
- No individual customer ID for cohort or retention analysis
- Profit is at order level — item-level margins cannot be computed without COGS data
- Power BI dashboard requires Windows or macOS with Power BI Desktop installed

---

## 🚀 Future Enhancements

- [ ] Machine learning model to predict late delivery risk (logistic regression / gradient boosting)
- [ ] Customer segmentation using RFM analysis
- [ ] Demand forecasting with ARIMA or Prophet
- [ ] Power BI Service deployment with auto-refresh
- [ ] REST API exposing KPIs in real time
- [ ] Docker containerization for fully portable execution

---

## 👤 Author

**[Your Name]**
- GitHub: [@your-username](https://github.com/your-username)
- LinkedIn: [linkedin.com/in/your-profile](https://linkedin.com/in/your-profile)
- Email: your.email@example.com

---

## 🤝 Contributing

Contributions are welcome. Please:
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

*Built for portfolio demonstration and internship applications.*
*Dataset: DataCo Smart Supply Chain (Kaggle) | License: MIT + CDLA-Sharing-1.0*
