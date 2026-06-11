import streamlit as st
from utils.scorecard import render_scorecard

st.set_page_config(
    page_title="Mica Scorecard | Telco Retail",
    page_icon="🔧",
    layout="wide",
)

render_scorecard({
    "name": "Mica",
    "where_merge": "(LOWER(TENANT) LIKE '%mica%' OR LOWER(TENANT) LIKE '%greenfields%')",
    "where_usage": "(LOWER(TENANT_NAME) LIKE '%mica%' OR LOWER(TENANT_NAME) LIKE '%greenfields%')",
})
