import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Workora BI Dashboard", page_icon="📊", layout="wide")

DATA = Path(__file__).parent

@st.cache_data
def load_data():
    traffic = pd.read_csv(DATA / "web_traffic.csv", parse_dates=["Date"])
    churn = pd.read_csv(DATA / "customer_churn.csv")
    market = pd.read_csv(DATA / "regional_market.csv")
    checkout = pd.read_csv(DATA / "checkout_ab_test.csv", parse_dates=["Timestamp"])
    # Clean churn data: remove duplicate CustomerIDs, convert numeric fields, and handle invalid values.
    churn = churn.drop_duplicates(subset=["CustomerID"]).copy()
    for col in ["Age", "TenureMonths", "MonthlyChargesINR", "TotalChargesINR", "SupportTickets", "LatePayments"]:
        churn[col] = pd.to_numeric(churn[col], errors="coerce")
    churn["TotalChargesINR"] = churn["TotalChargesINR"].fillna(churn["MonthlyChargesINR"] * churn["TenureMonths"])
    return traffic, churn, market, checkout

traffic, churn, market, checkout = load_data()

st.title("📊 Workora Business Intelligence Dashboard")
st.caption("Learning dashboard built from synthetic datasets. Figures are illustrative and are not real Workora business results.")

# Sidebar filters
st.sidebar.header("Dashboard Filters")
all_dates = pd.concat([traffic["Date"].dropna(), checkout["Timestamp"].dropna().dt.normalize()])
min_date, max_date = all_dates.min().date(), all_dates.max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date = end_date = pd.Timestamp(date_range)

regions = sorted(set(traffic["Region"].dropna().astype(str)) | set(churn["Region"].dropna().astype(str)))
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
categories = sorted(set(traffic["DeviceCategory"].dropna().astype(str)) | set(churn["SubscriptionType"].dropna().astype(str)))
selected_categories = st.sidebar.multiselect("Category (device or subscription)", categories, default=categories)

# Dataset-specific filtered views. The files do not share a common customer/session key,
# so they are analyzed independently rather than joined into misleading row-level records.
t = traffic[(traffic["Date"] >= start_date) & (traffic["Date"] < end_date + pd.Timedelta(days=1))]
t = t[t["Region"].astype(str).isin(selected_regions) & t["DeviceCategory"].astype(str).isin(selected_categories)]

c = churn[churn["Region"].astype(str).isin(selected_regions) & churn["SubscriptionType"].astype(str).isin(selected_categories)]
o = checkout[(checkout["Timestamp"] >= start_date) & (checkout["Timestamp"] < end_date + pd.Timedelta(days=1))].copy()
o["OrderValueINR"] = pd.to_numeric(o["OrderValueINR"], errors="coerce").fillna(0)
converted = o[o["Converted"].astype(str).str.lower().eq("yes")]

revenue = converted["OrderValueINR"].sum()
active_users = o.loc[o["CheckoutStarted"].astype(str).str.lower().eq("yes"), "VisitorID"].nunique()
churn_rate = (c["Churn"].astype(str).str.lower().eq("yes").mean() * 100) if len(c) else 0
avg_ticket = converted["OrderValueINR"].mean() if len(converted) else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"₹{revenue:,.0f}")
k2.metric("Active Users*", f"{active_users:,}")
k3.metric("Churn Rate", f"{churn_rate:.1f}%")
k4.metric("Avg. Ticket Size", f"₹{avg_ticket:,.0f}")
st.caption("*Active users is defined as unique visitors who started checkout in the selected period. Revenue and ticket size use converted orders only.")

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Revenue over time")
    if len(converted):
        rev = converted.assign(Date=converted["Timestamp"].dt.date).groupby("Date", as_index=False)["OrderValueINR"].sum()
        fig = px.line(rev, x="Date", y="OrderValueINR", markers=True, title="Daily converted order revenue")
        fig.update_layout(xaxis_title="Date", yaxis_title="Revenue (INR)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No converted orders in the selected date range.")
with right:
    st.subheader("Checkout conversion by variant")
    if len(o):
        ab = o.groupby("Variant", as_index=False).agg(Visitors=("VisitorID", "nunique"), Conversions=("Converted", lambda s: s.astype(str).str.lower().eq("yes").sum()))
        ab["Conversion Rate (%)"] = (ab["Conversions"] / ab["Visitors"] * 100).round(2)
        fig = px.bar(ab, x="Variant", y="Conversion Rate (%)", text="Conversion Rate (%)", title="A/B test conversion rate")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No checkout records in the selected date range.")

left, right = st.columns(2)
with left:
    st.subheader("Sessions by device")
    if len(t):
        device = t.groupby("DeviceCategory", as_index=False).agg(Sessions=("SessionID", "nunique"), Registrations=("Registered", lambda s: s.astype(str).str.lower().eq("yes").sum()))
        fig = px.bar(device, x="DeviceCategory", y="Sessions", color="DeviceCategory", title="Website sessions by device")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No web traffic records match the selected filters.")
with right:
    st.subheader("Customer churn by subscription")
    if len(c):
        cc = c.groupby("SubscriptionType", as_index=False).agg(Customers=("CustomerID", "nunique"), Churned=("Churn", lambda s: s.astype(str).str.lower().eq("yes").sum()))
        cc["Churn Rate (%)"] = (cc["Churned"] / cc["Customers"] * 100).round(2)
        fig = px.bar(cc, x="SubscriptionType", y="Churn Rate (%)", color="SubscriptionType", title="Churn rate by subscription")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No customer records match the selected filters.")

st.subheader("Regional market opportunity")
if len(market):
    m = market.copy()
    m["MonthlySearchDemand"] = pd.to_numeric(m["MonthlySearchDemand"], errors="coerce")
    fig = px.scatter_mapbox(
        m, lat="Latitude", lon="Longitude", size="MonthlySearchDemand",
        color="LeadConversionRate", hover_name="City",
        hover_data=["State", "MonthlySearchDemand", "ExistingCompetitors", "EstimatedAcquisitionCostINR"],
        zoom=3, height=430, mapbox_style="open-street-map",
        title="Search demand and lead conversion by location"
    )
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Data notes and assumptions"):
    st.markdown("""
    - All files contain **synthetic learning data**; do not report these values as actual company performance.
    - **Total Revenue:** sum of `OrderValueINR` for checkout records where `Converted = Yes`.
    - **Active Users:** unique visitors with `CheckoutStarted = Yes` in the selected date range (a proxy, because no user-activity table is supplied).
    - **Churn Rate:** share of customers marked `Churn = Yes` in the filtered customer dataset. The churn file has no date column, so date filtering does not apply to churn.
    - **Average Ticket Size:** average order value among converted visitors only.
    - **Cleaning:** duplicate customer IDs are removed; numeric fields are coerced to numbers; unknown total charges are estimated as monthly charges × tenure.
    - **Relationships:** the four CSV files have no shared row-level key, so each source is analyzed separately instead of being joined incorrectly.
    - **Category filter:** applies to device category for web traffic and subscription type for churn.
    """)

st.caption("Built with Streamlit, Pandas, and Plotly • Use the sidebar to explore the dashboard.")
