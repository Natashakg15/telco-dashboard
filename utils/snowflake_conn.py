"""
Snowflake connection helper.
Falls back to demo/sample data when secrets are not configured.
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta

MERGE_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE"

# ── Demo-mode detection ───────────────────────────────────────────────────────
def _has_snowflake_secrets() -> bool:
    try:
        return "snowflake" in st.secrets
    except Exception:
        return False

DEMO_MODE = not _has_snowflake_secrets()

# ── Live connection ───────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_connection():
    try:
        import snowflake.connector
        creds = st.secrets["snowflake"]
        return snowflake.connector.connect(
            account       = creds["account"],
            user          = creds["user"],
            password      = creds.get("password"),
            warehouse     = creds.get("warehouse", "COMPUTE_WH"),
            database      = creds.get("database", "UCONNECT_DW"),
            schema        = creds.get("schema", "ANALYTICS"),
            role          = creds.get("role"),
            authenticator = creds.get("authenticator", "snowflake"),
        )
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner="Loading data…")
def run_query(sql: str) -> pd.DataFrame:
    if DEMO_MODE:
        return _demo_query(sql)
    try:
        conn = get_connection()
        return pd.read_sql(sql, conn)
    except Exception:
        return _demo_query(sql)

# ── Sample tenants ────────────────────────────────────────────────────────────
_TENANTS = [
    "SPAR Alberton", "Build It Pretoria", "Mica Cape Town", "Aheers Durban",
    "Fashion Fusion JHB", "Progas Soweto", "Midas Springs", "Pet Pool Randburg",
    "SPAR Sandton", "Build It Roodepoort", "Mica Midrand", "Aheers Pinetown",
    "SPAR Boksburg", "Build It Germiston", "Fashion Fusion Tshwane", "Progas North",
    "Midas East Rand", "SPAR Centurion", "Build It Vereeniging", "Mica Polokwane",
]

def _demo_query(sql: str) -> pd.DataFrame:
    sql_upper = sql.upper()
    today = date.today()

    if "DISTINCT TENANT" in sql_upper:
        return pd.DataFrame({"TENANT": _TENANTS})

    if "ACTIVATION_DATE" in sql_upper and "COUNT" in sql_upper:
        rng = pd.date_range(end=today, periods=395, freq="D")
        np.random.seed(42)
        base = 1800
        counts = (
            np.random.poisson(base, len(rng))
            * np.where(pd.DatetimeIndex(rng).dayofweek >= 5, 0.35, 1.0)
        ).astype(int)
        return pd.DataFrame({"ACTIVATION_DATE": rng, "ACTIVATIONS": counts})

    if "LAST_MONTH" in sql_upper and "THIS_MONTH" in sql_upper:
        np.random.seed(7)
        last = np.random.randint(200, 2800, len(_TENANTS))
        this = (last * np.random.uniform(0.8, 1.25, len(_TENANTS))).astype(int)
        return pd.DataFrame({"TENANT": _TENANTS, "LAST_MONTH": last, "THIS_MONTH": this})

    return pd.DataFrame()
