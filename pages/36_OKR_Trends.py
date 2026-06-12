import streamlit as st
st.set_page_config(page_title="OKR Trends | Telco Retail", page_icon="📈", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "OKR Trends", "Strategy",
    kpis=[
        {"label": "Avg OKR Score", "source": "OKR tracking table"},
        {"label": "Objectives Met QTD", "source": "OKR tracking table"},
        {"label": "Score vs Prior Quarter", "source": "OKR tracking table"},
        {"label": "Key Results Closed", "source": "OKR tracking table"},
    ],
    chart_rows=[
        [
            {"title": "OKR Completion % — Quarterly Trend", "source": "OKR tracking table"},
            {"title": "Average Score by Objective", "source": "OKR tracking table"},
        ],
    ],
    note="OKR trend data requires a dedicated tracking source. Not currently available via MCP.",
)
