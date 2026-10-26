"""
test_pipeline.py
================
Automated tests for the DataCo Supply Chain analytics pipeline.
All test data is synthetic and clearly labeled as TEST DATA.
Never mix synthetic examples with real data.

Run with:
    python -m pytest tests/test_pipeline.py -v
"""

import sys
import os
import io
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clean_data import (
    standardise_columns,
    parse_dates,
    convert_numerics,
    remove_exact_duplicates,
    audit_missing_values,
    check_non_negative,
    standardise_categoricals,
    derive_columns,
)
from validate_data import run_all_validations


# ─────────────────────────────────────────────────────────────────────────────
# TEST FIXTURES – synthetic data only; labeled TEST DATA
# ─────────────────────────────────────────────────────────────────────────────

def make_test_df() -> pd.DataFrame:
    """
    Returns a minimal synthetic DataFrame that mimics the DataCo schema.
    ALL VALUES ARE SYNTHETIC TEST DATA.
    """
    return pd.DataFrame({
        "Order Id": [1001, 1001, 1002, 1003, 1004, 1004],  # duplicate rows at 0,1 and 4,5
        "Sales": [150.0, 150.0, 200.0, None, 75.5, 75.5],
        "Order Item Total": [145.0, 145.0, 195.0, 50.0, 72.0, 72.0],
        "Order Profit Per Order": [30.0, 30.0, -10.0, 5.0, 15.0, 15.0],
        "Order Item Quantity": [2, 2, 1, 0, 3, 3],
        "Order Item Product Price": [75.0, 75.0, 200.0, 50.0, 25.0, 25.0],
        "Order Item Discount": [5.0, 5.0, 5.0, 0.0, 3.5, 3.5],
        "Order Item Discount Rate": [0.033, 0.033, 0.025, 0.0, 0.047, 0.047],
        "Order Item Profit Ratio": [0.2, 0.2, -0.05, 0.1, 0.2, 0.2],
        "Days for shipping (real)": [3, 3, 5, 2, 7, 7],
        "Days for shipment (scheduled)": [4, 4, 3, 2, 4, 4],
        "Late_delivery_risk": [0, 0, 1, 0, 1, 1],
        "Order Date (DateOrders)": [
            "1/1/2017", "1/1/2017", "2/15/2017", "3/10/2017", "BAD_DATE", "BAD_DATE"
        ],
        "Shipping Date (DateOrders)": [
            "1/4/2017", "1/4/2017", "2/20/2017", "3/12/2017", None, None
        ],
        "Category Name": [" Electronics ", " Electronics ", "Furniture", "Clothing", "Electronics", "Electronics"],
        "Market": ["Europe", "Europe", "LATAM", "Pacific Asia", "USCA", "USCA"],
        "Shipping Mode": ["Second Class", "Second Class", "First Class", "Standard Class", "Same Day", "Same Day"],
        "Customer Segment": ["Consumer", "Consumer", "Corporate", "Home Office", "Consumer", "Consumer"],
        "Benefit per order": [28.0, 28.0, -12.0, 5.0, 14.0, 14.0],
        "Department Name": ["Electronics", "Electronics", "Furniture", "Apparel", "Electronics", "Electronics"],
        "Order Region": ["Western Europe", "Western Europe", "South America",
                         "Southeast Asia", "US Center", "US Center"],
        "Order Country": ["France", "France", "Brazil", "Philippines", "USA", "USA"],
        "Order Status": ["Complete", "Complete", "Complete", "Pending", "Shipped", "Shipped"],
        "Type": ["DEBIT", "DEBIT", "TRANSFER", "CASH", "PAYMENT", "PAYMENT"],
        "Customer Country": ["EE. UU.", "EE. UU.", "Brasil", "Philippines", "USA", "USA"],
        "Latitude": [47.1, 47.1, -15.8, 14.6, 39.5, 39.5],
        "Longitude": [2.3, 2.3, -47.9, 121.0, -95.0, -95.0],
    })


# ─────────────────────────────────────────────────────────────────────────────
# 1. Column standardisation
# ─────────────────────────────────────────────────────────────────────────────
class TestStandardiseColumns:
    def test_lowercase(self):
        df = pd.DataFrame({"Order Id": [1], "SALES": [100]})
        result = standardise_columns(df)
        assert "order_id" in result.columns
        assert "sales" in result.columns

    def test_spaces_to_underscores(self):
        df = pd.DataFrame({"Order Item Total": [100]})
        result = standardise_columns(df)
        assert "order_item_total" in result.columns

    def test_special_chars_stripped(self):
        df = pd.DataFrame({"Days for shipping (real)": [3]})
        result = standardise_columns(df)
        assert "days_for_shipping_real" in result.columns


# ─────────────────────────────────────────────────────────────────────────────
# 2. Duplicate removal
# ─────────────────────────────────────────────────────────────────────────────
class TestRemoveDuplicates:
    def test_exact_duplicates_removed(self):
        report = []
        df = make_test_df()
        df = standardise_columns(df)
        before = len(df)
        df_clean = remove_exact_duplicates(df, report)
        assert len(df_clean) < before
        assert df_clean.duplicated().sum() == 0

    def test_report_records_count(self):
        report = []
        df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
        remove_exact_duplicates(df, report)
        step = next(r for r in report if r["step"] == "remove_exact_duplicates")
        assert step["rows_affected"] == 1

    def test_no_duplicates_unaffected(self):
        report = []
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df_clean = remove_exact_duplicates(df, report)
        assert len(df_clean) == 3


# ─────────────────────────────────────────────────────────────────────────────
# 3. Date parsing
# ─────────────────────────────────────────────────────────────────────────────
class TestDateParsing:
    def test_valid_dates_parsed(self):
        report = []
        df = pd.DataFrame({"order_date_dateorders": ["1/1/2017", "2/15/2017", "12/31/2018"]})
        result = parse_dates(df, ["order_date_dateorders"], report)
        assert pd.api.types.is_datetime64_any_dtype(result["order_date_dateorders"])

    def test_invalid_dates_become_nat(self):
        report = []
        df = pd.DataFrame({"order_date_dateorders": ["1/1/2017", "BAD_DATE", None]})
        result = parse_dates(df, ["order_date_dateorders"], report)
        assert result["order_date_dateorders"].isna().sum() >= 1

    def test_bad_date_count_in_report(self):
        report = []
        df = pd.DataFrame({"order_date_dateorders": ["BAD", "ALSO_BAD", "1/1/2017"]})
        parse_dates(df, ["order_date_dateorders"], report)
        step = next(r for r in report if r["step"] == "parse_dates")
        assert step["rows_affected"] == 2

    def test_missing_date_column_skipped(self):
        report = []
        df = pd.DataFrame({"other_col": [1, 2]})
        # Should not raise
        parse_dates(df, ["order_date_dateorders"], report)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Numeric conversion
# ─────────────────────────────────────────────────────────────────────────────
class TestNumericConversion:
    def test_valid_numerics_preserved(self):
        report = []
        df = pd.DataFrame({"sales": ["100.5", "200.0", "300.75"]})
        result = convert_numerics(df, ["sales"], report)
        assert pd.api.types.is_numeric_dtype(result["sales"])
        assert result["sales"].sum() == pytest.approx(601.25)

    def test_invalid_strings_coerced(self):
        report = []
        df = pd.DataFrame({"sales": ["100", "abc", "200"]})
        result = convert_numerics(df, ["sales"], report)
        assert result["sales"].isna().sum() == 1


# ─────────────────────────────────────────────────────────────────────────────
# 5. Missing value audit
# ─────────────────────────────────────────────────────────────────────────────
class TestMissingValueAudit:
    def test_returns_only_missing_cols(self):
        df = pd.DataFrame({"a": [1, 2, None], "b": [4, 5, 6]})
        summary = audit_missing_values(df)
        assert "a" in summary.index
        assert "b" not in summary.index

    def test_correct_count(self):
        df = pd.DataFrame({"x": [None, None, 1, 2]})
        summary = audit_missing_values(df)
        assert summary.loc["x", "missing_count"] == 2

    def test_correct_percentage(self):
        df = pd.DataFrame({"x": [None, 1, 2, 3]})
        summary = audit_missing_values(df)
        assert summary.loc["x", "missing_pct"] == pytest.approx(25.0)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Derived columns
# ─────────────────────────────────────────────────────────────────────────────
class TestDeriveColumns:
    def test_shipping_delay_positive_when_late(self):
        report = []
        df = pd.DataFrame({
            "days_for_shipping_real": [5, 3],
            "days_for_shipment_scheduled": [4, 4],
            "order_date_dateorders": pd.to_datetime(["2017-01-01", "2017-02-01"]),
        })
        result = derive_columns(df, report)
        assert result["shipping_delay_days"].iloc[0] == 1
        assert result["shipping_delay_days"].iloc[1] == -1

    def test_is_late_derived_flag(self):
        report = []
        df = pd.DataFrame({
            "days_for_shipping_real": [6, 2],
            "days_for_shipment_scheduled": [4, 4],
            "order_date_dateorders": pd.to_datetime(["2017-01-01", "2017-02-01"]),
        })
        result = derive_columns(df, report)
        assert result["is_late_derived"].iloc[0] == 1
        assert result["is_late_derived"].iloc[1] == 0

    def test_year_month_created(self):
        report = []
        df = pd.DataFrame({
            "order_date_dateorders": pd.to_datetime(["2017-01-15", "2017-03-20"]),
        })
        result = derive_columns(df, report)
        assert "order_year_month" in result.columns
        assert result["order_year_month"].iloc[0] == "2017-01"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Late delivery rate calculation
# ─────────────────────────────────────────────────────────────────────────────
class TestLateDeliveryRate:
    def test_late_rate_calculation(self):
        """Test that late delivery rate = late_count / total"""
        df = pd.DataFrame({
            "late_delivery_risk": [1, 1, 0, 1, 0],
            "shipping_mode": ["First Class"] * 5,
            "days_for_shipping_real": [5, 6, 3, 7, 2],
            "days_for_shipment_scheduled": [4, 4, 4, 4, 4],
        })
        late_rate = df["late_delivery_risk"].sum() / len(df) * 100
        assert late_rate == pytest.approx(60.0)

    def test_zero_late_deliveries(self):
        df = pd.DataFrame({"late_delivery_risk": [0, 0, 0, 0]})
        late_rate = df["late_delivery_risk"].sum() / len(df) * 100
        assert late_rate == pytest.approx(0.0)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Distinct order counting
# ─────────────────────────────────────────────────────────────────────────────
class TestDistinctOrders:
    def test_distinct_order_count(self):
        """Order-items may share order_id; distinct count must be correct."""
        df = pd.DataFrame({
            "order_id": [1001, 1001, 1002, 1003, 1003, 1003],
            "sales": [10.0, 20.0, 15.0, 5.0, 8.0, 12.0],
        })
        assert df["order_id"].nunique() == 3

    def test_no_double_counting_profit(self):
        """Profit is per-order; dedup before summing."""
        df = pd.DataFrame({
            "order_id": [1001, 1001, 1002],
            "order_profit_per_order": [50.0, 50.0, 30.0],
        })
        total_profit = df.drop_duplicates(subset=["order_id"])["order_profit_per_order"].sum()
        assert total_profit == pytest.approx(80.0)

    def test_total_sales_includes_all_items(self):
        """Sales are per line-item; sum all rows."""
        df = pd.DataFrame({
            "order_id": [1001, 1001, 1002],
            "sales": [50.0, 30.0, 20.0],
        })
        assert df["sales"].sum() == pytest.approx(100.0)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Aggregation accuracy on controlled fixture
# ─────────────────────────────────────────────────────────────────────────────
class TestAggregationAccuracy:
    def test_monthly_sales_sum(self):
        """Monthly aggregation must equal the total sales sum."""
        df = pd.DataFrame({
            "order_year_month": ["2017-01", "2017-01", "2017-02", "2017-03"],
            "sales": [100.0, 200.0, 150.0, 50.0],
            "order_id": [1, 2, 3, 4],
        })
        monthly = df.groupby("order_year_month")["sales"].sum()
        assert monthly.sum() == pytest.approx(df["sales"].sum())

    def test_category_aggregation(self):
        df = pd.DataFrame({
            "category_name": ["A", "A", "B", "B", "C"],
            "sales": [100, 200, 50, 75, 300],
            "order_id": [1, 2, 3, 4, 5],
        })
        cat = df.groupby("category_name")["sales"].sum()
        assert cat["A"] == 300
        assert cat["B"] == 125
        assert cat["C"] == 300


# ─────────────────────────────────────────────────────────────────────────────
# 10. Validation module
# ─────────────────────────────────────────────────────────────────────────────
class TestValidation:
    def _make_valid_df(self):
        """Create a minimal valid DataFrame for validation testing."""
        n = 15000
        return pd.DataFrame({
            "order_id": range(n),
            "sales": np.random.uniform(10, 500, n),
            "order_item_total": np.random.uniform(9, 490, n),
            "order_profit_per_order": np.random.uniform(-50, 200, n),
            "order_date_dateorders": pd.date_range("2016-01-01", periods=n, freq="h"),
            "shipping_date_dateorders": pd.date_range("2016-01-03", periods=n, freq="h"),
            "shipping_mode": ["Standard Class"] * n,
            "category_name": ["Electronics"] * n,
            "market": ["USCA"] * n,
            "late_delivery_risk": np.random.randint(0, 2, n),
            "days_for_shipping_real": np.random.randint(1, 10, n),
            "days_for_shipment_scheduled": np.random.randint(1, 8, n),
        })

    def test_valid_df_passes(self):
        df = self._make_valid_df()
        result = run_all_validations(df)
        # Schema checks should pass for all required cols present
        from validate_data import CHECKS_FAILED
        schema_fails = [c for c in CHECKS_FAILED if c["check"].startswith("schema:")]
        assert len(schema_fails) == 0

    def test_missing_column_fails_schema(self):
        df = self._make_valid_df().drop(columns=["order_id"])
        run_all_validations(df)
        from validate_data import CHECKS_FAILED
        schema_fail = next((c for c in CHECKS_FAILED if c["check"] == "schema:order_id"), None)
        assert schema_fail is not None

    def test_duplicate_detection(self):
        df = self._make_valid_df()
        # Add exact duplicates
        df_dup = pd.concat([df, df.iloc[:5]], ignore_index=True)
        run_all_validations(df_dup)
        from validate_data import CHECKS_FAILED
        dup_fail = next((c for c in CHECKS_FAILED if c["check"] == "no_exact_duplicates"), None)
        assert dup_fail is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
