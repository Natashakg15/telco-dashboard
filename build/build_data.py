"""
Transforms raw Snowflake query dumps (web/build/raw_*.json) into the compact
web/data/sales_trends.json consumed by the static page's client-side JS.

Raw dumps are produced by running the same SQL as pages/01_Sales_Trends.py
via the Spot Snowflake MCP connector and saving the tool result's
"result_set.data" array. Re-run the queries and overwrite raw_*.json to refresh.
"""
import json
import os

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BUILD_DIR), "data")

DEFINED_GROUPS = [
    "Spar Retail", "Build It", "Midas", "Mica", "Fashion Fusion",
    "Progas", "Aheers", "The Unlimited", "Ladysmith Office National",
    "OnAir", "Pet Pool & Home", "Spot Mobile", "Spot Connect App & Digital",
]


def map_tenant_group(name: str) -> str:
    nl = (name or "").lower()
    if "build it" in nl:
        return "Build It"
    if "midas" in nl or "kr motor spares" in nl or "aca auto parts" in nl or "aca autoparts" in nl:
        return "Midas"
    if "mica" in nl or "greenfields hardware" in nl:
        return "Mica"
    if "spargs" in nl or "savemor" in nl or "spar" in nl:
        return "Spar Retail"
    if "fashion" in nl:
        return "Fashion Fusion"
    if "progas" in nl:
        return "Progas"
    if "aheers" in nl:
        return "Aheers"
    if nl == "the unlimited":
        return "The Unlimited"
    if "ladysmith office national" in nl:
        return "Ladysmith Office National"
    if "onair" in nl or "on air" in nl:
        return "OnAir"
    if "pet pool" in nl:
        return "Pet Pool & Home"
    if nl == "spot mobile":
        return "Spot Mobile"
    if "uconnect app" in nl or "uconnect digital" in nl:
        return "Spot Connect App & Digital"
    return "Other Tenants"


def load_raw(name):
    with open(os.path.join(BUILD_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def main():
    daily_raw = load_raw("raw_daily.json")["data"]
    daily = [{"date": d, "activations": int(a)} for d, a in daily_raw]

    group_raw = load_raw("raw_daily_by_group.json")["result_set"]["data"]
    daily_by_group = [{"date": d, "group": g, "activations": int(a)} for d, g, a in group_raw]

    tenant_month_raw = load_raw("raw_tenant_month.json")["data"]
    tenant_month = [
        {"tenant": t, "last_month": int(lm), "this_month": int(tm)}
        for t, lm, tm in tenant_month_raw
    ]
    for row in tenant_month:
        row["group"] = map_tenant_group(row["tenant"])

    snu_raw = load_raw("raw_snu_active1.json")["data"]
    snu_active1 = [
        {"date": d, "sims_never_used": int(snu), "active_1": int(a1)}
        for d, snu, a1 in snu_raw
    ]

    out = {
        "daily": daily,
        "daily_by_group": daily_by_group,
        "tenant_month": tenant_month,
        "snu_active1": snu_active1,
        "defined_groups": DEFINED_GROUPS,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, "01_sales_trends.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_path) / 1024
    print(f"Wrote {out_path} ({size_kb:.1f} KB) — {len(daily)} daily rows, "
          f"{len(daily_by_group)} daily_by_group rows, {len(tenant_month)} tenants, "
          f"{len(snu_active1)} snu_active1 rows")


if __name__ == "__main__":
    main()
