import pandas as pd


def get_unique_sorted(series: pd.Series) -> list:
    """Return sorted unique non-null string values from a pandas Series."""
    return sorted(series.dropna().astype(str).str.strip().unique())


def compute_avg_days(df: pd.DataFrame, applied_col: str, issue_col: str) -> str:
    """
    Calculate mean days between applied_col and issue_col dates.
    Returns '0 Days' on an empty DataFrame or when no valid rows exist.
    """
    if df.empty:
        return "0 Days"

    applied = pd.to_datetime(df[applied_col], errors="coerce")
    issued = pd.to_datetime(df[issue_col], errors="coerce")
    days = (issued - applied).dt.days.dropna()

    if days.empty:
        return "0 Days"

    return f"{days.mean():.1f} Days"
