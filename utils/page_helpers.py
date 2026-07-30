"""
Shared helpers for placeholder pages and common layouts.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.ci import (
    inject_css, page_header,
    HYPERMINT, HIGHVOLT_ORANGE, SONIC_BLUE,
    SURFACE_1, BORDER, ZERO_WHITE, SURFACE_2,
)

USAGE_TABLE = "UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS"
BILLING_TABLE = "UCONNECT_DW.ANALYTICS.VW_SPOT_BILLING_DATA"
APP_SUBS_TABLE = "UCONNECT_DW.ANALYTICS.VW_UCONNECT_APP_SUBSCRIPTIONS"


def render_subscription_billing_page(campaign_names: list):
    """
    Renders the 'Subscriptions - <Channel>' page layout for channels backed by
    VW_SPOT_BILLING_DATA, filtered to a set of CAMPAIGNNAME values (confirmed
    live against Snowflake - see pages/44-48 for the exact mapping per channel
    and its confidence level). Matches the real PBI layout from user screenshots:
    KPI row (book size, FTC%, Month 2%), monthly/daily new-sales trend lines,
    collected-book-by-deal stacked bar, KPI row 2 (yesterday/MTD/L30/L7avg),
    two DEALDESCRIPTION breakdown tables.
    """
    import streamlit as st
    import pandas as pd
    import plotly.graph_objects as go
    from utils.snowflake_conn import run_query
    from utils.ci import HYPERMINT, SONIC_BLUE, BORDER, ZERO_WHITE, SURFACE_1, SURFACE_2

    camp_list = ", ".join(repr(c) for c in campaign_names)

    @st.cache_data(ttl=1800, show_spinner="Loading subscription data…")
    def _load_kpis():
        df = run_query(f"""
            SELECT
                COUNT(DISTINCT CASE WHEN CURRENTPOLICYSTATUS NOT IN ('Cancelled','Lapsed') THEN POLICYNO END) AS BOOK_SIZE,
                SUM(CASE WHEN ISFIRSTCOLLECTION = 1 THEN PAID_FLAG ELSE 0 END)::FLOAT
                    / NULLIF(SUM(CASE WHEN ISFIRSTCOLLECTION = 1 THEN 1 ELSE 0 END), 0) AS FTC_PCT,
                SUM(CASE WHEN DATEDIFF('month', FIRSTBILLDATE, BILLINGDATE) = 1 THEN PAID_FLAG ELSE 0 END)::FLOAT
                    / NULLIF(SUM(CASE WHEN DATEDIFF('month', FIRSTBILLDATE, BILLINGDATE) = 1 THEN 1 ELSE 0 END), 0) AS MONTH2_PCT,
                COUNT(DISTINCT CASE WHEN SALESDATE = CURRENT_DATE() - 1 THEN POLICYNO END) AS SALES_YDAY,
                COUNT(DISTINCT CASE WHEN SALESDATE >= DATE_TRUNC('month', CURRENT_DATE()) THEN POLICYNO END) AS SALES_MTD,
                COUNT(DISTINCT CASE WHEN SALESDATE >= CURRENT_DATE() - 30 THEN POLICYNO END) AS SALES_L30,
                COUNT(DISTINCT CASE WHEN SALESDATE >= CURRENT_DATE() - 7 THEN POLICYNO END) AS SALES_L7
            FROM {BILLING_TABLE}
            WHERE ORGANIZATION = 'uconnect' AND CAMPAIGNNAME IN ({camp_list})
        """)
        df.columns = [c.upper() for c in df.columns]
        return df.iloc[0] if not df.empty else {}

    @st.cache_data(ttl=1800, show_spinner=False)
    def _load_monthly_sales():
        df = run_query(f"""
            SELECT DATE_TRUNC('month', SALESDATE) AS MONTH_START, COUNT(DISTINCT POLICYNO) AS SALES
            FROM {BILLING_TABLE}
            WHERE ORGANIZATION = 'uconnect' AND CAMPAIGNNAME IN ({camp_list})
              AND SALESDATE >= DATEADD(month, -13, CURRENT_DATE())
            GROUP BY 1 ORDER BY 1
        """)
        df.columns = [c.upper() for c in df.columns]
        return df

    @st.cache_data(ttl=1800, show_spinner=False)
    def _load_daily_sales():
        df = run_query(f"""
            SELECT SALESDATE AS DT, COUNT(DISTINCT POLICYNO) AS SALES
            FROM {BILLING_TABLE}
            WHERE ORGANIZATION = 'uconnect' AND CAMPAIGNNAME IN ({camp_list})
              AND SALESDATE >= CURRENT_DATE() - 30
            GROUP BY 1 ORDER BY 1
        """)
        df.columns = [c.upper() for c in df.columns]
        return df

    @st.cache_data(ttl=1800, show_spinner=False)
    def _load_collected_book():
        df = run_query(f"""
            SELECT DATE_TRUNC('month', BILLINGDATE) AS MONTH_START,
                   COALESCE(DEALDESCRIPTION, 'Unknown') AS DEALDESCRIPTION,
                   SUM(BILLED_COUNT) AS BILLED
            FROM {BILLING_TABLE}
            WHERE ORGANIZATION = 'uconnect' AND CAMPAIGNNAME IN ({camp_list})
              AND BILLINGDATE >= DATEADD(month, -13, CURRENT_DATE())
            GROUP BY 1, 2 ORDER BY 1, 2
        """)
        df.columns = [c.upper() for c in df.columns]
        return df

    @st.cache_data(ttl=1800, show_spinner=False)
    def _load_deal_breakdown(days_back: int):
        df = run_query(f"""
            SELECT COALESCE(DEALDESCRIPTION, 'Unknown') AS DEALDESCRIPTION, COUNT(DISTINCT POLICYNO) AS SALES
            FROM {BILLING_TABLE}
            WHERE ORGANIZATION = 'uconnect' AND CAMPAIGNNAME IN ({camp_list})
              AND SALESDATE >= CURRENT_DATE() - {days_back}
            GROUP BY 1 ORDER BY 2 DESC
        """)
        df.columns = [c.upper() for c in df.columns]
        return df

    kpis = _load_kpis()
    monthly = _load_monthly_sales()
    daily = _load_daily_sales()
    collected = _load_collected_book()
    deals_yday = _load_deal_breakdown(1)
    deals_l30 = _load_deal_breakdown(30)

    def _pct(v):
        try:
            f = float(v)
            return f"{f * 100:.2f}%" if f == f else "—"
        except (TypeError, ValueError):
            return "—"

    k1, k2, k3 = st.columns(3)
    k1.metric("Subscription Book", f"{int(kpis.get('BOOK_SIZE') or 0):,}")
    k2.metric("FTC %", _pct(kpis.get("FTC_PCT")))
    k3.metric("Month 2 %", _pct(kpis.get("MONTH2_PCT")))

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    def _base(title=""):
        return dict(
            title=dict(text=title, font=dict(color=ZERO_WHITE, size=13), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=10), margin=dict(l=8, r=8, t=32, b=8), height=260,
            xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=9, color="#888")),
            yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
        )

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        if not monthly.empty:
            monthly["MONTH_START"] = pd.to_datetime(monthly["MONTH_START"])
            fig = go.Figure(go.Scatter(
                x=monthly["MONTH_START"].dt.strftime("%b '%y").tolist(), y=monthly["SALES"].tolist(),
                mode="lines+markers", line=dict(color=HYPERMINT, width=2), marker=dict(size=4),
            ))
            fig.update_layout(**_base("Monthly trend of new sales"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            placeholder_chart("Monthly trend of new sales", "No sales in window", height=260)
    with c2:
        if not daily.empty:
            daily["DT"] = pd.to_datetime(daily["DT"])
            fig2 = go.Figure(go.Scatter(
                x=daily["DT"].dt.strftime("%d %b").tolist(), y=daily["SALES"].tolist(),
                mode="lines+markers", line=dict(color=SONIC_BLUE, width=2), marker=dict(size=4),
            ))
            fig2.update_layout(**_base("Daily trend of new sales"))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            placeholder_chart("Daily trend of new sales", "No sales in last 30 days", height=260)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    if not collected.empty:
        pivot = collected.pivot_table(index="MONTH_START", columns="DEALDESCRIPTION", values="BILLED", fill_value=0)
        from utils.ci import CHART_PALETTE
        fig3 = go.Figure()
        for i, col in enumerate(pivot.columns):
            fig3.add_trace(go.Bar(
                x=pivot.index.strftime("%b '%y").tolist(), y=pivot[col].tolist(),
                name=col, marker_color=CHART_PALETTE[i % len(CHART_PALETTE)], marker_line_width=0,
            ))
        layout3 = _base("Collected book trend via card")
        layout3["barmode"] = "stack"
        layout3["height"] = 320
        layout3["legend"] = dict(orientation="h", y=-0.25, font=dict(color=ZERO_WHITE, size=9), bgcolor="rgba(0,0,0,0)")
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    else:
        placeholder_chart("Collected book trend via card", "No billing data in window", height=320)

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    k4, k5, k6, k7 = st.columns(4)
    k4.metric("Sales Yesterday", f"{int(kpis.get('SALES_YDAY') or 0):,}")
    k5.metric("Sales MTD", f"{int(kpis.get('SALES_MTD') or 0):,}")
    k6.metric("Sales L30 Days", f"{int(kpis.get('SALES_L30') or 0):,}")
    l7avg = (float(kpis.get("SALES_L7") or 0) / 7)
    k7.metric("L7 Day Avg", f"{l7avg:,.2f}")

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    t1, t2 = st.columns(2, gap="medium")
    for col, df, label in [(t1, deals_yday, "Sales Yesterday"), (t2, deals_l30, "Sales Last 30 Days")]:
        with col:
            st.markdown(
                f"<h4 style='color:{HYPERMINT}; font-size:13px; margin-bottom:6px;'>{label}</h4>",
                unsafe_allow_html=True,
            )
            if df.empty:
                st.caption("No sales in this window.")
            else:
                rows_html = "".join(
                    f"<tr><td style='padding:4px 8px; color:{ZERO_WHITE}; font-size:12px;'>{r.DEALDESCRIPTION}</td>"
                    f"<td style='padding:4px 8px; color:{ZERO_WHITE}; font-size:12px; text-align:right;'>{r.SALES:,}</td></tr>"
                    for r in df.itertuples()
                )
                st.markdown(
                    f"<table style='width:100%; border-collapse:collapse; background:{SURFACE_1};'>"
                    f"<thead><tr><th style='padding:4px 8px; background:{SURFACE_2}; font-size:10px; "
                    f"text-align:left; color:#555;'>Product</th><th style='padding:4px 8px; background:{SURFACE_2}; "
                    f"font-size:10px; text-align:right; color:#555;'>Sales</th></tr></thead>"
                    f"<tbody>{rows_html}</tbody></table>",
                    unsafe_allow_html=True,
                )


def render_app_subscription_page():
    """
    Renders the 'Subscriptions - App' page, backed by VW_UCONNECT_APP_SUBSCRIPTIONS
    (confirmed live: its DESCRIPTION values match the app-bundle deal names shown
    in the real PBI page - e.g. '10GB', 'UNLIMITED TALK + 10GB' - a different
    table from the CAMPAIGNNAME-based billing pages).
    """
    import streamlit as st
    import pandas as pd
    import plotly.graph_objects as go
    from utils.snowflake_conn import run_query
    from utils.ci import HYPERMINT, SONIC_BLUE, BORDER, ZERO_WHITE, SURFACE_1, SURFACE_2, CHART_PALETTE

    @st.cache_data(ttl=1800, show_spinner="Loading app subscription data…")
    def _load_kpis():
        df = run_query(f"""
            SELECT
                COUNT(DISTINCT ACCOUNT_NUMBER) AS ACTIVE_USERS,
                COUNT(DISTINCT CASE WHEN TRANSACTION_DATE >= DATE_TRUNC('month', CURRENT_DATE()) THEN ACCOUNT_NUMBER END) AS BOOK_SIZE,
                COUNT(DISTINCT CASE WHEN TRANSACTION_DATE = CURRENT_DATE() - 1 THEN ACCOUNT_NUMBER END) AS SALES_YDAY,
                COUNT(DISTINCT CASE WHEN TRANSACTION_DATE >= DATE_TRUNC('month', CURRENT_DATE()) THEN ACCOUNT_NUMBER END) AS SALES_MTD,
                COUNT(DISTINCT CASE WHEN TRANSACTION_DATE >= CURRENT_DATE() - 30 THEN ACCOUNT_NUMBER END) AS SALES_L30,
                COUNT(DISTINCT CASE WHEN TRANSACTION_DATE >= CURRENT_DATE() - 7 THEN ACCOUNT_NUMBER END) AS SALES_L7,
                SUM(CASE WHEN FIRST_RECURRING = 'Y' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) AS FTC_PCT
            FROM {APP_SUBS_TABLE}
        """)
        df.columns = [c.upper() for c in df.columns]
        return df.iloc[0] if not df.empty else {}

    @st.cache_data(ttl=1800, show_spinner=False)
    def _load_monthly():
        df = run_query(f"""
            SELECT DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START, COUNT(DISTINCT ACCOUNT_NUMBER) AS SALES
            FROM {APP_SUBS_TABLE}
            WHERE TRANSACTION_DATE >= DATEADD(month, -13, CURRENT_DATE())
            GROUP BY 1 ORDER BY 1
        """)
        df.columns = [c.upper() for c in df.columns]
        return df

    @st.cache_data(ttl=1800, show_spinner=False)
    def _load_daily():
        df = run_query(f"""
            SELECT TRANSACTION_DATE AS DT, COUNT(DISTINCT ACCOUNT_NUMBER) AS SALES
            FROM {APP_SUBS_TABLE}
            WHERE TRANSACTION_DATE >= CURRENT_DATE() - 30
            GROUP BY 1 ORDER BY 1
        """)
        df.columns = [c.upper() for c in df.columns]
        return df

    @st.cache_data(ttl=1800, show_spinner=False)
    def _load_deal_breakdown(days_back: int):
        df = run_query(f"""
            SELECT COALESCE(DESCRIPTION, 'Unknown') AS DEALDESCRIPTION, COUNT(*) AS SALES
            FROM {APP_SUBS_TABLE}
            WHERE TRANSACTION_DATE >= CURRENT_DATE() - {days_back}
            GROUP BY 1 ORDER BY 2 DESC
            LIMIT 15
        """)
        df.columns = [c.upper() for c in df.columns]
        return df

    kpis = _load_kpis()
    monthly = _load_monthly()
    daily = _load_daily()
    deals_yday = _load_deal_breakdown(1)
    deals_l30 = _load_deal_breakdown(30)

    def _pct(v):
        try:
            f = float(v)
            return f"{f * 100:.2f}%" if f == f else "—"
        except (TypeError, ValueError):
            return "—"

    k1, k2, k3 = st.columns(3)
    k1.metric("Active Registered App Users", f"{int(kpis.get('ACTIVE_USERS') or 0):,}")
    k2.metric("Book Size", f"{int(kpis.get('BOOK_SIZE') or 0):,}")
    k3.metric("FTC %", _pct(kpis.get("FTC_PCT")))

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    def _base(title=""):
        return dict(
            title=dict(text=title, font=dict(color=ZERO_WHITE, size=13), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=10), margin=dict(l=8, r=8, t=32, b=8), height=260,
            xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=9, color="#888")),
            yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
        )

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        if not monthly.empty:
            monthly["MONTH_START"] = pd.to_datetime(monthly["MONTH_START"])
            fig = go.Figure(go.Scatter(
                x=monthly["MONTH_START"].dt.strftime("%b '%y").tolist(), y=monthly["SALES"].tolist(),
                mode="lines+markers", line=dict(color=HYPERMINT, width=2), marker=dict(size=4),
            ))
            fig.update_layout(**_base("Monthly trend of new sales from app"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            placeholder_chart("Monthly trend of new sales from app", "No sales in window", height=260)
    with c2:
        if not daily.empty:
            daily["DT"] = pd.to_datetime(daily["DT"])
            fig2 = go.Figure(go.Scatter(
                x=daily["DT"].dt.strftime("%d %b").tolist(), y=daily["SALES"].tolist(),
                mode="lines+markers", line=dict(color=SONIC_BLUE, width=2), marker=dict(size=4),
            ))
            fig2.update_layout(**_base("Daily trend of new sales from app"))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            placeholder_chart("Daily trend of new sales from app", "No sales in last 30 days", height=260)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    if not deals_l30.empty:
        fig3 = go.Figure(go.Bar(
            y=deals_l30["DEALDESCRIPTION"].tolist(), x=deals_l30["SALES"].tolist(), orientation="h",
            marker_color=CHART_PALETTE[0], marker_line_width=0,
        ))
        layout3 = _base("Collected book trend via card")
        layout3["height"] = 340
        layout3["yaxis"] = dict(autorange="reversed", showgrid=False)
        layout3["xaxis"] = dict(showgrid=True, gridcolor=BORDER, tickformat=",")
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    else:
        placeholder_chart("Collected book trend via card", "No data in window", height=340)

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    k4, k5, k6, k7 = st.columns(4)
    k4.metric("Sales Yesterday", f"{int(kpis.get('SALES_YDAY') or 0):,}")
    k5.metric("Sales MTD", f"{int(kpis.get('SALES_MTD') or 0):,}")
    k6.metric("Sales L30 Days", f"{int(kpis.get('SALES_L30') or 0):,}")
    l7avg = (float(kpis.get("SALES_L7") or 0) / 7)
    k7.metric("L7 Day Avg", f"{l7avg:,.2f}")

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    t1, t2 = st.columns(2, gap="medium")
    for col, df, label in [(t1, deals_yday, "Sales Yesterday"), (t2, deals_l30, "Sales Last 30 Days")]:
        with col:
            st.markdown(
                f"<h4 style='color:{HYPERMINT}; font-size:13px; margin-bottom:6px;'>{label}</h4>",
                unsafe_allow_html=True,
            )
            if df.empty:
                st.caption("No sales in this window.")
            else:
                rows_html = "".join(
                    f"<tr><td style='padding:4px 8px; color:{ZERO_WHITE}; font-size:12px;'>{r.DEALDESCRIPTION}</td>"
                    f"<td style='padding:4px 8px; color:{ZERO_WHITE}; font-size:12px; text-align:right;'>{r.SALES:,}</td></tr>"
                    for r in df.itertuples()
                )
                st.markdown(
                    f"<table style='width:100%; border-collapse:collapse; background:{SURFACE_1};'>"
                    f"<thead><tr><th style='padding:4px 8px; background:{SURFACE_2}; font-size:10px; "
                    f"text-align:left; color:#555;'>Product</th><th style='padding:4px 8px; background:{SURFACE_2}; "
                    f"font-size:10px; text-align:right; color:#555;'>Sales</th></tr></thead>"
                    f"<tbody>{rows_html}</tbody></table>",
                    unsafe_allow_html=True,
                )


def render_activation_utilisation_grid(groups: list, cols: int = 2):
    """
    Renders a grid of daily-activations(bar) + Active-1%(line, secondary axis)
    combo charts, one per tenant/channel group - matches the real PBI "New SIM
    Activations & Utilisation" pages 1-4.

    groups: list of {"label": str, "where": str}. `where` is a trusted SQL
    fragment (built from fixed tenant/channel names in the calling page, never
    user input) filtering VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS.
    """
    from utils.snowflake_conn import run_query

    @st.cache_data(ttl=1800, show_spinner=False)
    def _load(where_frag: str):
        df = run_query(f"""
            SELECT
                DATE(ACCOUNTCREATEDATE) AS DT,
                COUNT(*) AS ACTIVATIONS,
                SUM(CASE WHEN USAGE_0_30_DAYS = '1' THEN 1 ELSE 0 END)::FLOAT
                    / NULLIF(COUNT(*), 0) AS ACTIVE1_PCT
            FROM {USAGE_TABLE}
            WHERE DATE(ACCOUNTCREATEDATE) >= CURRENT_DATE() - 30
              AND ({where_frag})
            GROUP BY 1 ORDER BY 1
        """)
        df.columns = [c.upper() for c in df.columns]
        return df

    rows = [groups[i:i + cols] for i in range(0, len(groups), cols)]
    for row in rows:
        row_cols = st.columns(len(row), gap="medium")
        for col, group in zip(row_cols, row):
            with col:
                df = _load(group["where"])
                if df.empty:
                    placeholder_chart(group["label"], "No activations in the last 30 days", height=280)
                    continue
                df["DT"] = pd.to_datetime(df["DT"])
                df = df.sort_values("DT")
                x = df["DT"].dt.strftime("%d %b").tolist()
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=x, y=df["ACTIVATIONS"].tolist(), name="Activations",
                    marker_color=SONIC_BLUE, marker_line_width=0, yaxis="y1",
                    hovertemplate="%{x}<br><b>%{y:,} activations</b><extra></extra>",
                ))
                fig.add_trace(go.Scatter(
                    x=x, y=(df["ACTIVE1_PCT"] * 100).round(1).tolist(), name="Active 1 %",
                    mode="lines+markers", line=dict(color=HYPERMINT, width=2),
                    marker=dict(size=4, color=HYPERMINT), yaxis="y2",
                    hovertemplate="%{x}<br><b>Active 1 %%: %{y:.1f}%%</b><extra></extra>",
                ))
                fig.update_layout(
                    title=dict(text=group["label"], font=dict(color=ZERO_WHITE, size=13), x=0),
                    paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
                    font=dict(color="#888", size=10), height=280,
                    margin=dict(l=8, r=8, t=32, b=8),
                    xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=9, color="#888")),
                    yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
                    yaxis2=dict(overlaying="y", side="right", showgrid=False, ticksuffix="%", range=[0, 105]),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def placeholder_card(label: str, source: str):
    st.markdown(
        f"""
        <div style='background:{SURFACE_1}; border:1px dashed {BORDER};
                    border-radius:10px; padding:18px 16px; text-align:center;
                    min-height:90px;'>
            <div style='color:#555; font-size:11px; text-transform:uppercase;
                        letter-spacing:0.08em; margin-bottom:6px;'>{label}</div>
            <div style='color:#444; font-size:22px; font-weight:700;'>—</div>
            <div style='color:#3a3a3a; font-size:10px; margin-top:6px;'>
                Pending: <span style='color:{HIGHVOLT_ORANGE};'>{source}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def placeholder_chart(title: str, source: str, height: int = 300):
    st.markdown(
        f"""
        <div style='background:{SURFACE_1}; border:1px dashed {BORDER};
                    border-radius:10px; padding:24px 20px; height:{height}px;
                    display:flex; flex-direction:column; justify-content:center;
                    align-items:center; text-align:center;'>
            <div style='color:{ZERO_WHITE}; font-size:13px; font-weight:600;
                        margin-bottom:8px;'>{title}</div>
            <div style='color:#555; font-size:12px;'>Chart pending data access</div>
            <div style='color:{HIGHVOLT_ORANGE}; font-size:11px; margin-top:6px;'>
                Source: {source}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def placeholder_page(
    page_title: str,
    badge: str,
    kpis: list[dict],
    chart_rows: list[list[dict]],
    note: str = "",
):
    """
    Render a full placeholder page.

    kpis: list of {"label": str, "source": str}
    chart_rows: list of rows, each row is list of {"title": str, "source": str, "height": int}
    note: optional note shown below KPIs
    """
    inject_css()
    st.page_link("app.py", label="← Back to Menu")
    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
    page_header(page_title, badge=badge)

    if note:
        st.markdown(
            f"<p style='color:#666; font-size:12px; margin-bottom:16px;'>{note}</p>",
            unsafe_allow_html=True,
        )

    # KPI strip
    if kpis:
        cols = st.columns(len(kpis))
        for col, kpi in zip(cols, kpis):
            with col:
                placeholder_card(kpi["label"], kpi["source"])
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    # Chart rows
    for row in chart_rows:
        cols = st.columns(len(row), gap="medium")
        for col, chart in zip(cols, row):
            with col:
                placeholder_chart(
                    chart["title"],
                    chart["source"],
                    height=chart.get("height", 300),
                )
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
