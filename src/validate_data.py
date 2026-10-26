"""
validate_data.py
================
Post-cleaning validation – verifies that the cleaned dataset meets
expected constraints before analysis proceeds.
"""

import logging
import sys
from pathlib import Path

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "order_id",
    "sales",
    "order_item_total",
    "order_profit_per_order",
    "order_date_dateorders",
    "shipping_mode",
    "category_name",
    "market",
]

CHECKS_PASSED = []
CHECKS_FAILED = []


def _record(name: str, passed: bool, detail: str = "") -> None:
    entry = {"check": name, "passed": passed, "detail": detail}
    if passed:
        CHECKS_PASSED.append(entry)
        logger.info("✓ PASS  %s  %s", name, detail)
    else:
        CHECKS_FAILED.append(entry)
        logger.warning("✗ FAIL  %s  %s", name, detail)


def validate_schema(df: pd.DataFrame) -> None:
    for col in REQUIRED_COLUMNS:
        present = col in df.columns
        _record(f"schema:{col}", present, "present" if present else "MISSING")


def validate_no_exact_duplicates(df: pd.DataFrame) -> None:
    n_dup = df.duplicated().sum()
    _record("no_exact_duplicates", n_dup == 0, f"{n_dup} exact duplicates found")


def validate_date_columns(df: pd.DataFrame) -> None:
    for col in ["order_date_dateorders", "shipping_date_dateorders"]:
        if col not in df.columns:
            _record(f"date_dtype:{col}", False, "column missing")
            continue
        is_dt = pd.api.types.is_datetime64_any_dtype(df[col])
        _record(f"date_dtype:{col}", is_dt, "datetime64" if is_dt else str(df[col].dtype))


def validate_numeric_columns(df: pd.DataFrame) -> None:
    for col in ["sales", "order_item_total", "order_profit_per_order",
                "days_for_shipping_real", "days_for_shipment_scheduled"]:
        if col not in df.columns:
            continue
        is_num = pd.api.types.is_numeric_dtype(df[col])
        _record(f"numeric_dtype:{col}", is_num, str(df[col].dtype))


def validate_order_id(df: pd.DataFrame) -> None:
    if "order_id" not in df.columns:
        _record("order_id_not_null", False, "column missing")
        return
    null_count = df["order_id"].isna().sum()
    _record("order_id_not_null", null_count == 0, f"{null_count} nulls")


def validate_sales_positive(df: pd.DataFrame) -> None:
    if "sales" not in df.columns:
        return
    neg = (df["sales"] < 0).sum()
    # Flag but do not fail – some returns may legitimately appear
    _record("sales_non_negative", neg == 0,
            f"{neg} rows with negative sales (review manually)")


def validate_late_delivery_column(df: pd.DataFrame) -> None:
    col = next((c for c in ["late_delivery_risk", "is_late_derived"] if c in df.columns), None)
    if col is None:
        _record("late_delivery_col_present", False, "neither late_delivery_risk nor is_late_derived found")
        return
    vals = df[col].dropna().unique()
    is_binary_like = set(vals).issubset({0, 1, "0", "1", 0.0, 1.0})
    _record("late_delivery_binary", is_binary_like, f"values: {vals[:5]}")


def validate_date_range(df: pd.DataFrame) -> None:
    col = "order_date_dateorders"
    if col not in df.columns or not pd.api.types.is_datetime64_any_dtype(df[col]):
        return
    min_date = df[col].min()
    max_date = df[col].max()
    future_dates = (df[col] > pd.Timestamp.now()).sum()
    _record("date_range_no_future", future_dates == 0,
            f"Range: {min_date.date()} → {max_date.date()}, future rows: {future_dates}")


def validate_row_count(df: pd.DataFrame, expected_min: int = 10_000) -> None:
    n = len(df)
    _record("minimum_row_count", n >= expected_min,
            f"{n:,} rows (min expected: {expected_min:,})")


def run_all_validations(df: pd.DataFrame, output_path: str = None) -> bool:
    """Run all validations; optionally save report. Returns True if all pass."""
    CHECKS_PASSED.clear()
    CHECKS_FAILED.clear()

    validate_schema(df)
    validate_no_exact_duplicates(df)
    validate_date_columns(df)
    validate_numeric_columns(df)
    validate_order_id(df)
    validate_sales_positive(df)
    validate_late_delivery_column(df)
    validate_date_range(df)
    validate_row_count(df)

    all_results = CHECKS_PASSED + CHECKS_FAILED
    report_df = pd.DataFrame(all_results)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        report_df.to_csv(output_path, index=False)
        logger.info("Validation report saved: %s", output_path)

    n_pass = len(CHECKS_PASSED)
    n_fail = len(CHECKS_FAILED)
    logger.info("Validation: %d passed, %d failed", n_pass, n_fail)

    return n_fail == 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/supply_chain_clean.csv")
    parser.add_argument("--report", default="data/processed/validation_report.csv")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    df = pd.read_csv(args.input, low_memory=False,
                     parse_dates=["order_date_dateorders", "shipping_date_dateorders"])
    ok = run_all_validations(df, args.report)
    sys.exit(0 if ok else 1)
