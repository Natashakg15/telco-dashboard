import streamlit as st
st.set_page_config(page_title="Income Statement | Telco Retail", page_icon="💰", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Income Statement", "Financials",
    kpis=[
        {"label": "Revenue", "source": "GL / Income Statement table"},
        {"label": "Gross Profit", "source": "GL / Income Statement table"},
        {"label": "EBITDA", "source": "GL / Income Statement table"},
        {"label": "Net Profit", "source": "GL / Income Statement table"},
    ],
    chart_rows=[
        [
            {"title": "Revenue vs Gross Profit — Monthly", "source": "GL / Income Statement table"},
            {"title": "P&L Waterfall", "source": "GL / Income Statement table"},
        ],
        [
            {"title": "EBITDA Trend", "source": "GL / Income Statement table"},
            {"title": "Net Profit Margin %", "source": "GL / Income Statement table"},
        ],
    ],
    note="Income Statement data requires a GL / financial reporting source. Not currently available via MCP.",
)
