"""
SIM Activations & Utilisation — Sales section
Data: UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE
Filters by GROUPING (Prepay / Postpay / FLTE) and SIM_TYPE (e-SIM / Physical SIM)
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, SURFACE_2, BORDER, ZERO_WHITE, CHART_PALETTE,
)
from utils.snowflake_conn import run_query, MERGE_TABLE

st.set_page_config(page_title="SIM Activations & Utilisation | Telco Retail", page_icon="📡", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("SIM Activations & Utilisation", badge="Sales")

# ── Sidebar filters ──────────────────────────────────────────────────────────
GROUPING_OPTIONS = ["Prepay", "Postpay", "FLTE"]
SIM_TYPES = ["e-SIM", "Physical SIM", "PYSICAL-SIM"]

with st.sidebar:
    st.markdown(
        f"<div style='color:{HYPERMINT}; font-weight:700; font-size:13px; "
        f"text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;'>"
        f"Filters</div>",
        unsafe_allow_html=True,
    )
    sel_grouping = st.multiselect("Type (Grouping)", GROUPING_OPTIONS, default=[], placeholder="All types")
    sel_sim = st.multiselect("SIM Type", ["e-SIM", "Physical SIM"], default=[], placeholder="All SIM types")

def _where(col_g="GROUPING", col_s="SIM_TYPE"):
    clauses = []
    if sel_grouping:
        vals = ", ".join(repr(g) for g in sel_grouping)
        clauses.append(f"{col_g} IN ({vals})")
    if sel_sim:
        parts = []
        for s in sel_sim:
            if s == "Physical SIM":
                parts += ["'Physical SIM'", "'PYSICAL-SIM'"]
            else:
                parts.append(repr(s))
        clauses.append(f"{col_s} IN ({', '.join(parts)})")
    return "AND " + " AND ".join(clauses) if clauses else ""

where = _where()

# ── Data loaders ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner="Loading SIM data…")
def load_monthly_by_type(where_frag: str):
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START,
            CASE WHEN SIM_TYPE IN ('Physical SIM','PYSICAL-SIM') THEN 'Physical SIM'
                 ELSE COALESCE(SIM_TYPE,'Unknown') END AS SIM_CAT,
            COUNT(*) AS CNT
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATEADD(month,-13,CURRENT_DATE())
          {where_frag}
        GROUP BY 1,2 ORDER BY 1,2
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_grouping_breakdown(where_frag: str):
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START,
            COALESCE(GROUPING,'Unknown') AS GROUPING,
            COUNT(*) AS CNT
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATEADD(month,-13,CURRENT_DATE())
          {where_frag}
        GROUP BY 1,2 ORDER BY 1,2
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_channel_breakdown(where_frag: str):
    df = run_query(f"""
        SELECT
            COALESCE(NULLIF(SALES_CHANNEL,''),'Unknown') AS SALES_CHANNEL,
            COUNT(*) AS CNT
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATE_TRUNC('month', DATEADD(month,-1,CURRENT_DATE()))
          {where_frag}
        GROUP BY 1 ORDER BY 2 DESC
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_kpis(where_frag: str):
    df = run_query(f"""
        SELECT
            SUM(CASE WHEN ACTIVATION_DATE >= DATE_TRUNC('month',CURRENT_DATE()) THEN 1 ELSE 0 END) AS THIS_MONTH,
            SUM(CASE WHEN ACTIVATION_DATE >= DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE()))
                          AND ACTIVATION_DATE < DATE_TRUNC('month',CURRENT_DATE()) THEN 1 ELSE 0 END) AS LAST_MONTH,
            SUM(CASE WHEN TERMINATION_DATE IS NOT NULL
                          AND ACTIVATION_DATE >= DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE())) THEN 1 ELSE 0 END) AS TERMINATED,
            SUM(CASE WHEN CASE WHEN SIM_TYPE IN ('Physical SIM','PYSICAL-SIM') THEN 'Physical'
                         ELSE 'eSIM' END = 'eSIM'
                          AND ACTIVATION_DATE >= DATE_TRUNC('month',CURRENT_DATE()) THEN 1 ELSE 0 END) AS ESIM_THIS_MONTH
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE()))
          {where_frag}
    """)
    df.columns = [c.upper() for c in df.columns]
    return df.iloc[0] if not df.empty else {}

kpis         = load_kpis(where)
monthly_type = load_monthly_by_type(where)
grouping_df  = load_grouping_breakdown(where)
channel_df   = load_channel_breakdown(where)

monthly_type["MONTH_START"] = pd.to_datetime(monthly_type["MONTH_START"])
grouping_df["MONTH_START"]  = pd.to_datetime(grouping_df["MONTH_START"])

this_month = int(kpis.get("THIS_MONTH") or 0)
last_month = int(kpis.get("LAST_MONTH") or 0)
terminated = int(kpis.get("TERMINATED") or 0)
esim_mtd   = int(kpis.get("ESIM_THIS_MONTH") or 0)

# ── KPI strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("This Month Activations", f"{this_month:,}")
k2.metric("Last Month Activations", f"{last_month:,}", delta=f"{this_month-last_month:+,}")
k3.metric("e-SIM This Month", f"{esim_mtd:,}")
k4.metric("Terminated (prev 2 months)", f"{terminated:,}")
st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

# ── Layout helpers ────────────────────────────────────────────────────────────
def base_layout(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11),
        margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, linecolor="rgba(0,0,0,0)", tickformat=","),
        bargap=0.25, barmode="stack",
    )

# ── Chart 1: Stacked monthly by SIM type ──────────────────────────────────────
c1, c2 = st.columns(2, gap="medium")
with c1:
    pivot = monthly_type.pivot_table(index="MONTH_START", columns="SIM_CAT", values="CNT", fill_value=0)
    fig = go.Figure()
    colours = [HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE]
    for i, col in enumerate(pivot.columns):
        fig.add_trace(go.Bar(
            x=pivot.index.strftime("%b '%y").tolist(),
            y=pivot[col].tolist(),
            name=col,
            marker_color=colours[i % len(colours)],
            marker_line_width=0,
        ))
    fig.update_layout(**base_layout("Monthly Activations by SIM Type (13 months)"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Chart 2: Stacked monthly by Grouping ─────────────────────────────────────
with c2:
    pivot_g = grouping_df.pivot_table(index="MONTH_START", columns="GROUPING", values="CNT", fill_value=0)
    fig2 = go.Figure()
    for i, col in enumerate(pivot_g.columns):
        fig2.add_trace(go.Bar(
            x=pivot_g.index.strftime("%b '%y").tolist(),
            y=pivot_g[col].tolist(),
            name=col,
            marker_color=colours[i % len(colours)],
            marker_line_width=0,
        ))
    fig2.update_layout(**base_layout("Monthly Activations by Type (Prepay / Postpay / FLTE)"))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── Chart 3: Sales channel pie (prev month + this month) ─────────────────────
c3, c4 = st.columns(2, gap="medium")
with c3:
    if not channel_df.empty:
        fig3 = go.Figure(go.Pie(
            labels=channel_df["SALES_CHANNEL"].tolist(),
            values=channel_df["CNT"].tolist(),
            marker_colors=CHART_PALETTE[:len(channel_df)],
            hole=0.45,
            textinfo="label+percent",
            hovertemplate="%{label}<br><b>%{value:,}</b> (%{percent})<extra></extra>",
        ))
        fig3.update_layout(
            title=dict(text="Sales Channel Mix (prev 2 months)", font=dict(color=ZERO_WHITE, size=14), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=11),
            margin=dict(l=8, r=8, t=40, b=8),
            legend=dict(font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
            showlegend=True,
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No channel data.")

# ── Chart 4: e-SIM vs Physical SIM cumulative ─────────────────────────────────
with c4:
    if not monthly_type.empty:
        pivot2 = monthly_type.pivot_table(index="MONTH_START", columns="SIM_CAT", values="CNT", fill_value=0)
        pivot2 = pivot2.cumsum()
        fig4 = go.Figure()
        for i, col in enumerate(pivot2.columns):
            fig4.add_trace(go.Scatter(
                x=pivot2.index.strftime("%b '%y").tolist(),
                y=pivot2[col].tolist(),
                name=col,
                mode="lines",
                line=dict(color=colours[i % len(colours)], width=2),
                fill="tonexty" if i > 0 else None,
                fillcolor=colours[i % len(colours)].replace(")", ",0.15)").replace("rgb", "rgba") if "rgb" in colours[i % len(colours)] else colours[i % len(colours)] + "26",
            ))
        fig4.update_layout(
            title=dict(text="Cumulative SIM Type (13 months)", font=dict(color=ZERO_WHITE, size=14), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=11),
            margin=dict(l=8, r=8, t=40, b=8),
            xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
            yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
            legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
