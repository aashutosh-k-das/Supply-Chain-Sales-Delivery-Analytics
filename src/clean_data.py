"""
clean_data.py
=============
Reusable, reproducible data-cleaning pipeline for the DataCo Supply Chain dataset.

Usage
-----
    python src/clean_data.py --input data/raw/DataCoSupplyChainDataset.csv \
                              --output data/processed/supply_chain_clean.csv \
                              --report data/processed/cleaning_report.csv
"""

import os
import sys
import argparse
import warnings
import logging
from pathlib import Path

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants – known column semantics for the DataCo dataset
# These are mapped AFTER standardising header names (lowercase + underscores).
# ─────────────────────────────────────────────────────────────────────────────
DATE_COLUMNS = [
    "order_date_dateorders",
    "shipping_date_dateorders",
]

NUMERIC_COLUMNS = [
    "sales",
    "order_item_total",
    "order_item_product_price",
    "order_item_discount",
    "order_item_discount_rate",
    "order_item_profit_ratio",
    "order_item_quantity",
    "order_profit_per_order",
    "benefit_per_order",
    "order_item_cardprod_id",
    "days_for_shipping_real",
    "days_for_shipment_scheduled",
    "latitude",
    "longitude",
]

# Columns that must be positive (or zero)
NON_NEGATIVE_COLS = [
    "sales",
    "order_item_quantity",
    "order_item_product_price",
    "days_for_shipping_real",
    "days_for_shipment_scheduled",
]

CATEGORICAL_COLUMNS = [
    "type",
    "delivery_status",
    "late_delivery_risk",
    "category_name",
    "customer_segment",
    "department_name",
    "market",
    "order_country",
    "order_region",
    "order_state",
    "order_city",
    "order_status",
    "shipping_mode",
    "customer_country",
    "customer_state",
    "customer_city",
]


def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase column names and replace spaces / special chars with underscore."""
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return df


def parse_dates(df: pd.DataFrame, date_cols: list, report: list) -> pd.DataFrame:
    """Safely parse date columns; report unparseable counts."""
    df = df.copy()
    for col in date_cols:
        if col not in df.columns:
            logger.warning("Date column '%s' not found – skipping.", col)
            continue
        original_dtype = df[col].dtype
        if pd.api.types.is_datetime64_any_dtype(original_dtype):
            logger.info("'%s' already datetime – skipping parse.", col)
            continue
        parsed = pd.to_datetime(df[col], errors="coerce")
        bad = parsed.isna() & df[col].notna()
        n_bad = bad.sum()
        if n_bad > 0:
            logger.warning("'%s': %d values could not be parsed as dates.", col, n_bad)
        report.append(
            {"step": "parse_dates", "column": col, "rows_affected": int(n_bad),
             "action": "coerced to NaT"}
        )
        df[col] = parsed
    return df


def convert_numerics(df: pd.DataFrame, numeric_cols: list, report: list) -> pd.DataFrame:
    """Convert numeric columns; count and report coercions."""
    df = df.copy()
    for col in numeric_cols:
        if col not in df.columns:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        original_non_null = df[col].notna().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        new_null = df[col].isna().sum()
        n_coerced = new_null - (len(df) - original_non_null)
        n_coerced = max(n_coerced, 0)
        if n_coerced > 0:
            logger.warning("'%s': %d values coerced to NaN.", col, n_coerced)
        report.append(
            {"step": "convert_numeric", "column": col, "rows_affected": int(n_coerced),
             "action": "coerced to NaN"}
        )
    return df


def remove_exact_duplicates(df: pd.DataFrame, report: list) -> pd.DataFrame:
    """Remove fully identical rows (all columns identical)."""
    n_before = len(df)
    df = df.drop_duplicates()
    n_removed = n_before - len(df)
    logger.info("Exact duplicates removed: %d", n_removed)
    report.append(
        {"step": "remove_exact_duplicates", "column": "ALL", "rows_affected": n_removed,
         "action": "dropped"}
    )
    return df


def audit_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Return a summary table of missing values."""
    total = len(df)
    missing = df.isna().sum()
    pct = (missing / total * 100).round(2)
    summary = pd.DataFrame({
        "missing_count": missing,
        "missing_pct": pct,
    })
    summary = summary[summary["missing_count"] > 0].sort_values("missing_count", ascending=False)
    return summary


def check_non_negative(df: pd.DataFrame, cols: list, report: list) -> pd.DataFrame:
    """Flag but DO NOT drop rows with negative values in cols that should be ≥ 0."""
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            continue
        mask = df[col] < 0
        n_bad = mask.sum()
        if n_bad > 0:
            logger.warning("'%s': %d rows have negative values (flagged only).", col, n_bad)
            report.append(
                {"step": "check_non_negative", "column": col, "rows_affected": int(n_bad),
                 "action": "flagged – NOT dropped (business review required)"}
            )
    return df


def standardise_categoricals(df: pd.DataFrame, cat_cols: list, report: list) -> pd.DataFrame:
    """Strip whitespace and title-case selected categorical columns."""
    df = df.copy()
    for col in cat_cols:
        if col not in df.columns:
            continue
        before_unique = df[col].nunique()
        df[col] = df[col].astype(str).str.strip().str.title()
        after_unique = df[col].nunique()
        if before_unique != after_unique:
            logger.info("'%s' unique values changed: %d → %d", col, before_unique, after_unique)
        report.append(
            {"step": "standardise_categoricals", "column": col,
             "rows_affected": len(df),
             "action": "stripped whitespace + title-cased"}
        )
    return df


def derive_columns(df: pd.DataFrame, report: list) -> pd.DataFrame:
    """Add analytically useful derived columns."""
    df = df.copy()

    # Shipping delay: actual minus scheduled (positive = late)
    if "days_for_shipping_real" in df.columns and "days_for_shipment_scheduled" in df.columns:
        df["shipping_delay_days"] = (
            df["days_for_shipping_real"] - df["days_for_shipment_scheduled"]
        )
        report.append(
            {"step": "derive_columns", "column": "shipping_delay_days",
             "rows_affected": df["shipping_delay_days"].notna().sum(),
             "action": "created: days_for_shipping_real - days_for_shipment_scheduled"}
        )

    # Order year-month for time-series analysis
    date_col = next((c for c in DATE_COLUMNS if c in df.columns), None)
    if date_col:
        df["order_year_month"] = df[date_col].dt.to_period("M").astype(str)
        report.append(
            {"step": "derive_columns", "column": "order_year_month",
             "rows_affected": df["order_year_month"].notna().sum(),
             "action": f"created from {date_col}"}
        )
        df["order_year"] = df[date_col].dt.year
        df["order_month"] = df[date_col].dt.month

    # Late delivery flag derived from actual vs scheduled
    if "shipping_delay_days" in df.columns:
        df["is_late_derived"] = (df["shipping_delay_days"] > 0).astype(int)
        report.append(
            {"step": "derive_columns", "column": "is_late_derived",
             "rows_affected": int(df["is_late_derived"].sum()),
             "action": "1 if shipping_delay_days > 0"}
        )

    return df


def run_cleaning_pipeline(input_path: str, output_path: str, report_path: str) -> pd.DataFrame:
    """
    Execute the full cleaning pipeline.

    Parameters
    ----------
    input_path  : Path to the raw CSV file.
    output_path : Where to save the cleaned CSV.
    report_path : Where to save the cleaning quality report CSV.

    Returns
    -------
    Cleaned DataFrame.
    """
    report: list = []

    # ── 1. Load ───────────────────────────────────────────────────
    logger.info("Loading dataset from: %s", input_path)
    try:
        df = pd.read_csv(input_path, encoding="latin-1", low_memory=False)
    except FileNotFoundError:
        logger.error("File not found: %s", input_path)
        sys.exit(1)

    initial_rows, initial_cols = df.shape
    logger.info("Loaded: %d rows × %d columns", initial_rows, initial_cols)
    report.append(
        {"step": "load", "column": "—", "rows_affected": initial_rows,
         "action": f"loaded {initial_rows} rows × {initial_cols} cols"}
    )

    # ── 2. Standardise column names ───────────────────────────────
    df = standardise_columns(df)
    logger.info("Columns standardised.")

    # ── 3. Remove exact duplicates ────────────────────────────────
    df = remove_exact_duplicates(df, report)

    # ── 4. Parse date columns ─────────────────────────────────────
    df = parse_dates(df, DATE_COLUMNS, report)

    # ── 5. Convert numeric columns ────────────────────────────────
    df = convert_numerics(df, NUMERIC_COLUMNS, report)

    # ── 6. Audit missing values (record only – no imputation) ─────
    missing_summary = audit_missing_values(df)
    if not missing_summary.empty:
        logger.info("Missing value summary:\n%s", missing_summary.to_string())
        for col, row in missing_summary.iterrows():
            report.append(
                {"step": "audit_missing", "column": col,
                 "rows_affected": int(row["missing_count"]),
                 "action": f"{row['missing_pct']}% missing – no imputation applied"}
            )

    # ── 7. Check non-negative constraints ─────────────────────────
    df = check_non_negative(df, NON_NEGATIVE_COLS, report)

    # ── 8. Standardise categoricals ───────────────────────────────
    df = standardise_categoricals(df, CATEGORICAL_COLUMNS, report)

    # ── 9. Derive useful columns ──────────────────────────────────
    df = derive_columns(df, report)

    # ── 10. Save outputs ──────────────────────────────────────────
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Cleaned data saved to: %s  (%d rows × %d cols)", output_path, *df.shape)

    report_df = pd.DataFrame(report)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(report_path, index=False)
    logger.info("Cleaning report saved to: %s", report_path)

    # ── 11. Final summary ─────────────────────────────────────────
    final_rows, final_cols = df.shape
    logger.info(
        "Pipeline complete.  Rows: %d → %d  |  Cols: %d → %d",
        initial_rows, final_rows, initial_cols, final_cols,
    )

    return df


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry-point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DataCo Supply Chain – Data Cleaning Pipeline"
    )
    parser.add_argument(
        "--input",
        default=os.path.join("data", "raw", "DataCoSupplyChainDataset.csv"),
        help="Path to raw CSV (default: data/raw/DataCoSupplyChainDataset.csv)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join("data", "processed", "supply_chain_clean.csv"),
        help="Path for cleaned CSV output",
    )
    parser.add_argument(
        "--report",
        default=os.path.join("data", "processed", "cleaning_report.csv"),
        help="Path for cleaning quality report",
    )
    args = parser.parse_args()
    run_cleaning_pipeline(args.input, args.output, args.report)
