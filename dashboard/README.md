# Power BI Dashboard – Implementation Guide

## Overview
This guide walks you through building the **Supply Chain Sales, Profitability & Delivery Performance** dashboard in Power BI Desktop.

---

## Prerequisites
- Power BI Desktop (free download: https://powerbi.microsoft.com/desktop/)
- Cleaned dataset: `data/processed/supply_chain_clean.csv`
- DAX measures: `dashboard/power_bi_measures.dax`

---

## Step 1 – Import the Cleaned Dataset

1. Open Power BI Desktop → **Get Data** → **Text/CSV**
2. Navigate to `data/processed/supply_chain_clean.csv`
3. In the preview, verify columns are detected correctly
4. Click **Load**

> **Encoding note**: If characters appear garbled, use **Transform Data** → **Home** → **Source** → change encoding to `UTF-8`

---

## Step 2 – Verify Data Types in Power Query

| Column | Expected Type |
|---|---|
| `order_date_dateorders` | Date/Time |
| `shipping_date_dateorders` | Date/Time |
| `sales` | Decimal Number |
| `order_item_total` | Decimal Number |
| `order_profit_per_order` | Decimal Number |
| `order_item_quantity` | Whole Number |
| `late_delivery_risk` | Whole Number (0/1) |
| `days_for_shipping_real` | Whole Number |
| `days_for_shipment_scheduled` | Whole Number |
| `order_id` | Whole Number |
| `category_name`, `market`, `shipping_mode` | Text |

---

## Step 3 – Create the Date Table

In **Power BI Desktop** → **Modeling** → **New Table**, paste:

```dax
DateTable =
    VAR MinDate = MIN( supply_chain_clean[order_date_dateorders] )
    VAR MaxDate = MAX( supply_chain_clean[order_date_dateorders] )
    RETURN
        ADDCOLUMNS(
            CALENDAR( MinDate, MaxDate ),
            "Year",         YEAR([Date]),
            "Month",        MONTH([Date]),
            "Month Name",   FORMAT([Date], "MMM"),
            "Year-Month",   FORMAT([Date], "YYYY-MM"),
            "Quarter",      "Q" & QUARTER([Date]),
            "Week",         WEEKNUM([Date])
        )
```

Then:
- Right-click `DateTable` → **Mark as date table** → set **Date column** = `Date`
- In **Model view** → drag `DateTable[Date]` → `supply_chain_clean[order_date_dateorders]`

---

## Step 4 – Create All DAX Measures

Open `dashboard/power_bi_measures.dax` in a text editor.
For each measure block:
1. In Power BI → **Modeling** → **New Measure**
2. Paste the DAX expression
3. Name the measure exactly as labeled
4. Apply the formatting specified in the comments

Core measures to create first (in order):
1. `Total Sales`
2. `Total Profit`
3. `Total Item Revenue`
4. `Distinct Orders`
5. `Average Order Value`
6. `Avg Profit per Order`
7. `Profit Margin %`
8. `Late Deliveries`
9. `Total Eligible Shipments`
10. `Late Delivery Rate %`
11. `Avg Actual Shipping Days`
12. `Avg Scheduled Shipping Days`
13. `Avg Shipping Delay Days`
14. `Sales PM` (requires DateTable relationship)
15. `Sales MoM Growth %`
16. `Profit PM`
17. `Profit MoM Growth %`

---

## Step 5 – Dashboard Layout

### Page 1: Executive Overview

| Visual | Type | Fields |
|---|---|---|
| Total Revenue KPI card | Card | `Total Sales` |
| Total Profit KPI card | Card | `Total Profit` |
| Distinct Orders card | Card | `Distinct Orders` |
| Average Order Value card | Card | `Average Order Value` |
| Late Delivery Rate card | Card | `Late Delivery Rate %` |
| Monthly Sales & Profit | Line + Clustered Column | X: `DateTable[Year-Month]`, Bar: `Total Sales`, Line: `Total Profit` |
| Profit Margin Trend | Line chart | X: `DateTable[Year-Month]`, Y: `Profit Margin %` |
| **Slicers**: Market, Customer Segment, Order Year | Slicer | `market`, `customer_segment`, `DateTable[Year]` |

---

### Page 2: Product & Regional Performance

| Visual | Type | Fields |
|---|---|---|
| Sales by Category | Horizontal Bar | Y: `category_name`, X: `Total Sales` – sorted descending |
| Profit Margin by Category | Horizontal Bar | Y: `category_name`, X: `Profit Margin %` – color: conditional (green/red) |
| Top 10 Products by Sales | Clustered Bar | Top N filter on `product_name` |
| Bottom 10 Products by Profit | Table | `product_name`, `Total Sales`, `Total Profit`, `Profit Margin %` |
| Revenue by Market | Donut/Treemap | Legend: `market`, Values: `Total Sales` |
| Regional Profit | Map or Bar | Region: `order_region`, Value: `Total Profit` |
| **Slicers**: Market, Category, Department | Slicer | |

---

### Page 3: Delivery Performance

| Visual | Type | Fields |
|---|---|---|
| Late Delivery Rate (overall) | KPI Card | `Late Delivery Rate %` |
| Late Rate by Shipping Mode | Clustered Bar | X: `shipping_mode`, Y: `Late Delivery Rate %` |
| Actual vs Scheduled Days | Clustered Bar | X: `shipping_mode`, Values: `Avg Actual Shipping Days`, `Avg Scheduled Shipping Days` |
| Late Rate by Region | Bar or Map | X: `order_region` or `market`, Y: `Late Delivery Rate %` |
| Delivery Performance Trend | Line | X: `DateTable[Year-Month]`, Y: `Late Delivery Rate %` |
| **Slicers**: Shipping Mode, Market, Date Range | Slicer | |

---

## Step 6 – Formatting Guidelines

### Color Palette
| Purpose | Hex |
|---|---|
| Primary (Sales) | `#2196F3` |
| Profit/Positive | `#4CAF50` |
| Loss/Negative | `#F44336` |
| Warning/Caution | `#FF9800` |
| Neutral | `#607D8B` |
| Background | `#F5F5F5` |
| Card Background | `#FFFFFF` |

### Typography
- Title font: **Segoe UI Semibold**, 14–16pt
- Body font: **Segoe UI**, 10–11pt
- KPI values: **Segoe UI Bold**, 24–28pt

### General Rules
- Add data labels to bar charts
- Use consistent padding (16px) between visuals
- Include a page title in a text box at the top of each page
- Add a footer: "Source: DataCo Smart Supply Chain Dataset | Analysis: [Your Name] | Date: [Date]"

---

## Step 7 – Screenshots

After completing the dashboard:
1. Take full-page screenshots of all 3 pages
2. Save as PNG to `screenshots/`
3. Name them: `dashboard_page1_overview.png`, `dashboard_page2_product.png`, `dashboard_page3_delivery.png`
4. Update `README.md` to reference these screenshots

---

## Step 8 – Export & Share

- Save the `.pbix` file locally (do **not** commit it to Git – it contains embedded data)
- Export to PDF: **File** → **Export** → **Export to PDF** for sharing
- Optionally publish to Power BI Service: **Home** → **Publish** → select workspace
