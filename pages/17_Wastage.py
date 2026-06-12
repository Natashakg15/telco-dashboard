"""
Wastage — Commercial section
Data: UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE
Measures SIM terminations, churn reasons, and age-at-termination distribution.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE, CHART_PALETTE,
)
from utils.snowflake_conn import run_query, MERGE_TABLE

st.set_page_config(page_title="Wastage | Telco Retail", page_icon="📉", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Wastage", badge="Commercial")

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner="Loading wastage data…")
def load_monthly_churn():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', TERMINATION_DATE) AS MONTH_START,
            COUNT(*) AS TERMINATED
        FROM {MERGE_TABLE}
        WHERE TERMINATION_DATE IS NOT NULL
          AND TERMINATION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_churn_reasons():
    df = run_query(f"""
        SELECT
            COALESCE(NULLIF(CHURN_REASON,''),'Unknown') AS REASON,
            COUNT(*) AS CNT
        FROM {MERGE_TABLE}
        WHERE TERMINATION_DATE IS NOT NULL
          AND TERMINATION_DATE >= DATEADD(month,-6,CURRENT_DATE())
        GROUP BY 1 ORDER BY 2 DESC
        LIMIT 15
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_age_at_churn():
    df = run_query(f"""
        SELECT
            CASE
                WHEN DATEDIFF('day', ACTIVATION_DATE, TERMINATION_DATE) <= 30  THEN '0-30 days'
                WHEN DATEDIFF('day', ACTIVATION_DATE, TERMINATION_DATE) <= 90  THEN '31-90 days'
                WHEN DATEDIFF('day', ACTIVATION_DATE, TERMINATION_DATE) <= 180 THEN '91-180 days'
                WHEN DATEDIFF('day', ACTIVATION_DATE, TERMINATION_DATE) <= 365 THEN '181-365 days'
                ELSE '365+ days'
            END AS AGE_BAND,
            COUNT(*) AS CNT
        FROM {MERGE_TABLE}
        WHERE TERMINATION_DATE IS NOT NULL
          AND ACTIVATION_DATE IS NOT NULL
          AND TERMINATION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_kpis():
    df = run_query(f"""
        SELECT
            SUM(CASE WHEN TERMINATION_DATE >= DATE_TRUNC('month',CURRENT_DATE()) THEN 1 ELSE 0 END) AS THIS_MONTH,
            SUM(CASE WHEN TERMINATION_DATE >= DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE()))
                          AND TERMINATION_DATE < DATE_TRUNC('month',CURRENT_DATE()) THEN 1 ELSE 0 END) AS LAST_MONTH,
            SUM(CASE WHEN TERMINATION_DATE >= CURRENT_DATE()-6 THEN 1 ELSE 0 END) AS LAST_7,
            SUM(CASE WHEN DATEDIFF('day',ACTIVATION_DATE,TERMINATION_DATE) <= 30
                          AND TERMINATION_DATE >= DATEADD(month,-1,CURRENT_DATE()) THEN 1 ELSE 0 END) AS EARLY_CHURN
        FROM {MERGE_TABLE}
        WHERE TERMINATION_DATE IS NOT NULL
          AND TERMINATION_DATE >= DATEADD(month,-1,CURRENT_DATE())
    """)
    df.columns = [c.upper() for c in df.columns]
    return df.iloc[0] if not df.empty else {}

kpis         = load_kpis()
monthly_churn = load_monthly_churn()
churn_reasons = load_churn_reasons()
age_at_churn  = load_age_at_churn()

monthly_churn["MONTH_START"] = pd.to_datetime(monthly_churn["MONTH_START"])

this_m = int(kpis.get("THIS_MONTH") or 0)
last_m = int(kpis.get("LAST_MONTH") or 0)
last_7 = int(kpis.get("LAST_7") or 0)
early  = int(kpis.get("EARLY_CHURN") or 0)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Terminated This Month", f"{this_m:,}")
k2.metric("Terminated Last Month", f"{last_m:,}", delta=f"{this_m-last_m:+,}", delta_color="inverse")
k3.metric("Last 7 Days", f"{last_7:,}")
k4.metric("Early Churn ≤30d (prev 2 months)", f"{early:,}")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

def _base(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
        bargap=0.3,
    )

c1, c2 = st.columns(2, gap="medium")

with c1:
    fig = go.Figure(go.Bar(
        x=monthly_churn["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=monthly_churn["TERMINATED"].tolist(),
        marker_color=HIGHVOLT_ORANGE, marker_line_width=0,
        hovertemplate="%{x}<br><b>Terminated: %{y:,}</b><extra></extra>",
    ))
    fig.update_layout(**_base("Monthly Terminations (13 months)"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    if not churn_reasons.empty:
        fig2 = go.Figure(go.Bar(
            y=churn_reasons["REASON"].tolist(),
            x=churn_reasons["CNT"].tolist(),
            orientation="h",
            marker_color=SONIC_BLUE, marker_line_width=0,
            hovertemplate="%{y}<br><b>%{x:,}</b><extra></extra>",
        ))
        layout2 = dict(
            title=dict(text="Churn Reasons (last 6 months)", font=dict(color=ZERO_WHITE, size=14), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
            xaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
            yaxis=dict(showgrid=False, autorange="reversed"),
            bargap=0.3,
        )
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No churn reason data.")

c3, c4 = st.columns(2, gap="medium")

with c3:
    if not age_at_churn.empty:
        order = ["0-30 days","31-90 days","91-180 days","181-365 days","365+ days"]
        age_at_churn["SORT"] = age_at_churn["AGE_BAND"].apply(lambda x: order.index(x) if x in order else 99)
        age_at_churn = age_at_churn.sort_values("SORT")
        fig3 = go.Figure(go.Bar(
            x=age_at_churn["AGE_BAND"].tolist(),
            y=age_at_churn["CNT"].tolist(),
            marker_color=ULTRAVIOLET, marker_line_width=0,
            hovertemplate="%{x}<br><b>%{y:,}</b><extra></extra>",
        ))
        fig3.update_layout(**_base("Age at Churn Distribution (13 months)"))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No age-at-churn data.")

with c4:
    # Pie donut of age bands
    if not age_at_churn.empty:
        fig4 = go.Figure(go.Pie(
            labels=age_at_churn["AGE_BAND"].tolist(),
            values=age_at_churn["CNT"].tolist(),
            marker_colors=CHART_PALETTE[:len(age_at_churn)],
            hole=0.45,
            textinfo="label+percent",
        ))
        fig4.update_layout(
            title=dict(text="Age at Churn — Share", font=dict(color=ZERO_WHITE, size=14), x=0),
            paper_bgcolor=SURFACE_1, font=dict(color="#888", size=11),
            margin=dict(l=8, r=8, t=40, b=8),
            legend=dict(font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
