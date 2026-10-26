"""
analyze_data.py
===============
Business analysis module for the DataCo Supply Chain dataset.

Usage
-----
    python src/analyze_data.py \
        --input data/processed/supply_chain_clean.csv \
        --output-dir outputs/
"""

import os
import sys
import argparse
import logging
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")          # Non-interactive backend for script usage
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Plotting style ──────────────────────────────────────────────────────────
plt.style.use("seaborn-v0_8-whitegrid")
PALETTE = "viridis"
FIG_DPI = 150
sns.set_palette("muted")


def _save_fig(fig, output_dir: str, filename: str) -> str:
    """Save a matplotlib figure and return the file path."""
    path = os.path.join(output_dir, filename)
    fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Chart saved: %s", path)
    return path


def load_cleaned_data(path: str) -> pd.DataFrame:
    """Load cleaned CSV, parsing dates automatically."""
    df = pd.read_csv(path, low_memory=False, parse_dates=["order_date_dateorders",
                                                            "shipping_date_dateorders"])
    logger.info("Cleaned data loaded: %d rows × %d cols", *df.shape)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# KPI 1 – Top-Level KPIs
# ─────────────────────────────────────────────────────────────────────────────
def compute_toplevel_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    KPIs:
      • Total Sales          = sum(sales)
      • Total Profit         = sum(order_profit_per_order) — per unique order
      • Total Item Revenue   = sum(order_item_total) — row grain
      • Distinct Orders      = count of unique order_id values
      • Avg Order Value (AOV)= Total Sales / Distinct Orders
      • Avg Profit/Order     = Total Profit / Distinct Orders
    """
    total_sales = df["sales"].sum() if "sales" in df.columns else np.nan

    # Profit is at order level – deduplicate by order_id before summing
    if "order_id" in df.columns and "order_profit_per_order" in df.columns:
        order_level = df.drop_duplicates(subset=["order_id"])
        total_profit = order_level["order_profit_per_order"].sum()
        distinct_orders = order_level["order_id"].nunique()
    else:
        total_profit = df.get("order_profit_per_order", pd.Series(dtype=float)).sum()
        distinct_orders = len(df)

    total_item_revenue = df["order_item_total"].sum() if "order_item_total" in df.columns else np.nan
    aov = total_sales / distinct_orders if distinct_orders > 0 else np.nan
    avg_profit_per_order = total_profit / distinct_orders if distinct_orders > 0 else np.nan

    kpi_df = pd.DataFrame([{
        "metric": "Total Sales (USD)",
        "value": round(total_sales, 2),
        "note": "Sum of sales column across all order-items"
    }, {
        "metric": "Total Profit (USD)",
        "value": round(total_profit, 2),
        "note": "Sum of order_profit_per_order deduplicated by order_id"
    }, {
        "metric": "Total Item Revenue (USD)",
        "value": round(total_item_revenue, 2),
        "note": "Sum of order_item_total across all rows"
    }, {
        "metric": "Distinct Orders",
        "value": int(distinct_orders),
        "note": "Count of unique order_id values"
    }, {
        "metric": "Average Order Value (USD)",
        "value": round(aov, 2),
        "note": "Total Sales / Distinct Orders"
    }, {
        "metric": "Average Profit Per Order (USD)",
        "value": round(avg_profit_per_order, 2),
        "note": "Total Profit / Distinct Orders"
    }])

    logger.info("Top-level KPIs computed.")
    for _, row in kpi_df.iterrows():
        val = row["value"]
        formatted_val = f"{val:,.2f}" if isinstance(val, (int, float, np.number)) else str(val)
        logger.info("  %-35s %s", row["metric"], formatted_val)

    return kpi_df


# ─────────────────────────────────────────────────────────────────────────────
# KPI 2 – Monthly Sales & Profit Trend
# ─────────────────────────────────────────────────────────────────────────────
def compute_monthly_trends(df: pd.DataFrame, output_dir: str) -> pd.DataFrame:
    """Aggregate sales and profit by year-month."""
    if "order_year_month" not in df.columns:
        logger.warning("'order_year_month' not found – skipping monthly trends.")
        return pd.DataFrame()

    monthly = (
        df.groupby("order_year_month", observed=True)
        .agg(
            total_sales=("sales", "sum"),
            total_item_revenue=("order_item_total", "sum"),
            order_count=("order_id", "nunique"),
        )
        .reset_index()
        .sort_values("order_year_month")
    )

    # Profit at order level – merge back
    if "order_id" in df.columns and "order_profit_per_order" in df.columns:
        order_profit = (
            df.drop_duplicates(subset=["order_id"])
            .groupby("order_year_month", observed=True)["order_profit_per_order"]
            .sum()
            .reset_index()
            .rename(columns={"order_profit_per_order": "total_profit"})
        )
        monthly = monthly.merge(order_profit, on="order_year_month", how="left")
    else:
        monthly["total_profit"] = np.nan

    monthly["profit_margin_pct"] = (
        (monthly["total_profit"] / monthly["total_sales"]) * 100
    ).round(2)

    # ── Chart ─────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    x = range(len(monthly))
    labels = monthly["order_year_month"].tolist()

    axes[0].bar(x, monthly["total_sales"] / 1e6, color="#2196F3", alpha=0.85, label="Sales")
    axes[0].plot(x, monthly["total_profit"] / 1e6, color="#F44336", marker="o",
                 linewidth=2, markersize=4, label="Profit")
    axes[0].set_ylabel("USD (Millions)")
    axes[0].set_title("Monthly Sales & Profit Trend", fontsize=14, fontweight="bold")
    axes[0].legend()
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.1f}M"))

    axes[1].fill_between(x, monthly["profit_margin_pct"], alpha=0.5, color="#4CAF50")
    axes[1].plot(x, monthly["profit_margin_pct"], color="#388E3C", linewidth=2)
    axes[1].axhline(0, color="red", linestyle="--", linewidth=1)
    axes[1].set_ylabel("Profit Margin (%)")
    axes[1].set_title("Monthly Profit Margin %", fontsize=14, fontweight="bold")
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.1f}%"))

    step = max(1, len(labels) // 12)
    axes[1].set_xticks(list(x)[::step])
    axes[1].set_xticklabels(labels[::step], rotation=45, ha="right")

    fig.tight_layout()
    _save_fig(fig, output_dir, "01_monthly_sales_profit.png")

    return monthly


# ─────────────────────────────────────────────────────────────────────────────
# KPI 3 – Category Performance
# ─────────────────────────────────────────────────────────────────────────────
def compute_category_performance(df: pd.DataFrame, output_dir: str) -> pd.DataFrame:
    """Sales, profit, and margin by product category."""
    if "category_name" not in df.columns:
        logger.warning("'category_name' not found – skipping category analysis.")
        return pd.DataFrame()

    cat = (
        df.groupby("category_name", observed=True)
        .agg(
            total_sales=("sales", "sum"),
            total_item_revenue=("order_item_total", "sum"),
            order_item_count=("order_id", "count"),
            distinct_orders=("order_id", "nunique"),
        )
        .reset_index()
    )

    if "order_profit_per_order" in df.columns:
        cat_profit = (
            df.drop_duplicates(subset=["order_id"])
            .groupby("category_name", observed=True)["order_profit_per_order"]
            .sum()
            .reset_index()
            .rename(columns={"order_profit_per_order": "total_profit"})
        )
        cat = cat.merge(cat_profit, on="category_name", how="left")
    else:
        cat["total_profit"] = np.nan

    cat["profit_margin_pct"] = (cat["total_profit"] / cat["total_sales"] * 100).round(2)
    cat = cat.sort_values("total_sales", ascending=False)

    # ── Chart ─────────────────────────────────────────────────────
    top_n = min(15, len(cat))
    plot_df = cat.head(top_n)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Left: Sales by category
    bars = axes[0].barh(plot_df["category_name"], plot_df["total_sales"] / 1e6,
                        color=sns.color_palette("Blues_d", top_n))
    axes[0].set_xlabel("Total Sales (USD Millions)")
    axes[0].set_title(f"Top {top_n} Categories by Sales", fontsize=13, fontweight="bold")
    axes[0].invert_yaxis()

    # Right: Profit margin
    colors = ["#4CAF50" if v >= 0 else "#F44336" for v in plot_df["profit_margin_pct"]]
    axes[1].barh(plot_df["category_name"], plot_df["profit_margin_pct"], color=colors)
    axes[1].set_xlabel("Profit Margin (%)")
    axes[1].set_title("Profit Margin % by Category", fontsize=13, fontweight="bold")
    axes[1].axvline(0, color="black", linewidth=0.8)
    axes[1].invert_yaxis()

    fig.tight_layout()
    _save_fig(fig, output_dir, "02_category_performance.png")

    return cat


# ─────────────────────────────────────────────────────────────────────────────
# KPI 4 – Regional Performance
# ─────────────────────────────────────────────────────────────────────────────
def compute_regional_performance(df: pd.DataFrame, output_dir: str) -> pd.DataFrame:
    """Revenue and profit by market / region."""
    group_col = next((c for c in ["market", "order_region", "order_country"]
                      if c in df.columns), None)
    if group_col is None:
        logger.warning("No regional column found – skipping regional analysis.")
        return pd.DataFrame()

    reg = (
        df.groupby(group_col, observed=True)
        .agg(
            total_sales=("sales", "sum"),
            order_count=("order_id", "nunique"),
        )
        .reset_index()
    )

    if "order_profit_per_order" in df.columns:
        reg_profit = (
            df.drop_duplicates(subset=["order_id"])
            .groupby(group_col, observed=True)["order_profit_per_order"]
            .sum()
            .reset_index()
            .rename(columns={"order_profit_per_order": "total_profit"})
        )
        reg = reg.merge(reg_profit, on=group_col, how="left")
    else:
        reg["total_profit"] = np.nan

    reg["profit_margin_pct"] = (reg["total_profit"] / reg["total_sales"] * 100).round(2)
    reg = reg.sort_values("total_sales", ascending=False)

    # ── Chart ─────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    colors_sales = sns.color_palette("Blues_d", len(reg))
    axes[0].bar(reg[group_col], reg["total_sales"] / 1e6, color=colors_sales)
    axes[0].set_xlabel(group_col.replace("_", " ").title())
    axes[0].set_ylabel("Total Sales (USD Millions)")
    axes[0].set_title(f"Revenue by {group_col.replace('_',' ').title()}", fontsize=13, fontweight="bold")
    axes[0].tick_params(axis="x", rotation=30)

    colors_profit = ["#4CAF50" if v >= 0 else "#F44336" for v in reg["profit_margin_pct"]]
    axes[1].bar(reg[group_col], reg["profit_margin_pct"], color=colors_profit)
    axes[1].set_xlabel(group_col.replace("_", " ").title())
    axes[1].set_ylabel("Profit Margin (%)")
    axes[1].set_title(f"Profit Margin % by {group_col.replace('_',' ').title()}", fontsize=13, fontweight="bold")
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].tick_params(axis="x", rotation=30)

    fig.tight_layout()
    _save_fig(fig, output_dir, "03_regional_performance.png")

    return reg


# ─────────────────────────────────────────────────────────────────────────────
# KPI 5 – Delivery Performance
# ─────────────────────────────────────────────────────────────────────────────
def compute_delivery_performance(df: pd.DataFrame, output_dir: str) -> pd.DataFrame:
    """Late delivery rate by shipping mode and region."""

    # Determine which late-delivery indicator to use
    if "late_delivery_risk" in df.columns:
        # Dataset contains pre-computed risk flag (0/1 or string)
        df = df.copy()
        df["is_late"] = pd.to_numeric(df["late_delivery_risk"], errors="coerce").fillna(0).astype(int)
        late_col = "is_late"
        late_source = "late_delivery_risk (pre-computed label)"
    elif "is_late_derived" in df.columns:
        late_col = "is_late_derived"
        late_source = "is_late_derived (actual > scheduled days)"
    else:
        logger.warning("No late-delivery indicator found.")
        return pd.DataFrame()

    logger.info("Late delivery source: %s", late_source)

    # Overall late rate
    overall_late_pct = (df[late_col].sum() / len(df) * 100)
    logger.info("Overall Late Delivery Rate: %.2f%%", overall_late_pct)

    results = []

    # ── By shipping mode ─────────────────────────────────────────
    if "shipping_mode" in df.columns:
        by_mode = (
            df.groupby("shipping_mode", observed=True)
            .agg(
                total_shipments=(late_col, "count"),
                late_shipments=(late_col, "sum"),
                avg_actual_days=("days_for_shipping_real", "mean"),
                avg_scheduled_days=("days_for_shipment_scheduled", "mean"),
            )
            .reset_index()
        )
        by_mode["late_rate_pct"] = (by_mode["late_shipments"] / by_mode["total_shipments"] * 100).round(2)
        by_mode["dimension"] = "shipping_mode"
        by_mode = by_mode.rename(columns={"shipping_mode": "segment"})
        results.append(by_mode)

    # ── By market/region ──────────────────────────────────────────
    group_col = next((c for c in ["market", "order_region"] if c in df.columns), None)
    if group_col:
        by_region = (
            df.groupby(group_col, observed=True)
            .agg(
                total_shipments=(late_col, "count"),
                late_shipments=(late_col, "sum"),
                avg_actual_days=("days_for_shipping_real", "mean"),
                avg_scheduled_days=("days_for_shipment_scheduled", "mean"),
            )
            .reset_index()
        )
        by_region["late_rate_pct"] = (by_region["late_shipments"] / by_region["total_shipments"] * 100).round(2)
        by_region["dimension"] = group_col
        by_region = by_region.rename(columns={group_col: "segment"})
        results.append(by_region)

    delivery_df = pd.concat(results, ignore_index=True) if results else pd.DataFrame()

    # ── Charts ────────────────────────────────────────────────────
    if "shipping_mode" in df.columns:
        mode_df = delivery_df[delivery_df["dimension"] == "shipping_mode"].copy()
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Late rate by shipping mode
        colors = sns.color_palette("RdYlGn_r", len(mode_df))
        axes[0].bar(mode_df["segment"], mode_df["late_rate_pct"], color=colors)
        axes[0].set_ylabel("Late Delivery Rate (%)")
        axes[0].set_title("Late Delivery Rate by Shipping Mode", fontsize=13, fontweight="bold")
        axes[0].tick_params(axis="x", rotation=20)
        for bar, val in zip(axes[0].patches, mode_df["late_rate_pct"]):
            axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                         f"{val:.1f}%", ha="center", fontsize=9)

        # Actual vs Scheduled days
        x = np.arange(len(mode_df))
        w = 0.35
        axes[1].bar(x - w/2, mode_df["avg_actual_days"], w, label="Actual Days", color="#2196F3")
        axes[1].bar(x + w/2, mode_df["avg_scheduled_days"], w, label="Scheduled Days", color="#FF9800")
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(mode_df["segment"], rotation=20)
        axes[1].set_ylabel("Average Days")
        axes[1].set_title("Actual vs Scheduled Shipping Days", fontsize=13, fontweight="bold")
        axes[1].legend()

        fig.suptitle(f"Delivery Performance  |  Overall Late Rate: {overall_late_pct:.1f}%\n"
                     f"Source: {late_source}", fontsize=10, color="gray")
        fig.tight_layout()
        _save_fig(fig, output_dir, "04_delivery_performance.png")

    return delivery_df


# ─────────────────────────────────────────────────────────────────────────────
# KPI 6 – Summary Statistics
# ─────────────────────────────────────────────────────────────────────────────
def compute_summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Descriptive statistics for all numeric columns."""
    numeric_df = df.select_dtypes(include=np.number)
    stats = numeric_df.describe().T
    stats.index.name = "column"
    stats = stats.reset_index()
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# Profitability distribution chart
# ─────────────────────────────────────────────────────────────────────────────
def plot_profitability_distribution(df: pd.DataFrame, output_dir: str) -> None:
    """Plot distribution of profit per order."""
    col = "order_profit_per_order"
    if col not in df.columns:
        return
    data = df.drop_duplicates(subset=["order_id"])[col].dropna() if "order_id" in df.columns else df[col].dropna()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Histogram
    axes[0].hist(data, bins=60, color="#5C6BC0", edgecolor="white", alpha=0.85)
    axes[0].axvline(data.mean(), color="red", linestyle="--", label=f"Mean: ${data.mean():,.0f}")
    axes[0].axvline(data.median(), color="orange", linestyle="--", label=f"Median: ${data.median():,.0f}")
    axes[0].set_xlabel("Profit per Order (USD)")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("Profit per Order – Distribution", fontsize=13, fontweight="bold")
    axes[0].legend()

    # Box plot by customer segment
    if "customer_segment" in df.columns:
        seg_data = df.drop_duplicates(subset=["order_id"])[["customer_segment", col]].dropna() \
                   if "order_id" in df.columns else df[["customer_segment", col]].dropna()
        segments = seg_data["customer_segment"].unique()
        seg_profits = [seg_data[seg_data["customer_segment"] == s][col].values for s in segments]
        boxplot_kwargs = dict(patch_artist=True,
                             boxprops=dict(facecolor="#90CAF9"),
                             medianprops=dict(color="red", linewidth=2))
        try:
            axes[1].boxplot(seg_profits, tick_labels=segments, **boxplot_kwargs)
        except TypeError:
            axes[1].boxplot(seg_profits, labels=segments, **boxplot_kwargs)
        axes[1].set_xlabel("Customer Segment")
        axes[1].set_ylabel("Profit per Order (USD)")
        axes[1].set_title("Profit Distribution by Customer Segment", fontsize=13, fontweight="bold")
        axes[1].tick_params(axis="x", rotation=20)
    else:
        axes[1].set_visible(False)

    fig.tight_layout()
    _save_fig(fig, output_dir, "05_profitability_distribution.png")


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────
def run_analysis(input_path: str, output_dir: str) -> dict:
    """Run the full analysis suite and save all outputs."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    charts_dir = os.path.join(output_dir, "charts")
    Path(charts_dir).mkdir(exist_ok=True)

    df = load_cleaned_data(input_path)

    outputs = {}

    # KPI 1
    kpi_df = compute_toplevel_kpis(df)
    path = os.path.join(output_dir, "summary_statistics.csv")
    kpi_df.to_csv(path, index=False)
    outputs["kpis"] = kpi_df
    logger.info("Saved: %s", path)

    # KPI 2
    monthly = compute_monthly_trends(df, charts_dir)
    if not monthly.empty:
        path = os.path.join(output_dir, "monthly_sales.csv")
        monthly.to_csv(path, index=False)
        outputs["monthly"] = monthly
        logger.info("Saved: %s", path)

    # KPI 3
    cat = compute_category_performance(df, charts_dir)
    if not cat.empty:
        path = os.path.join(output_dir, "category_performance.csv")
        cat.to_csv(path, index=False)
        outputs["category"] = cat
        logger.info("Saved: %s", path)

    # KPI 4
    reg = compute_regional_performance(df, charts_dir)
    if not reg.empty:
        path = os.path.join(output_dir, "regional_performance.csv")
        reg.to_csv(path, index=False)
        outputs["regional"] = reg
        logger.info("Saved: %s", path)

    # KPI 5
    delivery = compute_delivery_performance(df, charts_dir)
    if not delivery.empty:
        path = os.path.join(output_dir, "delivery_analysis.csv")
        delivery.to_csv(path, index=False)
        outputs["delivery"] = delivery
        logger.info("Saved: %s", path)

    # KPI 6 – Summary stats
    stats = compute_summary_statistics(df)
    path = os.path.join(output_dir, "descriptive_statistics.csv")
    stats.to_csv(path, index=False)
    outputs["stats"] = stats
    logger.info("Saved: %s", path)

    # Profitability chart
    plot_profitability_distribution(df, charts_dir)

    logger.info("Analysis complete. All outputs in: %s", output_dir)
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DataCo Supply Chain – Business Analysis")
    parser.add_argument("--input", default=os.path.join("data", "processed", "supply_chain_clean.csv"))
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    run_analysis(args.input, args.output_dir)
