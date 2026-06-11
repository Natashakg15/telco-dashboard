import streamlit as st
from utils.scorecard import render_scorecard

st.set_page_config(
    page_title="Pet Pool & Home Scorecard | Telco Retail",
    page_icon="🐾",
    layout="wide",
)

render_scorecard({
    "name": "Pet Pool & Home",
    "where_merge": "LOWER(TENANT) LIKE '%pet pool%'",
    "where_usage": "LOWER(TENANT_NAME) LIKE '%pet pool%'",
})
