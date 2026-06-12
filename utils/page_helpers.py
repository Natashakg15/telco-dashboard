"""
Shared helpers for placeholder pages and common layouts.
"""
import streamlit as st
from utils.ci import (
    inject_css, page_header,
    HYPERMINT, HIGHVOLT_ORANGE, SONIC_BLUE,
    SURFACE_1, BORDER, ZERO_WHITE, SURFACE_2,
)


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
