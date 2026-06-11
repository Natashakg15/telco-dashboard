import streamlit as st
from utils.scorecard import render_scorecard

st.set_page_config(
    page_title="Fashion Fusion Scorecard | Telco Retail",
    page_icon="👗",
    layout="wide",
)

render_scorecard({
    "name": "Fashion Fusion",
    "where_merge": "LOWER(TENANT) LIKE '%fashion%'",
    "where_usage": "LOWER(TENANT_NAME) LIKE '%fashion%'",
})
