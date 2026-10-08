import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Nassau Candy | Profitability Analytics", page_icon="🍫", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("nassau_candy_cleaned.csv", parse_dates=["Order Date", "Ship Date"])
    df["Gross Margin %"] = np.where(df["Sales"] != 0, df["Gross Profit"] / df["Sales"] * 100, np.nan)
    df["Profit per Unit"] = np.where(df["Units"] != 0, df["Gross Profit"] / df["Units"], np.nan)
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    return df

df = load_data()

st.title("Nassau Candy Distributor — Product Line Profitability")
st.caption("Decision dashboard for product margin, cost efficiency, concentration, and risk.")

with st.sidebar:
    st.header("Filters")
    min_d, max_d = df["Order Date"].min().date(), df["Order Date"].max().date()
    date_range = st.date_input("Order date range", (min_d, max_d), min_value=min_d, max_value=max_d)
    divisions = ["All"] + sorted(df["Division"].dropna().unique().tolist())
    division = st.selectbox("Division", divisions)
    margin_threshold = st.slider("Minimum margin threshold (%)", 0, 100, 40, 1)
    product_search = st.text_input("Product search")

f = df.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    f = f[(f["Order Date"].dt.date >= date_range[0]) & (f["Order Date"].dt.date <= date_range[1])]
if division != "All":
    f = f[f["Division"] == division]
if product_search:
    f = f[f["Product Name"].str.contains(product_search, case=False, na=False)]

sales = f["Sales"].sum()
profit = f["Gross Profit"].sum()
cost = f["Cost"].sum()
units = f["Units"].sum()
margin = profit / sales * 100 if sales else 0
ppu = profit / units if units else 0

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Revenue", f"${sales:,.2f}")
c2.metric("Gross Profit", f"${profit:,.2f}")
c3.metric("Gross Margin", f"{margin:.1f}%")
c4.metric("Units", f"{units:,.0f}")
c5.metric("Profit / Unit", f"${ppu:.2f}")

# Data quality warning
ship_days = (f["Ship Date"] - f["Order Date"]).dt.days
if len(f) and ship_days.median() > 365:
    st.warning(
        f"Data-quality flag: median Order-to-Ship gap is {ship_days.median():,.0f} days. "
        "Shipment-delay analysis is therefore excluded from profitability conclusions."
    )

tab1,tab2,tab3,tab4 = st.tabs([
    "Product Profitability","Division Performance","Cost & Margin Diagnostics","Profit Concentration"
])

with tab1:
    st.subheader("Product-level profitability leaderboard")
    p = f.groupby(["Product ID","Product Name"], as_index=False).agg(
        Sales=("Sales","sum"), Cost=("Cost","sum"), Profit=("Gross Profit","sum"),
        Units=("Units","sum"), Orders=("Order ID","nunique")
    )
    p["Margin %"] = p["Profit"]/p["Sales"]*100
    p["Profit / Unit"] = p["Profit"]/p["Units"]
    p["Revenue Contribution %"] = p["Sales"]/p["Sales"].sum()*100
    p["Profit Contribution %"] = p["Profit"]/p["Profit"].sum()*100
    p["Risk"] = np.select(
        [p["Margin %"] < margin_threshold,
         (p["Sales"] >= p["Sales"].median()) & (p["Margin %"] < 50)],
        ["Margin Risk","High-Sales / Low-Margin"], default="Healthy"
    )
    st.dataframe(
        p.sort_values("Profit", ascending=False)[
            ["Product Name","Sales","Profit","Margin %","Profit / Unit",
             "Revenue Contribution %","Profit Contribution %","Risk"]
        ].style.format({
            "Sales":"${:,.2f}","Profit":"${:,.2f}","Margin %":"{:.1f}%",
            "Profit / Unit":"${:.2f}","Revenue Contribution %":"{:.1f}%",
            "Profit Contribution %":"{:.1f}%"
        }), use_container_width=True, hide_index=True
    )
    col1,col2 = st.columns(2)
    with col1:
        fig=px.bar(p.sort_values("Profit",ascending=True), x="Profit", y="Product Name",
                   orientation="h", title="Gross Profit by Product")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig=px.scatter(p, x="Sales", y="Margin %", size="Profit", color="Risk",
                       hover_name="Product Name", title="Sales vs Gross Margin")
        fig.add_hline(y=margin_threshold, line_dash="dash")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Division performance")
    d=f.groupby("Division",as_index=False).agg(
        Sales=("Sales","sum"),Cost=("Cost","sum"),Profit=("Gross Profit","sum"),
        Units=("Units","sum"),Products=("Product ID","nunique")
    )
    d["Margin %"]=d["Profit"]/d["Sales"]*100
    d["Profit / Unit"]=d["Profit"]/d["Units"]
    col1,col2=st.columns(2)
    with col1:
        fig=px.bar(d, x="Division", y=["Sales","Profit"], barmode="group",
                   title="Revenue vs Gross Profit")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        fig=px.box(f, x="Division", y="Gross Margin %", points="all",
                   title="Margin Distribution by Division")
        st.plotly_chart(fig,use_container_width=True)
    st.dataframe(d.style.format({"Sales":"${:,.2f}","Cost":"${:,.2f}","Profit":"${:,.2f}",
                                 "Margin %":"{:.1f}%","Profit / Unit":"${:.2f}"}),
                 use_container_width=True,hide_index=True)

with tab3:
    st.subheader("Cost structure and margin-risk diagnostics")
    p=f.groupby(["Product ID","Product Name"],as_index=False).agg(
        Sales=("Sales","sum"),Cost=("Cost","sum"),Profit=("Gross Profit","sum"),
        Units=("Units","sum"))
    p["Margin %"]=p["Profit"]/p["Sales"]*100
    p["Cost Ratio %"]=p["Cost"]/p["Sales"]*100
    p["Profit / Unit"]=p["Profit"]/p["Units"]
    p["Risk"]=np.select(
        [p["Margin %"] < margin_threshold, p["Margin %"] < 50],
        ["Below Threshold","Margin Risk"], default="Healthy")
    fig=px.scatter(p,x="Sales",y="Cost",size="Profit",color="Margin %",
                   hover_name="Product Name",title="Cost vs Sales by Product")
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(p.sort_values("Margin %")[
        ["Product Name","Sales","Cost","Profit","Margin %","Cost Ratio %","Profit / Unit","Risk"]
    ].style.format({"Sales":"${:,.2f}","Cost":"${:,.2f}","Profit":"${:,.2f}",
                    "Margin %":"{:.1f}%","Cost Ratio %":"{:.1f}%","Profit / Unit":"${:.2f}"}),
                  use_container_width=True,hide_index=True)

with tab4:
    st.subheader("Pareto concentration analysis")
    p=f.groupby("Product Name",as_index=False).agg(Sales=("Sales","sum"),Profit=("Gross Profit","sum"))
    p=p.sort_values("Profit",ascending=False)
    p["Cumulative Profit %"]=p["Profit"].cumsum()/p["Profit"].sum()*100
    p["Cumulative Revenue %"]=p["Sales"].sort_values(ascending=False).cumsum()/p["Sales"].sum()*100
    col1,col2=st.columns(2)
    with col1:
        q=p.sort_values("Profit",ascending=False).copy()
        fig=px.bar(q,x="Product Name",y="Profit",title="Profit Pareto")
        fig.add_scatter(x=q["Product Name"], y=q["Cumulative Profit %"], yaxis="y2",
                        mode="lines+markers", name="Cumulative %")
        fig.update_layout(yaxis2=dict(overlaying="y",side="right",range=[0,105]))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        q=p.sort_values("Sales",ascending=False).copy()
        q["Cumulative Revenue %"]=q["Sales"].cumsum()/q["Sales"].sum()*100
        fig=px.bar(q,x="Product Name",y="Sales",title="Revenue Pareto")
        fig.add_scatter(x=q["Product Name"], y=q["Cumulative Revenue %"], yaxis="y2",
                        mode="lines+markers", name="Cumulative %")
        fig.update_layout(yaxis2=dict(overlaying="y",side="right",range=[0,105]))
        st.plotly_chart(fig,use_container_width=True)
    top_profit=p.sort_values("Profit",ascending=False)
    n80=(top_profit["Profit"].cumsum()/top_profit["Profit"].sum()*100 < 80).sum()+1
    top_rev=q
    n80rev=(top_rev["Cumulative Revenue %"] < 80).sum()+1
    st.info(f"Profit concentration: {n80} products are needed to exceed 80% of profit. "
            f"Revenue concentration: {n80rev} products are needed to exceed 80% of revenue.")

st.divider()
st.caption("Note: Gross Profit is validated as Sales − Cost. Product-level margins are effectively constant over time in this dataset, so margin volatility is not a meaningful differentiator.")
