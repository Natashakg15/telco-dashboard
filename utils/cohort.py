"""
Cohort-aging revenue — replaces the blocked VW_COHORT_OVERALL_SALES_WITH_AGING_ON_MEASURES
view. Built entirely from tables we already have access to: UCONNECT_MAY_MERGE
(activation cohort) joined to UCONNECT_MAY_MERGE_REVENUE (revenue by account/month),
aged by months-since-activation.

Feeds: Commercial Cohort Analysis (16), Value of New Business (32), Retain Users
Reward ROI (40).
"""
import streamlit as st
import pandas as pd

from utils.snowflake_conn import run_query, MERGE_TABLE

REV_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE"

REVENUE_EXPR = """(
    COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0) + COALESCE(REVENUE_APP_PURCHASES_VALUE,0)
  + COALESCE(REVENUE_MAY_BILLRUN_VALUE,0) + COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)
  + COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0) + COALESCE(REVENUE_WHATSAPP_PURCHASES_VALUE,0)
)"""


@st.cache_data(ttl=3600, show_spinner="Loading cohort-aging revenue…")
def load_cohort_aging(months_back: int = 13, max_age_months: int = 12) -> pd.DataFrame:
    """
    Returns one row per (COHORT_MONTH, AGE_MONTHS): ACQUIRED (fixed per cohort month),
    ACTIVE (distinct accounts from that cohort with revenue > 0 in that age month),
    REVENUE (summed revenue from that cohort in that age month).
    AGE_MONTHS=0 is the acquisition month itself.
    """
    df = run_query(f"""
        WITH ACQ AS (
            SELECT ACCOUNT_NUMBER, DATE_TRUNC('month', ACTIVATION_DATE) AS COHORT_MONTH
            FROM {MERGE_TABLE}
            WHERE MASTER_TENANT = 'uConnect'
              AND ACTIVATION_DATE >= DATEADD(month, -{months_back}, CURRENT_DATE())
        ),
        COHORT_SIZE AS (
            SELECT COHORT_MONTH, COUNT(DISTINCT ACCOUNT_NUMBER) AS ACQUIRED
            FROM ACQ GROUP BY 1
        ),
        REV AS (
            SELECT ACCOUNT_NUMBER, DATE_TRUNC('month', TRANSACTION_DATE) AS REV_MONTH,
                   {REVENUE_EXPR} AS REVENUE
            FROM {REV_TABLE}
        ),
        JOINED AS (
            SELECT ACQ.COHORT_MONTH, DATEDIFF('month', ACQ.COHORT_MONTH, REV.REV_MONTH) AS AGE_MONTHS,
                   ACQ.ACCOUNT_NUMBER, REV.REVENUE
            FROM ACQ JOIN REV ON ACQ.ACCOUNT_NUMBER = REV.ACCOUNT_NUMBER
            WHERE DATEDIFF('month', ACQ.COHORT_MONTH, REV.REV_MONTH) BETWEEN 0 AND {max_age_months}
        )
        SELECT
            J.COHORT_MONTH, J.AGE_MONTHS, CS.ACQUIRED,
            COUNT(DISTINCT CASE WHEN J.REVENUE > 0 THEN J.ACCOUNT_NUMBER END) AS ACTIVE,
            SUM(J.REVENUE) AS REVENUE
        FROM JOINED J
        JOIN COHORT_SIZE CS ON J.COHORT_MONTH = CS.COHORT_MONTH
        GROUP BY 1,2,3
        ORDER BY 1,2
    """)
    df.columns = [c.upper() for c in df.columns]
    if not df.empty:
        df["COHORT_MONTH"] = pd.to_datetime(df["COHORT_MONTH"])
        df["REVENUE_PER_ACQUIRED"] = (df["REVENUE"] / df["ACQUIRED"].replace(0, float("nan"))).round(2)
        df["REVENUE_PER_ACTIVE"] = (df["REVENUE"] / df["ACTIVE"].replace(0, float("nan"))).round(2)
    return df
