import streamlit as st
st.set_page_config(page_title="Margin Efficiency Metrics | Telco Retail", page_icon="📊", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Margin Efficiency Metrics", "Financials",
    kpis=[
        {"label": "Gross Margin %", "source": "GL / cost of sale table"},
        {"label": "Contribution Margin %", "source": "GL / cost of sale table"},
        {"label": "EBITDA Margin %", "source": "GL / cost of sale table"},
        {"label": "Net Margin %", "source": "GL / cost of sale table"},
    ],
    chart_rows=[
        [
            {"title": "Margin % Trends (13 months)", "source": "GL / cost of sale table"},
            {"title": "Margin by Product / Channel", "source": "GL / cost of sale table"},
        ],
    ],
    note="Margin metrics require cost-of-sale and GL data. Not currently available via MCP.",
)
