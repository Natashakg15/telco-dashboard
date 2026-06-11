import streamlit as st
from utils.scorecard import render_scorecard

st.set_page_config(
    page_title="Spar Scorecard | Telco Retail",
    page_icon="🏪",
    layout="wide",
)

render_scorecard({
    "name": "Spar",
    "where_merge": """
        (LOWER(TENANT) LIKE '%spar%' OR LOWER(TENANT) LIKE '%savemor%')
        AND LOWER(TENANT) NOT LIKE '%midas%'
    """,
    "where_usage": """
        (LOWER(TENANT_NAME) LIKE '%spar%' OR LOWER(TENANT_NAME) LIKE '%savemor%')
        AND LOWER(TENANT_NAME) NOT LIKE '%midas%'
    """,
})
