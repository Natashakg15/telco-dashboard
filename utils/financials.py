"""
Financials data loader.

Source: data/format_is_long.csv - a one-time snapshot pulled from the 'Format Is'
sheet of TEST INCOME STATEMENT.xlsx (SharePoint: Telco Retail new business
evaluation model / Excel Reports), taken 2026-07-28. This is a hand-maintained
Excel workbook with no live connection yet - there is no Graph API or sync job
wiring this dashboard to SharePoint, so this snapshot will NOT update on its own.
Re-pull and replace the CSV manually (or build a proper integration - see
project notes) to refresh it.

Reported EBITDA swings from a plausible ~R0.4-1.5M/month range through Feb 2027
to a consistently worsening -R2M..-R4.3M/month from Mar 2027 onward - this looks
like a stale or different-scenario budget block rather than a real continuation,
not a real forecast. Treat anything from UNVERIFIED_FROM onward as unverified.
"""
import os
import pandas as pd
import streamlit as st

_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "format_is_long.csv")

SNAPSHOT_DATE = "28 Jul 2026"
UNVERIFIED_FROM = pd.Timestamp("2027-03-01")


@st.cache_data(ttl=3600, show_spinner=False)
def load_financials() -> pd.DataFrame:
    df = pd.read_csv(_CSV_PATH, parse_dates=["month"])
    return df


def line(df: pd.DataFrame, detail: str) -> pd.Series:
    """Monthly series for one Detail line item, indexed by month."""
    d = df[df["detail"] == detail].set_index("month")["value"].sort_index()
    return d[~d.index.duplicated()]


def lines_sum(df: pd.DataFrame, details: list) -> pd.Series:
    """Monthly series summing several named Detail line items."""
    d = df[df["detail"].isin(details)].groupby("month")["value"].sum().sort_index()
    return d


def section_total(df: pd.DataFrame, section: str) -> pd.Series:
    """Monthly series summing every Detail row under a Section (Revenue, Opex, etc.)."""
    d = df[df["section"] == section].groupby("month")["value"].sum().sort_index()
    return d


def section_breakdown(df: pd.DataFrame, section: str, by: str = "subheader") -> pd.DataFrame:
    """Monthly totals per sub-group within a section, wide format (columns = groups)."""
    sub = df[df["section"] == section]
    wide = sub.groupby(["month", by])["value"].sum().unstack(by).sort_index()
    return wide.fillna(0)


def ytd(series: pd.Series, as_of: pd.Timestamp) -> float:
    """Sum of a monthly series from Jan of as_of's year through as_of's month."""
    start = pd.Timestamp(year=as_of.year, month=1, day=1)
    return float(series[(series.index >= start) & (series.index <= as_of)].sum())


def latest_two(series: pd.Series, as_of: pd.Timestamp):
    """(this_month_value, last_month_value) for the two most recent months <= as_of."""
    s = series[series.index <= as_of]
    this_v = float(s.iloc[-1]) if len(s) >= 1 else 0.0
    last_v = float(s.iloc[-2]) if len(s) >= 2 else 0.0
    return this_v, last_v
