"""
Snowflake connection helper.
Reads credentials from Streamlit secrets (secrets.toml) or environment variables.
"""
import streamlit as st
import snowflake.connector
import pandas as pd
from functools import wraps

# ── Table reference ───────────────────────────────────────────────────────────
MERGE_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE"


@st.cache_resource(show_spinner=False)
def get_connection():
    """Return a cached Snowflake connection."""
    creds = st.secrets["snowflake"]
    conn = snowflake.connector.connect(
        account   = creds["account"],
        user      = creds["user"],
        password  = creds.get("password"),
        warehouse = creds.get("warehouse", "COMPUTE_WH"),
        database  = creds.get("database", "UCONNECT_DW"),
        schema    = creds.get("schema", "ANALYTICS"),
        role      = creds.get("role"),
        authenticator = creds.get("authenticator", "snowflake"),
    )
    return conn


@st.cache_data(ttl=3600, show_spinner="Loading data…")
def run_query(sql: str) -> pd.DataFrame:
    """Execute SQL and return a DataFrame. Results cached for 1 hour."""
    conn = get_connection()
    return pd.read_sql(sql, conn)
