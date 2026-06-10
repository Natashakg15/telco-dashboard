"""
Snowflake connection helper.
Falls back to demo/sample data when secrets are not configured.
DEMO_MODE is checked lazily (inside functions) to avoid import-time Streamlit issues.
"""
import pandas as pd
import numpy as np
from datetime import date

MERGE_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE"

# ── Sample tenants (demo data) ────────────────────────────────────────────────
_TENANTS = [
    "SPAR Alberton", "Build It Pretoria", "Mica Cape Town", "Aheers Durban",
    "Fashion Fusion JHB", "Progas Soweto", "Midas Springs", "Pet Pool Randburg",
    "SPAR Sandton", "Build It Roodepoort", "Mica Midrand", "Aheers Pinetown",
    "SPAR Boksburg", "Build It Germiston", "Fashion Fusion Tshwane", "Progas North",
    "Midas East Rand", "SPAR Centurion", "Build It Vereeniging", "Mica Polokwane",
]

def _is_demo() -> bool:
    """Check at call-time whether Snowflake secrets are configured."""
    try:
        import streamlit as st
        return "snowflake" not in st.secrets
    except Exception:
        return True

def run_query(sql: str) -> pd.DataFrame:
    """Execute SQL and return a DataFrame, or fall back to demo data."""
    import streamlit as st

    if _is_demo():
        return _demo_query(sql)

    # ── Live Snowflake query ──────────────────────────────────────────────────
    try:
        import snowflake.connector
        creds = st.secrets["snowflake"]
        conn = snowflake.connector.connect(
            account       = creds["account"],
            user          = creds["user"],
            password      = creds.get("password"),
            warehouse     = creds.get("warehouse", "COMPUTE_WH"),
            database      = creds.get("database", "UCONNECT_DW"),
            schema        = creds.get("schema", "ANALYTICS"),
            role          = creds.get("role"),
            authenticator = creds.get("authenticator", "snowflake"),
        )
        df = pd.read_sql(sql, conn)
        conn.close()
        # Normalise column names to uppercase for consistency
        df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return _demo_query(sql)


def _demo_query(sql: str) -> pd.DataFrame:
    sql_up = sql.upper()
    today  = date.today()

    # Tenant list
    if "DISTINCT TENANT" in sql_up:
        return pd.DataFrame({"TENANT": _TENANTS})

    # Daily activations
    if "ACTIVATION_DATE" in sql_up and "COUNT" in sql_up:
        rng = pd.date_range(end=today, periods=395, freq="D")
        np.random.seed(42)
        base   = 1800
        counts = (
            np.random.poisson(base, len(rng))
            * np.where(pd.DatetimeIndex(rng).dayofweek >= 5, 0.35, 1.0)
        ).astype(int)
        return pd.DataFrame({"ACTIVATION_DATE": rng, "ACTIVATIONS": counts})

    # Tenant month tables
    if "LAST_MONTH" in sql_up and "THIS_MONTH" in sql_up:
        np.random.seed(7)
        last = np.random.randint(200, 2800, len(_TENANTS))
        this = (last * np.random.uniform(0.8, 1.25, len(_TENANTS))).astype(int)
        return pd.DataFrame({
            "TENANT":     _TENANTS,
            "LAST_MONTH": last,
            "THIS_MONTH": this,
        })

    return pd.DataFrame()
