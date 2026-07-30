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

    # ── The following block was added after a full QA sweep found that the two
    # broad catch-alls further down (bare "MONTH_START" and "ACTIVATION_DATE"+
    # "COUNT") were silently swallowing more specific queries below and handing
    # back the wrong columns - a KeyError/TypeError in demo mode, but more
    # importantly the same silent wrong-shape risk would hit production the
    # moment live Snowflake calls fail and fall back to demo data (as they
    # currently do, mid Auth-Policy outage). Each check here is anchored to a
    # column alias unique to its real query and must stay above those two
    # catch-alls and above each other in the order shown - see comments.

    # SIM Activations & Utilisation (page 11) — monthly by SIM type
    if "SIM_CAT" in sql_up and "CNT" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(61)
        rows = []
        for m in rng:
            for cat, base in [("e-SIM", 2200), ("Physical SIM", 5800), ("Unknown", 150)]:
                rows.append({"MONTH_START": m, "SIM_CAT": cat, "CNT": int(np.random.poisson(base))})
        return pd.DataFrame(rows)

    # SIM Activations & Utilisation — monthly by Grouping (Prepay/Postpay/FLTE)
    if "COALESCE(GROUPING" in sql_up and "CNT" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(62)
        rows = []
        for m in rng:
            for grp, base in [("Prepay", 6500), ("Postpay", 1200), ("FLTE", 450)]:
                rows.append({"MONTH_START": m, "GROUPING": grp, "CNT": int(np.random.poisson(base))})
        return pd.DataFrame(rows)

    # SIM Activations & Utilisation — channel mix, no month dimension. Keyed on
    # "AS SALES_CHANNEL" (this query outputs a SALES_CHANNEL column), not a bare
    # "SALES_CHANNEL" substring - Trading Store Trend's sidebar filter injects a
    # "WHERE SALES_CHANNEL IN (...)" fragment into every one of its own queries,
    # which a bare substring check would have wrongly intercepted.
    if "AS SALES_CHANNEL" in sql_up and "CNT" in sql_up:
        return pd.DataFrame({
            "SALES_CHANNEL": ["F2F", "Telesales", "Digital", "Unknown"],
            "CNT": [9800, 4200, 1300, 210],
        })

    # SIM Activations & Utilisation — KPI strip
    if "ESIM_THIS_MONTH" in sql_up:
        return pd.DataFrame({
            "THIS_MONTH": [8420], "LAST_MONTH": [7960],
            "TERMINATED": [610], "ESIM_THIS_MONTH": [2150],
        })

    # Recharge Qty Dash (page 19) — weekly by recharge type
    if "RECHARGE_DESCRIPTION" in sql_up and "WEEK_START" in sql_up:
        rng = pd.date_range(end=today, periods=26, freq="W-MON")
        np.random.seed(63)
        rows = []
        for w in rng:
            for t, base_qty, base_val in [("PINLESS+ATM", 14000, 320), ("VOUCHER", 6200, 180)]:
                qty = int(np.random.poisson(base_qty))
                rows.append({"WEEK_START": w, "TYPE": t, "QTY": qty, "TOTAL_VALUE": round(qty * base_val, 2)})
        return pd.DataFrame(rows)

    # Recharge Qty Dash — monthly by recharge type
    if "RECHARGE_DESCRIPTION" in sql_up and "MONTH_START" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(64)
        rows = []
        for m in rng:
            for t, base_qty, base_val in [("PINLESS+ATM", 62000, 320), ("VOUCHER", 27000, 180)]:
                qty = int(np.random.poisson(base_qty))
                rows.append({"MONTH_START": m, "TYPE": t, "QTY": qty, "TOTAL_VALUE": round(qty * base_val, 2)})
        return pd.DataFrame(rows)

    # Recharge Qty Dash — KPI strip
    if "QTY_MTD" in sql_up:
        return pd.DataFrame({"QTY_MTD": [58200], "VALUE_MTD": [18624000.0],
                              "QTY_LM": [55100], "VALUE_LM": [17632000.0]})

    # Prepaid Recharge Projection (page 23) — must follow the RECHARGE_DESCRIPTION
    # checks above since that query also contains QTY/TOTAL_VALUE/MONTH_START
    if "TOTAL_VALUE" in sql_up and "QTY" in sql_up and "MONTH_START" in sql_up:
        rng = pd.date_range(end=today, periods=12, freq="MS")
        np.random.seed(65)
        qty = np.random.randint(70000, 95000, len(rng))
        return pd.DataFrame({
            "MONTH_START": rng, "QTY": qty,
            "TOTAL_VALUE": (qty * 320 * np.random.uniform(0.95, 1.05, len(rng))).round(2),
        })

    # Trading Store Trend (page 12) — weekly (must follow RECHARGE_DESCRIPTION checks)
    if "WEEK_START" in sql_up and "CNT" in sql_up:
        rng = pd.date_range(end=today, periods=26, freq="W-MON")
        np.random.seed(66)
        return pd.DataFrame({"WEEK_START": rng, "CNT": np.random.randint(1200, 2600, len(rng))})

    # Trading Store Trend — monthly
    if "MONTH_START" in sql_up and "CNT" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(67)
        return pd.DataFrame({"MONTH_START": rng, "CNT": np.random.randint(5200, 11000, len(rng))})

    # Wastage (page 17) — monthly terminations
    if "TERMINATED" in sql_up and "MONTH_START" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(68)
        return pd.DataFrame({"MONTH_START": rng, "TERMINATED": np.random.randint(900, 2100, len(rng))})

    # Wastage — KPI strip. Must precede "LAST_MONTH"+"THIS_MONTH" further down,
    # which was silently stealing this (both aliases appear here too) and handing
    # back the 20-row tenant table instead of a single aggregate row.
    if "EARLY_CHURN" in sql_up:
        return pd.DataFrame({"THIS_MONTH": [413], "LAST_MONTH": [375],
                              "LAST_7": [92], "EARLY_CHURN": [61]})

    # Wastage — age-at-churn distribution. Must precede "ACTIVATION_DATE"+"COUNT"
    # further down, which was silently stealing this (the query filters on
    # ACTIVATION_DATE IS NOT NULL and uses COUNT(*)) and handing back a daily
    # activations dataframe with no AGE_BAND column.
    if "AGE_BAND" in sql_up:
        return pd.DataFrame({
            "AGE_BAND": ["0-30 days", "31-90 days", "91-180 days", "181-365 days", "365+ days"],
            "CNT": [420, 610, 480, 390, 310],
        })

    # Wastage — churn reasons
    if "AS REASON" in sql_up and "CNT" in sql_up:
        return pd.DataFrame({
            "REASON": ["Not using", "Port out", "Credit fail", "Deceased", "Other"],
            "CNT": [1200, 450, 210, 80, 320],
        })

    # Revenue Metrics (page 26)
    if "PAYING_ACCOUNTS" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(69)
        rev = np.random.uniform(800000, 3000000, len(rng))
        return pd.DataFrame({
            "MONTH_START": rng, "TOTAL_REVENUE": rev.round(0),
            "PAYING_ACCOUNTS": np.random.randint(28000, 42000, len(rng)),
        })

    # Recharge Trend by Recharge Type (page 20) — checked before the
    # Revenue Comparisons check below, since its column names also contain
    # the substrings "CELLC"/"VOUCHER"/"BILLRUN" inside longer aliases
    if "REVENUE_CELLC_RECHARGE_QUANTITY" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(71)
        n = len(rng)
        qty_cols = {
            "REVENUE_CELLC_RECHARGE_QUANTITY": np.random.randint(40000, 60000, n),
            "REVENUE_RETAIL_VOUCHER_REDEMPTIONS_QUANTITY": np.random.randint(15000, 25000, n),
            "REVENUE_APP_PURCHASES_QUANTITY": np.random.randint(8000, 14000, n),
            "REVENUE_MAY_BILLRUN_QUANITITY": np.random.randint(6000, 10000, n),
            "REVENUE_POST_PAID_SUCCESSFULL_QUANTITY": np.random.randint(3000, 6000, n),
            "REVENUE_MAY_WEBSITE_RECHARGES_QUANTITY": np.random.randint(1000, 3000, n),
        }
        data = {"MONTH_START": rng}
        for qty_col, vals in qty_cols.items():
            val_col = qty_col.replace("QUANTITY", "VALUE").replace("QUANITITY", "VALUE")
            data[qty_col] = vals
            data[val_col] = (vals * np.random.uniform(280, 350)).round(0)
        return pd.DataFrame(data)

    # Revenue Comparisons (page 22) — keyed on "AS CELLC"/"AS VOUCHER"/"AS BILLRUN"
    # (this query aliases each stream to its own short column), not bare substring
    # matches - "CELLC"/"VOUCHER"/"BILLRUN" also appear inside longer column names
    # like REVENUE_CELLC_RECHARGE_VALUE in several other queries (Exco Scorecard's
    # REV_MTD, Retain Users' per-recipient revenue, etc.) that don't want this shape.
    # Also excludes TOTAL_REVENUE so it doesn't shadow Recharge Revenue Monthly's
    # query, which aliases the same 3 streams plus a combined TOTAL_REVENUE.
    if ("AS CELLC" in sql_up and "AS VOUCHER" in sql_up and "AS BILLRUN" in sql_up
            and "TOTAL_REVENUE" not in sql_up):
        rng = pd.date_range(end=today, periods=14, freq="MS")
        np.random.seed(70)
        rev = np.random.uniform(800000, 3000000, len(rng))
        return pd.DataFrame({
            "MONTH_START": rng,
            "CELLC":    (rev * 0.40).round(0), "VOUCHER":  (rev * 0.15).round(0),
            "APP":      (rev * 0.20).round(0), "BILLRUN":  (rev * 0.15).round(0),
            "POSTPAID": (rev * 0.10).round(0),
        })

    # Cohort-aging revenue (utils/cohort.py) — feeds pages 16, 32, 40
    if "AGE_MONTHS" in sql_up and "COHORT_MONTH" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(72)
        rows = []
        for m in rng:
            acquired = int(np.random.randint(2000, 6000))
            for age in range(0, 7):
                active = min(acquired, max(0, int(acquired * (0.85 ** age) * np.random.uniform(0.9, 1.1))))
                revenue = round(active * np.random.uniform(180, 260), 2)
                rows.append({
                    "COHORT_MONTH": m, "AGE_MONTHS": age,
                    "ACQUIRED": acquired, "ACTIVE": active, "REVENUE": revenue,
                })
        return pd.DataFrame(rows)

    # Exco Scorecard — activations MTD / last month. Moved ahead of the
    # generic "ACTIVATION_DATE"+"COUNT" catch-all further down, which was
    # silently stealing this query and handing back a daily-activations
    # dataframe with no ACT_MTD column.
    if "ACT_MTD" in sql_up:
        return pd.DataFrame({"ACT_MTD": [4218]})

    # Retain Users via Free Airtime (page 40) — excludes REWARD_COST_PER_ACT
    # so it doesn't shadow Acquisition Cost / Value of New Business's queries
    if ("REWARD_QTY" in sql_up and "REWARD_VALUE" in sql_up
            and "REWARD_COST_PER_ACT" not in sql_up):
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(73)
        qty = np.random.randint(1800, 4200, len(rng))
        return pd.DataFrame({
            "MONTH_START": rng, "REWARD_QTY": qty,
            "REWARD_VALUE": (qty * np.random.uniform(85, 140)).round(0),
        })

    # Retain Users via Free Airtime — retention rate by reward group
    if "STILL_ACTIVE" in sql_up and "GRP" in sql_up:
        return pd.DataFrame({
            "GRP": ["Reward Recipient", "No Reward"],
            "TOTAL": [4200, 18600],
            "STILL_ACTIVE": [3150, 9800],
        })

    # Retain Users via Free Airtime — revenue per reward recipient
    if "RECIPIENT_REVENUE" in sql_up:
        rng = pd.date_range(end=today, periods=6, freq="MS")
        np.random.seed(78)
        recipients = np.random.randint(600, 1800, len(rng))
        return pd.DataFrame({
            "MONTH_START": rng, "RECIPIENTS": recipients,
            "RECIPIENT_REVENUE": (recipients * np.random.uniform(180, 320, len(rng))).round(2),
        })

    # Subscriptions (page 14) — KPI strip
    if "BILLED_MTD" in sql_up:
        return pd.DataFrame({"BILLED_MTD": [6100], "PAID_MTD": [5480],
                              "BILLED_LM": [5820], "AMT_MTD": [1830000.0]})

    # Subscriptions Cohort (page 15) — acquired-month x billing-month grid
    if "ACQUIRED_MONTH" in sql_up:
        rng = pd.date_range(end=today, periods=12, freq="MS")
        np.random.seed(74)
        rows = []
        for acq_m in rng:
            for bill_m in pd.date_range(acq_m, periods=6, freq="MS"):
                if bill_m > pd.Timestamp(today):
                    continue
                billed = int(np.random.randint(300, 1200))
                paid = int(billed * np.random.uniform(0.75, 0.95))
                rows.append({
                    "ACQUIRED_MONTH": acq_m, "BILLING_MONTH": bill_m,
                    "BILLED": billed, "PAID": paid,
                    "BILLED_AMT": round(billed * 349, 2), "PAID_AMT": round(paid * 349, 2),
                })
        return pd.DataFrame(rows)

    # Shared: Subscriptions' monthly-by-channel (page 14) and Subscriptions
    # Cohort's monthly trend (page 15) both want MONTH_START/CHANNEL/BILLED/PAID
    if "BILLED" in sql_up and "PAID" in sql_up and "MONTH_START" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(75)
        rows = []
        for m in rng:
            for ch, base in [("MOBILE STORE", 2200), ("DISTRIBUTION", 1400), ("ONLINE", 900),
                              ("FINANCIAL SERVICES", 300), ("AFFINITY", 250), ("NRP", 120)]:
                billed = int(np.random.poisson(base))
                paid = int(billed * np.random.uniform(0.75, 0.95))
                rows.append({
                    "MONTH_START": m, "CHANNEL": ch, "BILLED": billed, "PAID": paid,
                    "BILLED_AMT": round(billed * 349, 2), "PAID_AMT": round(paid * 349, 2),
                })
        return pd.DataFrame(rows)

    # Commercial Cohort Analysis (page 16) — acquisitions
    if "STILL_ACTIVE" in sql_up and "ACQ_MONTH" in sql_up:
        rng = pd.date_range(end=today, periods=12, freq="MS")
        np.random.seed(76)
        acquired = np.random.randint(2000, 6000, len(rng))
        still_active = (acquired * np.random.uniform(0.55, 0.85, len(rng))).astype(int)
        return pd.DataFrame({"ACQ_MONTH": rng, "ACQUIRED": acquired, "STILL_ACTIVE": still_active})

    # Commercial Cohort Analysis — revenue per cohort
    if "ACCOUNTS" in sql_up and "ACQ_MONTH" in sql_up:
        rng = pd.date_range(end=today, periods=12, freq="MS")
        np.random.seed(77)
        accounts = np.random.randint(1800, 5500, len(rng))
        return pd.DataFrame({
            "ACQ_MONTH": rng, "ACCOUNTS": accounts,
            "TOTAL_REVENUE": (accounts * np.random.uniform(180, 260, len(rng))).round(2),
        })

    # Subscriptions - App (page 44) KPI strip. Must precede the generic
    # "BOOK_SIZE" check below (both queries share that alias).
    if "ACTIVE_USERS" in sql_up:
        return pd.DataFrame({
            "ACTIVE_USERS": [46125], "BOOK_SIZE": [2614], "SALES_YDAY": [20],
            "SALES_MTD": [350], "SALES_L30": [349], "SALES_L7": [105], "FTC_PCT": [1.0],
        })

    # Subscriptions billing pages (14, 45-48) — KPI strip
    if "BOOK_SIZE" in sql_up:
        return pd.DataFrame({
            "BOOK_SIZE": [4253], "FTC_PCT": [0.5507], "MONTH2_PCT": [0.5130],
            "SALES_YDAY": [77], "SALES_MTD": [1467], "SALES_L30": [1529], "SALES_L7": [517],
        })

    # Subscriptions pages — deal/product breakdown (no month dimension).
    # Must precede the "AS SALES"+"MONTH_START" and bare "AS SALES" checks below.
    if "AS SALES" in sql_up and "DEALDESCRIPTION" in sql_up:
        return pd.DataFrame({
            "DEALDESCRIPTION": ["Triplesave", "Uconnect Upsell R399", "Uconnect Upsell R349", "Breakfree"],
            "SALES": [77, 34, 21, 9],
        })

    # Subscriptions pages — monthly new-sales trend
    if "AS SALES" in sql_up and "MONTH_START" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(79)
        return pd.DataFrame({"MONTH_START": rng, "SALES": np.random.randint(800, 4500, len(rng))})

    # Subscriptions pages — daily new-sales trend (fallback: no DEALDESCRIPTION,
    # no MONTH_START - must be checked last among the three "AS SALES" variants)
    if "AS SALES" in sql_up:
        rng = pd.date_range(end=today, periods=30, freq="D")
        np.random.seed(80)
        return pd.DataFrame({"DT": rng, "SALES": np.random.randint(30, 90, len(rng))})

    # Subscriptions billing pages — collected book by deal, monthly
    if "DEALDESCRIPTION" in sql_up and "BILLED" in sql_up:
        rng = pd.date_range(end=today, periods=13, freq="MS")
        np.random.seed(81)
        rows = []
        for m in rng:
            for deal, base in [("Triplesave", 2000), ("Uconnect Upsell R399", 1400),
                                ("Uconnect Upsell R349", 900), ("Breakfree", 300)]:
                rows.append({"MONTH_START": m, "DEALDESCRIPTION": deal, "BILLED": int(np.random.poisson(base))})
        return pd.DataFrame(rows)

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

    # Rate of Sale 7-day avg (scorecard) — must precede the generic daily-activations check below
    if "ROS_7_DAYS" in sql_up:
        return pd.DataFrame({"ROS_7_DAYS": [34.5]})

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

    # Spar / scorecard SIM quality (ACTIVE_1_COUNT, SIMS_NEVER_USED, etc.) — must precede the
    # Sales Trends SNU-by-day check below, since this query's SQL also contains "SIMS_NEVER_USED"
    if "ACCOUNTCREATEDATE" in sql_up and "ACTIVE_1_COUNT" in sql_up:
        return pd.DataFrame({
            "ACTIVE_1_COUNT":          [8200],
            "SIMS_NEVER_USED":         [1400],
            "REGISTERED_BASE_35_60":   [9800],
            "TOTAL_SIMS":              [11000],
            "ACTIVE_1_PCT":            [0.745],
            "QOS_PROXY_PCT":           [0.63],
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

    # Last data refresh timestamp (home page indicator)
    if "MINUTES_AGO" in sql_up:
        return pd.DataFrame({"LAST_REFRESH": ["demo"], "MINUTES_AGO": [0]})

    # Churn by reason
    if "CHURN_COUNT" in sql_up:
        return pd.DataFrame({
            "CHURN_REASON": ["Not using", "Port out", "Credit fail", "Deceased", "Other"],
            "CHURN_COUNT": [1200, 450, 210, 80, 320],
        })

    return pd.DataFrame()
