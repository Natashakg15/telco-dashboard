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
        if not st.session_state.get("_sf_demo_reason_shown"):
            print("[snowflake_conn] 'snowflake' block missing from st.secrets — using demo data", flush=True)
            st.session_state["_sf_demo_reason_shown"] = True
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
    except Exception as e:
        print(f"[snowflake_conn] live query failed, falling back to demo data: {e!r}", flush=True)
        if not st.session_state.get("_sf_error_shown"):
            st.caption(f"⚠️ Snowflake unavailable, showing demo data — {e}")
            st.session_state["_sf_error_shown"] = True
        return _demo_query(sql)


def _demo_query(sql: str) -> pd.DataFrame:
    sql_up = sql.upper()
    today  = date.today()

    # Tenant list
    if "DISTINCT TENANT" in sql_up:
        return pd.DataFrame({"TENANT": _TENANTS})

    # Monthly activations + reward cost per activation (complex JOIN — must precede MONTH_START)
    if "REWARD_COST_PER_ACT" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(33)
        acts = np.random.randint(3000, 12000, len(rng))
        reward_val = np.random.uniform(50000, 300000, len(rng))
        reward_qty = np.random.randint(200, 2000, len(rng))
        total_rev  = np.random.uniform(800000, 3000000, len(rng))
        return pd.DataFrame({
            "MONTH_START":        rng,
            "ACTIVATIONS":        acts,
            "REWARD_VALUE":       reward_val.round(0),
            "REWARD_QTY":         reward_qty,
            "TOTAL_REVENUE":      total_rev.round(0),
            "REWARD_COST_PER_ACT": (reward_val / acts).round(2),
        })

    # Monthly revenue (TOTAL_REVENUE + MONTH_START — must precede plain MONTH_START)
    if "TOTAL_REVENUE" in sql_up and "MONTH_START" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(43)
        rev = np.random.uniform(800000, 3000000, len(rng))
        return pd.DataFrame({
            "MONTH_START":   rng,
            "TOTAL_REVENUE": rev.round(0),
            "CELLC":   (rev * 0.40).round(0),
            "VOUCHER": (rev * 0.15).round(0),
            "APP":     (rev * 0.20).round(0),
            "BILLRUN": (rev * 0.15).round(0),
            "POSTPAID":(rev * 0.10).round(0),
        })

    # Monthly activations (DATE_TRUNC → MONTH_START alias)
    if "MONTH_START" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(42)
        counts = np.random.randint(3000, 12000, len(rng))
        return pd.DataFrame({"MONTH_START": rng, "ACTIVATIONS": counts})

    # Channel acquisitions by month (must precede plain ACTIVATION_DATE check)
    if "ACT_BY_CHANNEL" in sql_up:
        rng = pd.date_range(end=today, periods=12, freq="MS")
        np.random.seed(55)
        rows = []
        for m in rng:
            for ch, base in [("F2F", 5000), ("Telesales", 2500), ("Digital", 800)]:
                rows.append({
                    "ACQ_MONTH": m,
                    "SALES_CHANNEL": ch,
                    "ACT_BY_CHANNEL": int(np.random.poisson(base)),
                })
        return pd.DataFrame(rows)

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

    # SNU + Active 1 by activation date (Sales Trends page)
    if "ACCOUNTCREATEDATE" in sql_up and "SIMS_NEVER_USED" in sql_up:
        rng = pd.date_range(end=today, periods=90, freq="D")
        np.random.seed(99)
        return pd.DataFrame({
            "DT":             rng,
            "SIMS_NEVER_USED": np.random.randint(50, 400, 90),
            "ACTIVE_1":        np.random.randint(200, 1500, 90),
        })

    # Active subscriptions — activations + Active 1 % per day
    if "ACCOUNTCREATEDATE" in sql_up and "ACTIVE1_PCT" in sql_up:
        rng = pd.date_range(end=today, periods=31, freq="D")
        np.random.seed(11)
        activations = (
            np.random.poisson(1800, 31)
            * np.where(pd.DatetimeIndex(rng).dayofweek >= 5, 0.35, 1.0)
        ).astype(int)
        active1_pct = np.clip(np.random.normal(0.72, 0.08, 31), 0.40, 0.98)
        return pd.DataFrame({
            "DT":           rng,
            "ACTIVATIONS":  activations,
            "ACTIVE1_PCT":  active1_pct,
        })

    # Spar / scorecard SIM quality (ACTIVE_1_COUNT, SIMS_NEVER_USED, etc.)
    if "ACCOUNTCREATEDATE" in sql_up and "ACTIVE_1_COUNT" in sql_up:
        return pd.DataFrame({
            "ACTIVE_1_COUNT":   [8200],
            "SIMS_NEVER_USED":  [1400],
            "TOTAL_SIMS":       [11000],
            "ACTIVE_1_PCT":     [0.745],
            "QOS_PROXY_PCT":    [0.63],
        })

    # Active subscriptions — KPI aggregates
    if "ACCOUNTCREATEDATE" in sql_up:
        return pd.DataFrame({
            "ACTIVE7_30_35_PCT":     [0.61],
            "STILL_USING_PCT":       [0.74],
            "QUALITY_INDICATOR_PCT": [0.68],
        })

    # ── New aggregate KPIs ────────────────────────────────────────────────────

    # Total active SIM count (no termination)
    if "ACTIVE_SIM_COUNT" in sql_up:
        return pd.DataFrame({"ACTIVE_SIM_COUNT": [87432]})

    # Total SIMs ever sold (all time)
    if "TOTAL_SIMS_SOLD" in sql_up:
        return pd.DataFrame({"TOTAL_SIMS_SOLD": [245000]})

    # Activations MTD (single row)
    if "ACT_MTD" in sql_up:
        return pd.DataFrame({"ACT_MTD": [4218]})

    # Revenue MTD (single row)
    if "REV_MTD" in sql_up:
        return pd.DataFrame({"REV_MTD": [2341000.0]})

    # Sales channel breakdown
    if "SALES_CHANNEL" in sql_up and "SIMS" in sql_up:
        return pd.DataFrame({
            "CHANNEL": ["F2F", "Telesales", "Digital"],
            "SIMS": [62000, 28000, 8200],
        })

    # SIM grouping (Prepay / Postpaid / FLTE)
    if "SIM_GROUPING" in sql_up:
        return pd.DataFrame({
            "SIM_GROUPING": ["Prepay", "Postpaid", "FLTE"],
            "SIMS": [71000, 18000, 5100],
        })

    # Churn by reason
    if "CHURN_COUNT" in sql_up:
        return pd.DataFrame({
            "CHURN_REASON": ["Not using", "Port out", "Credit fail", "Deceased", "Other"],
            "CHURN_COUNT": [1200, 450, 210, 80, 320],
        })

    return pd.DataFrame()
