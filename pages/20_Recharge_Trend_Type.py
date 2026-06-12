"""
Recharge Trend by Recharge Type — Recharges section
Data: UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE
All revenue streams trended over time, togglable by type.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE, SURFACE_2,
)
from utils.snowflake_conn import run_query

REV_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE"

REVENUE_TYPES = {
    "Cell C Recharge":       ("REVENUE_CELLC_RECHARGE_QUANTITY",       "REVENUE_CELLC_RECHARGE_VALUE"),
    "Retail Voucher":        ("REVENUE_RETAIL_VOUCHER_REDEMPTIONS_QUANTITY", "REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE"),
    "App Purchases":         ("REVENUE_APP_PURCHASES_QUANTITY",         "REVENUE_APP_PURCHASES_VALUE"),
    "Billrun":               ("REVENUE_MAY_BILLRUN_QUANITITY",          "REVENUE_MAY_BILLRUN_VALUE"),
    "Postpaid (Successful)": ("REVENUE_POST_PAID_SUCCESSFULL_QUANTITY", "REVENUE_POST_PAID_SUCCESSFULL_VALUE"),
    "WhatsApp Purchases":    ("REVENUE_WHATSAPP_PURCHASES_QUANTITY",    "REVENUE_WHATSAPP_PURCHASES_VALUE"),
    "Website Recharges":     ("REVENUE_MAY_WEBSITE_RECHARGES_QUANTITY", "REVENUE_MAY_WEBSITE_RECHARGES_VALUE"),
}

PALETTE = [HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE, "#9b59b6", "#f1c40f", "#1abc9c"]

st.set_page_config(page_title="Recharge Trend by Type | Telco Retail", page_icon="📊", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Recharge Trend by Recharge Type", badge="Recharges")

with st.sidebar:
    st.markdown(
        f"<div style='color:{HYPERMINT}; font-weight:700; font-size:13px; "
        f"text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;'>"
        f"Revenue Types</div>",
        unsafe_allow_html=True,
    )
    sel_types = st.multiselect(
        "Select types", list(REVENUE_TYPES.keys()),
        default=list(REVENUE_TYPES.keys()),
        label_visibility="collapsed",
    )

@st.cache_data(ttl=1800, show_spinner="Loading revenue trends…")
def load_monthly_all():
    qty_cols = ", ".join(f"SUM(COALESCE({v[0]},0)) AS {v[0]}" for v in REVENUE_TYPES.values())
    val_cols = ", ".join(f"SUM(COALESCE({v[1]},0)) AS {v[1]}" for v in REVENUE_TYPES.values())
    df = run_query(f"""
        SELECT DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
               {qty_cols}, {val_cols}
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

df = load_monthly_all()
df["MONTH_START"] = pd.to_datetime(df["MONTH_START"])
x_labels = df["MONTH_START"].dt.strftime("%b '%y").tolist()

def _base(title="", barmode="stack"):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
        bargap=0.3, barmode=barmode,
        legend=dict(orientation="h", y=-0.18, font=dict(color=ZERO_WHITE, size=10), bgcolor="rgba(0,0,0,0)"),
    )

# ── Chart 1: Stacked quantity ─────────────────────────────────────────────────
c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure()
    for i, name in enumerate(sel_types):
        qty_col = REVENUE_TYPES[name][0].upper()
        if qty_col in df.columns:
            fig.add_trace(go.Bar(
                x=x_labels, y=df[qty_col].tolist(),
                name=name, marker_color=PALETTE[i % len(PALETTE)], marker_line_width=0,
            ))
    fig.update_layout(**_base("Monthly Recharge Quantity by Type"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    fig2 = go.Figure()
    for i, name in enumerate(sel_types):
        val_col = REVENUE_TYPES[name][1].upper()
        if val_col in df.columns:
            fig2.add_trace(go.Bar(
                x=x_labels, y=df[val_col].tolist(),
                name=name, marker_color=PALETTE[i % len(PALETTE)], marker_line_width=0,
            ))
    layout2 = _base("Monthly Revenue (R) by Type")
    layout2["yaxis"] = dict(showgrid=True, gridcolor=BORDER, tickprefix="R", tickformat=",.0f")
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── Chart 2: Line trends ──────────────────────────────────────────────────────
st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
c3, c4 = st.columns(2, gap="medium")
with c3:
    fig3 = go.Figure()
    for i, name in enumerate(sel_types):
        val_col = REVENUE_TYPES[name][1].upper()
        if val_col in df.columns:
            fig3.add_trace(go.Scatter(
                x=x_labels, y=df[val_col].tolist(),
                name=name, mode="lines",
                line=dict(color=PALETTE[i % len(PALETTE)], width=2),
            ))
    layout3 = _base("Revenue Trend Lines by Type")
    layout3["barmode"] = "group"
    layout3["yaxis"] = dict(showgrid=True, gridcolor=BORDER, tickprefix="R", tickformat=",.0f")
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    # Month-on-month % change for largest revenue type
    if sel_types:
        name = sel_types[0]
        val_col = REVENUE_TYPES[name][1].upper()
        if val_col in df.columns:
            vals = df[val_col].tolist()
            mom = [None] + [
                round((vals[i] - vals[i-1]) / vals[i-1] * 100, 1) if vals[i-1] else None
                for i in range(1, len(vals))
            ]
            colors_mom = [HYPERMINT if (v or 0) >= 0 else HIGHVOLT_ORANGE for v in mom]
            fig4 = go.Figure(go.Bar(
                x=x_labels, y=mom,
                marker_color=colors_mom, marker_line_width=0,
                hovertemplate="%{x}<br><b>%{y:.1f}%</b><extra></extra>",
            ))
            layout4 = _base(f"MoM % Change — {name}")
            layout4["yaxis"] = dict(showgrid=True, gridcolor=BORDER, ticksuffix="%")
            fig4.update_layout(**layout4)
            st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Select a type to see MoM change.")
    else:
        st.info("Select at least one type.")
