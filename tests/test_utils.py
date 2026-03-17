import pytest
import pandas as pd
from utils import get_unique_sorted, compute_avg_days


# Tests for get_unique_sorted

class TestGetUniqueSorted:
    def test_basic_sort(self):
        s = pd.Series(["B", "A", "C"])
        assert get_unique_sorted(s) == ["A", "B", "C"]

    def test_strips_whitespace(self):
        s = pd.Series(["  B", "A  ", " C "])
        assert get_unique_sorted(s) == ["A", "B", "C"]

    def test_drops_nulls(self):
        s = pd.Series(["A", None, "B", float("nan")])
        result = get_unique_sorted(s)
        assert None not in result
        assert "nan" not in result

    def test_deduplicates(self):
        s = pd.Series(["A", "A", "B"])
        assert get_unique_sorted(s) == ["A", "B"]

    def test_empty_series(self):
        assert get_unique_sorted(pd.Series([], dtype=str)) == []

    def test_numeric_series_coerced_to_str(self):
        s = pd.Series([3, 1, 2])
        assert get_unique_sorted(s) == ["1", "2", "3"]


# Tests for compute_avg_days

class TestComputeAvgDays:
    def test_empty_df_returns_zero(self):
        df = pd.DataFrame(columns=["applied", "issued"])
        assert compute_avg_days(df, "applied", "issued") == "0 Days"

    def test_basic_average(self):
        df = pd.DataFrame({
            "applied": ["2023-01-01", "2023-01-01"],
            "issued":  ["2023-01-11", "2023-01-21"],
        })
        assert compute_avg_days(df, "applied", "issued") == "15.0 Days"

    def test_single_row(self):
        df = pd.DataFrame({
            "applied": ["2023-06-01"],
            "issued":  ["2023-06-11"],
        })
        assert compute_avg_days(df, "applied", "issued") == "10.0 Days"

    def test_all_nat_returns_zero(self):
        df = pd.DataFrame({
            "applied": [None, None],
            "issued":  [None, None],
        })
        assert compute_avg_days(df, "applied", "issued") == "0 Days"

    def test_mixed_nat_ignores_invalid_rows(self):
        df = pd.DataFrame({
            "applied": ["2023-01-01", None],
            "issued":  ["2023-01-11", None],
        })
        assert compute_avg_days(df, "applied", "issued") == "10.0 Days"

    def test_same_day_returns_zero_days(self):
        df = pd.DataFrame({
            "applied": ["2023-03-15"],
            "issued":  ["2023-03-15"],
        })
        assert compute_avg_days(df, "applied", "issued") == "0.0 Days"
