# Telco Retail Dashboard — Pack v1

Spot CI-compliant analytics dashboard for Telco Retail.  
Business Custodian: **Siddeek Rahim**

## Stack
- **Frontend / App:** Streamlit
- **Data:** Snowflake (`UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE`)
- **Charts:** Plotly
- **CI:** Spot Brand Guidelines 2025 (THERMOLINE design system)

## Sections
| Section | Pages |
|---|---|
| Strategy & Book | Exco Scorecard, Spot Connect Book, OKR Scorecard, OKR Trends, Revenue Trends, Voice/Data Usage, Retain Users |
| Sales | Sales Trends, Quality of Sales, SIM Activations & Utilisation, Scorecards, Trading Store Trend, Pipeline & Commissions |
| Subscriptions | Subscriptions, Cohort Analysis |
| Commercial | Cohort Analysis, Wastage, Pargo Collections |
| Recharges | Recharge Qty, Recharge Trend, Revenue Monthly, Revenue Comparisons, Prepaid Projection |
| Financials | Income Statement, Revenue Metrics, Margin Efficiency, Cost of Sale, Opex, Acquisition Cost, Forward/Trailing 12, Value of New Business |

## Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd telco-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure Snowflake credentials
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your Snowflake credentials

# 4. Run
streamlit run app.py
```

## Colours
| Token | Hex | Usage |
|---|---|---|
| Inkcore | `#0e0e0e` | Background |
| Zero White | `#ffffff` | Text |
| HyperMint | `#13f460` | Primary accent |
| Sonic Blue | `#2d40e9` | Secondary |
| UltraViolet | `#52BEC0` | Tertiary |
| HighVolt Orange | `#f44610` | Highlight |
