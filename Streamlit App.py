
from __future__ import annotations
import streamlit as st
import re
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from queries import QUERIES

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
st.set_page_config(page_title="OLA Ride Insights", page_icon="🚖", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
CLEAN_CSV = BASE_DIR / "data" / "ola_rides_clean.csv.gz"
RAW_XLSX = BASE_DIR / "data" / "OLA_DataSet.xlsx"

ACCENT = "#1E7F3A"          # deep green (OLA-inspired, readable on light/dark)
SEQ = ["#1E7F3A", "#4C9F38", "#8BC34A", "#C0CA33", "#F9A825", "#EF6C00", "#6D4C41"]
STATUS_COLORS = {
    "Success": "#1E7F3A",
    "Canceled by Driver": "#D84315",
    "Canceled by Customer": "#F9A825",
    "Driver Not Found": "#78909C",
}
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem;}
      div[data-testid="stMetric"] {
          border: 1px solid rgba(128,128,128,.25); border-radius: 10px;
          padding: 10px 14px;
      }
      div[data-testid="stMetricValue"] {font-size: 1.45rem;}
      .note {font-size: .88rem; opacity: .75;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Data layer
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading ride data...")
def load_data() -> pd.DataFrame:
    if CLEAN_CSV.exists():
        df = pd.read_csv(CLEAN_CSV)
    else:  # fall back to cleaning the raw workbook on the fly
        from data_prep import clean
        df = clean(pd.read_excel(RAW_XLSX, sheet_name="July"))
    df["Booking_DateTime"] = pd.to_datetime(df["Booking_DateTime"])
    df["Ride_Date"] = pd.to_datetime(df["Ride_Date"]).dt.date
    return df


@st.cache_resource(show_spinner="Building SQL engine...")
def get_connection() -> sqlite3.Connection:
    """In-memory SQLite DB holding the full cleaned table `ola_rides`."""
    df = load_data().copy()
    df["Booking_DateTime"] = df["Booking_DateTime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["Ride_Date"] = df["Ride_Date"].astype(str)
    con = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql("ola_rides", con, index=False)
    for col in ["Booking_Status", "Vehicle_Type", "Customer_ID", "Ride_Date"]:
        con.execute(f"CREATE INDEX idx_{col} ON ola_rides({col})")
    return con


@st.cache_data(show_spinner=False)
def run_sql(sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_connection())


def inr(x: float) -> str:
    """Indian-style short currency: ₹3.51 Cr / ₹12.4 L / ₹9,850."""
    if x >= 1e7:
        return f"₹{x/1e7:,.2f} Cr"
    if x >= 1e5:
        return f"₹{x/1e5:,.2f} L"
    return f"₹{x:,.0f}"


def show(fig, height: int = 380):
    fig.for_each_xaxis(lambda a: a.update(title_text="Rides") if a.title.text == "count" else None)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=50, b=10),
                      legend_title_text="", hoverlabel=dict(namelength=-1))
    st.plotly_chart(fig, width="stretch")


df_all = load_data()

# ----------------------------------------------------------------------------
# Sidebar: navigation + filters
# ----------------------------------------------------------------------------
st.sidebar.title("🚖 OLA Ride Insights")
page = st.sidebar.radio(
    "Go to",
    ["🏠 Overview", "📈 Overall", "🚗 Vehicle Type", "💰 Revenue",
     "❌ Cancellation", "⭐ Ratings", "🧮 SQL Queries", "📊 Power BI Dashboard",
     "🔍 Insights & Anomalies", "🗂️ Data Explorer"],
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
min_d, max_d = df_all["Ride_Date"].min(), df_all["Ride_Date"].max()
date_sel = st.sidebar.date_input("Date range", (min_d, max_d),
                                 min_value=min_d, max_value=max_d)
veh_opts = sorted(df_all["Vehicle_Type"].unique())
veh_sel = st.sidebar.multiselect("Vehicle type", veh_opts, default=veh_opts)
status_opts = list(STATUS_COLORS)
status_sel = st.sidebar.multiselect("Booking status", status_opts, default=status_opts)
pay_opts = sorted(df_all["Payment_Method"].dropna().unique())
pay_sel = st.sidebar.multiselect("Payment method (successful rides)", pay_opts,
                                 default=pay_opts)
loc_sel = st.sidebar.multiselect("Pickup location (blank = all)",
                                 sorted(df_all["Pickup_Location"].unique()))

if isinstance(date_sel, tuple) and len(date_sel) == 2:
    d_from, d_to = date_sel
else:  # user is mid-selection
    d_from, d_to = min_d, max_d

mask = (
    df_all["Ride_Date"].between(d_from, d_to)
    & df_all["Vehicle_Type"].isin(veh_sel)
    & df_all["Booking_Status"].isin(status_sel)
    & (df_all["Payment_Method"].isin(pay_sel) | df_all["Payment_Method"].isna())
)
if loc_sel:
    mask &= df_all["Pickup_Location"].isin(loc_sel)
df = df_all[mask]
succ = df[df["Booking_Status"] == "Success"]

st.sidebar.caption(f"Showing **{len(df):,}** of {len(df_all):,} bookings")
st.sidebar.caption("Filters apply to dashboard pages. SQL page queries the full table.")

if df.empty and page not in ("🧮 SQL Queries", "📊 Power BI Dashboard"):
    st.warning("No rows match the current filters. Widen the selection in the sidebar.")
    st.stop()


# ----------------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------------
def kpi_row(data: pd.DataFrame) -> None:
    s = data[data["Booking_Status"] == "Success"]
    total = len(data)
    c = st.columns(4)
    c[0].metric("Total bookings", f"{total:,}")
    c[1].metric("Success rate", f"{len(s)/total:.1%}" if total else "–")
    c[2].metric("Revenue (successful)", inr(s["Booking_Value"].sum()))
    c[3].metric("Avg fare / ride", inr(s["Booking_Value"].mean()) if len(s) else "–")
    c = st.columns(4)
    canc = data["Cancelled_By"].ne("Not Cancelled").sum()
    c[0].metric("Cancellation rate", f"{canc/total:.1%}" if total else "–")
    c[1].metric("Avg ride distance", f"{s['Ride_Distance'].mean():.1f} km" if len(s) else "–")
    c[2].metric("Avg driver rating", f"{s['Driver_Ratings'].mean():.2f} ★" if len(s) else "–")
    c[3].metric("Avg customer rating", f"{s['Customer_Rating'].mean():.2f} ★" if len(s) else "–")


if page == "🏠 Overview":
    st.title("OLA Ride Insights — Bengaluru, July 2024")
    st.markdown(
        "Interactive analysis of **103K OLA bookings**: demand patterns, revenue, "
        "cancellations and ratings. Use the sidebar to filter every chart."
    )
    kpi_row(df)
    st.markdown("### Snapshot")
    a, b = st.columns([3, 2])
    with a:
        daily = df.groupby("Ride_Date").size().reset_index(name="Rides")
        show(px.area(daily, x="Ride_Date", y="Rides", title="Daily ride volume",
                     color_discrete_sequence=[ACCENT]), 320)
    with b:
        stat = df["Booking_Status"].value_counts().reset_index()
        show(px.pie(stat, names="Booking_Status", values="count", hole=.55,
                    title="Booking status", color="Booking_Status",
                    color_discrete_map=STATUS_COLORS), 320)
    st.markdown("**Pages:** Overall · Vehicle Type · Revenue · Cancellation · Ratings "
                "(Power BI view segregation), plus SQL answers, Power BI embed, "
                "anomaly detection and a searchable data explorer.")

elif page == "📈 Overall":
    st.title("Overall")
    kpi_row(df)
    gran = st.radio("Ride volume granularity", ["Daily", "Hourly", "Day of week"],
                    horizontal=True)
    if gran == "Daily":
        vol = (df.groupby(["Ride_Date", "Booking_Status"]).size()
               .reset_index(name="Rides"))
        fig = px.line(vol, x="Ride_Date", y="Rides", color="Booking_Status",
                      color_discrete_map=STATUS_COLORS, markers=True,
                      title="1. Ride volume over time")
    elif gran == "Hourly":
        vol = df.groupby("Ride_Hour").size().reset_index(name="Rides")
        fig = px.bar(vol, x="Ride_Hour", y="Rides", title="1. Ride volume by hour of day",
                     color_discrete_sequence=[ACCENT])
        fig.update_xaxes(dtick=1)
    else:
        # average per calendar day avoids bias from 5 Mon/Tue/Wed in July 2024
        per_day = df.groupby(["Ride_Date", "Day_Name"]).size().reset_index(name="Rides")
        vol = (per_day.groupby("Day_Name")["Rides"].mean().reindex(DAY_ORDER)
               .round(0).reset_index())
        fig = px.bar(vol, x="Day_Name", y="Rides",
                     title="1. Average rides per day, by weekday",
                     color_discrete_sequence=[ACCENT])
    show(fig, 420)

    stat = df["Booking_Status"].value_counts().reset_index()
    stat["Share"] = (stat["count"] / stat["count"].sum() * 100).round(1)
    a, b = st.columns([2, 3])
    with a:
        show(px.pie(stat, names="Booking_Status", values="count", hole=.5,
                    title="2. Booking status breakdown", color="Booking_Status",
                    color_discrete_map=STATUS_COLORS), 400)
    with b:
        st.markdown("#### Status table")
        st.dataframe(stat.rename(columns={"count": "Bookings", "Share": "Share %"}),
                     hide_index=True, width="stretch")
        lost = df.loc[df["Booking_Status"] != "Success", "Booking_Value"].sum()
        st.info(f"Booking value of rides that did **not** happen: **{inr(lost)}** "
                "— the size of the prize for reducing cancellations.")

elif page == "🚗 Vehicle Type":
    st.title("Vehicle Type")
    vt = (succ.groupby("Vehicle_Type")
          .agg(Rides=("Booking_ID", "count"), Total_Distance=("Ride_Distance", "sum"),
               Avg_Distance=("Ride_Distance", "mean"), Revenue=("Booking_Value", "sum"),
               Avg_Driver_Rating=("Driver_Ratings", "mean"),
               Avg_Customer_Rating=("Customer_Rating", "mean"))
          .round(2).reset_index())
    icons = df_all.drop_duplicates("Vehicle_Type").set_index("Vehicle_Type")["Vehicle_Image_URL"]

    cols = st.columns(len(vt) or 1)
    for col, (_, r) in zip(cols, vt.sort_values("Revenue", ascending=False).iterrows()):
        with col:
            st.image(icons.get(r["Vehicle_Type"]), width=48)
            st.markdown(f"**{r['Vehicle_Type']}**")
            st.caption(f"{int(r['Rides']):,} rides · {inr(r['Revenue'])}")

    top5 = vt.nlargest(5, "Total_Distance")
    show(px.bar(top5.sort_values("Total_Distance"), x="Total_Distance", y="Vehicle_Type",
                orientation="h", text_auto=",.0f",
                title="3. Top 5 vehicle types by total ride distance (km)",
                color_discrete_sequence=[ACCENT]), 380)
    a, b = st.columns(2)
    with a:
        show(px.bar(vt.sort_values("Avg_Distance"), x="Avg_Distance", y="Vehicle_Type",
                    orientation="h", text_auto=".1f",
                    title="Average distance per successful ride (km)",
                    color_discrete_sequence=["#4C9F38"]))
    with b:
        show(px.bar(vt.sort_values("Revenue"), x="Revenue", y="Vehicle_Type",
                    orientation="h", text_auto=".3s", title="Revenue by vehicle type (₹)",
                    color_discrete_sequence=["#8BC34A"]))
    st.dataframe(vt, hide_index=True, width="stretch")

elif page == "💰 Revenue":
    st.title("Revenue")
    c = st.columns(3)
    c[0].metric("Revenue", inr(succ["Booking_Value"].sum()))
    c[1].metric("Paying rides", f"{len(succ):,}")
    c[2].metric("Median fare / km", f"₹{succ['Fare_per_KM'].median():.1f}")

    pay = (succ.groupby("Payment_Method")["Booking_Value"].agg(["sum", "count"])
           .reset_index().rename(columns={"sum": "Revenue", "count": "Rides"})
           .sort_values("Revenue"))
    a, b = st.columns(2)
    with a:
        show(px.bar(pay, x="Revenue", y="Payment_Method", orientation="h",
                    text_auto=".3s", title="6. Revenue by payment method (₹)",
                    color_discrete_sequence=[ACCENT]))
    with b:
        top_c = (succ.groupby("Customer_ID")["Booking_Value"].sum()
                 .nlargest(5).reset_index().sort_values("Booking_Value"))
        show(px.bar(top_c, x="Booking_Value", y="Customer_ID", orientation="h",
                    text_auto=",", title="7. Top 5 customers by total booking value (₹)",
                    color_discrete_sequence=["#4C9F38"]))

    mode = st.radio("Ride distance per day", ["Total km per day", "Distribution (box)"],
                    horizontal=True)
    if mode == "Total km per day":
        dist = succ.groupby("Ride_Date")["Ride_Distance"].sum().reset_index()
        fig = px.bar(dist, x="Ride_Date", y="Ride_Distance",
                     title="8. Ride distance per day (km)",
                     color_discrete_sequence=[ACCENT])
    else:
        fig = px.box(succ, x="Day_of_Month", y="Ride_Distance",
                     title="8. Ride distance distribution per day of month",
                     color_discrete_sequence=[ACCENT])
    show(fig, 420)

    rev_day = succ.groupby("Ride_Date")["Booking_Value"].sum().reset_index()
    show(px.line(rev_day, x="Ride_Date", y="Booking_Value", markers=True,
                 title="Daily revenue trend (₹)", color_discrete_sequence=["#EF6C00"]), 340)

elif page == "❌ Cancellation":
    st.title("Cancellation")
    total = len(df)
    c = st.columns(4)
    n_cust = (df["Cancelled_By"] == "Customer").sum()
    n_drv = (df["Cancelled_By"] == "Driver").sum()
    n_nf = (df["Booking_Status"] == "Driver Not Found").sum()
    n_inc = (df["Incomplete_Rides"] == "Yes").sum()
    c[0].metric(f"Cancelled by customer · {n_cust/total:.1%}", f"{n_cust:,}")
    c[1].metric(f"Cancelled by driver · {n_drv/total:.1%}", f"{n_drv:,}")
    c[2].metric(f"Driver not found · {n_nf/total:.1%}", f"{n_nf:,}")
    c[3].metric("Incomplete rides (started, not finished)", f"{n_inc:,}")

    a, b = st.columns(2)
    with a:
        cr = df["Canceled_Rides_by_Customer"].value_counts().reset_index()
        show(px.bar(cr.sort_values("count"), x="count", y="Canceled_Rides_by_Customer",
                    orientation="h", text_auto=",",
                    title="5a. Cancelled ride reasons — Customer",
                    color_discrete_sequence=["#F9A825"]).update_yaxes(title=""))
    with b:
        dr = df["Canceled_Rides_by_Driver"].value_counts().reset_index()
        show(px.bar(dr.sort_values("count"), x="count", y="Canceled_Rides_by_Driver",
                    orientation="h", text_auto=",",
                    title="5b. Cancelled ride reasons — Driver",
                    color_discrete_sequence=["#D84315"]).update_yaxes(title=""))

    a, b = st.columns(2)
    with a:
        ir = df["Incomplete_Rides_Reason"].value_counts().reset_index()
        show(px.pie(ir, names="Incomplete_Rides_Reason", values="count", hole=.5,
                    title="Incomplete ride reasons",
                    color_discrete_sequence=["#6D4C41", "#EF6C00", "#78909C"]))
    with b:
        rate = (df.assign(Cancelled=df["Cancelled_By"].ne("Not Cancelled"))
                .groupby("Ride_Hour")["Cancelled"].mean().mul(100).round(1).reset_index())
        fig = px.line(rate, x="Ride_Hour", y="Cancelled", markers=True,
                      title="Cancellation rate by hour (%)",
                      labels={"Cancelled": "Cancelled %", "Ride_Hour": "Hour"},
                      color_discrete_sequence=["#D84315"])
        fig.update_xaxes(dtick=2).update_yaxes(range=[0, rate["Cancelled"].max() * 1.25])
        show(fig)

elif page == "⭐ Ratings":
    st.title("Ratings")
    c = st.columns(2)
    c[0].metric("Avg driver rating", f"{succ['Driver_Ratings'].mean():.2f} ★")
    c[1].metric("Avg customer rating", f"{succ['Customer_Rating'].mean():.2f} ★")
    a, b = st.columns(2)
    with a:
        show(px.histogram(succ, x="Driver_Ratings", nbins=21,
                          title="9. Driver ratings distribution",
                          color_discrete_sequence=[ACCENT]))
    with b:
        show(px.histogram(succ, x="Customer_Rating", nbins=21,
                          title="Customer ratings distribution",
                          color_discrete_sequence=["#F9A825"]))

    vr = (succ.groupby("Vehicle_Type")[["Driver_Ratings", "Customer_Rating"]].mean()
          .round(2).reset_index())
    long = vr.melt(id_vars="Vehicle_Type", var_name="Rating", value_name="Average")
    show(px.bar(long, x="Vehicle_Type", y="Average", color="Rating", barmode="group",
                text_auto=".2f", range_y=[3.5, 4.2],
                title="4 & 10. Customer vs driver ratings by vehicle type",
                color_discrete_map={"Driver_Ratings": ACCENT,
                                    "Customer_Rating": "#F9A825"}), 420)
    sample = succ.sample(min(4000, len(succ)), random_state=1)
    show(px.density_heatmap(sample, x="Driver_Ratings", y="Customer_Rating", nbinsx=21,
                            nbinsy=21, title="10. Customer vs driver rating (density)",
                            color_continuous_scale="Greens"), 420)

elif page == "🧮 SQL Queries":
    st.title("SQL Queries")
    st.markdown('<p class="note">All queries run live on an in-memory SQLite copy '
                'of the full cleaned table <code>ola_rides</code> (filters not applied). '
                'MySQL versions are in <code>sql/ola_queries.sql</code>.</p>',
                unsafe_allow_html=True)
    q_title = st.selectbox("Pick a question", list(QUERIES))
    q = QUERIES[q_title]
    st.code(q["sql"].strip(), language="sql")
    res = run_sql(q["sql"])
    st.caption(f"{len(res):,} rows · {q['note']}")
    if len(res) == 1 and res.shape[1] <= 3:
        cols = st.columns(res.shape[1])
        for col, name in zip(cols, res.columns):
            val = res.iloc[0][name]
            col.metric(name.replace("_", " "),
                       f"{val:,.0f}" if isinstance(val, (int, float)) and val > 100 else val)
    search = st.text_input("Search within result (any column)", "")
    view = res
    if search:
        hit = res.astype(str).apply(lambda s: s.str.contains(search, case=False, regex=False))
        view = res[hit.any(axis=1)]
    st.dataframe(view.head(5000), hide_index=True, width="stretch")
    if len(view) > 5000:
        st.caption("Showing first 5,000 rows — download for the full result.")
    st.download_button("⬇️ Download result (CSV)", view.to_csv(index=False),
                       file_name=f"{q['view']}.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("Run your own query")
    custom = st.text_area("SELECT statement on table `ola_rides`",
                          "SELECT Vehicle_Type, COUNT(*) AS rides\nFROM ola_rides\n"
                          "GROUP BY Vehicle_Type\nORDER BY rides DESC;", height=130)
    if st.button("Run query", type="primary"):
        if not re.match(r"^\s*(select|with)\b", custom, re.I) or re.search(
                r"\b(insert|update|delete|drop|alter|create|attach|pragma)\b", custom, re.I):
            st.error("Only read-only SELECT / WITH queries are allowed.")
        else:
            try:
                out = pd.read_sql_query(custom, get_connection())
                st.success(f"{len(out):,} rows")
                st.dataframe(out.head(5000), hide_index=True, width="stretch")
            except Exception as e:  # show SQL errors to the user
                st.error(f"SQL error: {e}")

elif page == "📊 Power BI Dashboard":
    st.title("Power BI Dashboard")
    try:
        default_url = st.secrets.get("POWERBI_EMBED_URL", "")
    except Exception:  # no secrets.toml present
        default_url = ""
    url = st.text_input("Power BI 'Publish to web' embed URL", value=default_url,
                        placeholder="https://app.powerbi.com/view?r=...")
    if url.startswith("https://app.powerbi.com/"):
        components.iframe(url, height=720, scrolling=True)
    else:
        st.info(
            "**How to embed your report**\n\n"
            "1. Publish the `.pbix` from Power BI Desktop to your workspace.\n"
            "2. In Power BI Service open the report → **File → Embed report → "
            "Publish to web (public)** → copy the link.\n"
            "3. Paste it above, or add `POWERBI_EMBED_URL = \"...\"` to "
            "`.streamlit/secrets.toml` (or the app's *Secrets* on Streamlit Cloud) "
            "so it loads automatically."
        )

elif page == "🔍 Insights & Anomalies":
    st.title("Insights & Anomalies")
    st.subheader("Peak demand — hour × weekday")
    per = (df.groupby(["Ride_Date", "Day_Name", "Ride_Hour"]).size()
           .groupby(["Day_Name", "Ride_Hour"]).mean().reset_index(name="Avg rides"))
    heat = per.pivot(index="Day_Name", columns="Ride_Hour", values="Avg rides").reindex(DAY_ORDER)
    show(px.imshow(heat, aspect="auto", color_continuous_scale="Greens",
                   labels=dict(x="Hour of day", y="", color="Avg rides / hour"),
                   title="Average bookings per hour slot (use for driver allocation)"), 380)

    slot = (df.groupby("Time_Slot")
            .agg(Bookings=("Booking_ID", "count"),
                 Success_Rate=("Is_Success", "mean"),
                 Revenue=("Revenue", "sum")).reset_index())
    slot["Success_Rate"] = (slot["Success_Rate"] * 100).round(1)
    st.dataframe(slot, hide_index=True, width="stretch")

    st.subheader("Fare anomalies (possible fraud / data-entry errors)")
    st.markdown('<p class="note">Successful rides whose fare per km is above '
                'Q3 + 3×IQR. Very short trips with very high fares are the first '
                'thing to audit.</p>', unsafe_allow_html=True)
    anom = succ[succ["Is_Fare_Anomaly"] == 1]
    c = st.columns(3)
    c[0].metric(f"Flagged rides · {len(anom)/max(len(succ),1):.1%} of successful",
                f"{len(anom):,}")
    c[1].metric("Value at risk", inr(anom["Booking_Value"].sum()))
    c[2].metric("Same pickup & drop", f"{int(df['Is_Same_Pickup_Drop'].sum()):,}")
    pts = succ.sample(min(6000, len(succ)), random_state=7).assign(
        Flag=lambda d: d["Is_Fare_Anomaly"].map({1: "Flagged", 0: "Normal"}))
    show(px.scatter(pts, x="Ride_Distance", y="Booking_Value", color="Flag",
                    color_discrete_map={"Normal": "#9E9E9E", "Flagged": "#D84315"},
                    opacity=.55, title="Fare vs distance (6,000-ride sample)"), 420)
    st.dataframe(anom.sort_values("Fare_per_KM", ascending=False)
                 [["Booking_ID", "Ride_Date", "Customer_ID", "Vehicle_Type", "Route",
                   "Ride_Distance", "Booking_Value", "Fare_per_KM", "Payment_Method"]]
                 .head(500), hide_index=True, width="stretch")

    st.subheader("Key business takeaways")
    tot = len(df)
    lost = df.loc[df["Booking_Status"] != "Success", "Booking_Value"].sum()
    top_pay = succ.groupby("Payment_Method")["Booking_Value"].sum()
    top_drv_reason = df["Canceled_Rides_by_Driver"].value_counts()
    top_cus_reason = df["Canceled_Rides_by_Customer"].value_counts()
    bullets = [
        f"**{1 - len(succ)/tot:.0%} of bookings never turn into a ride**, leaving "
        f"{inr(lost)} of booking value on the table.",
        f"Drivers cancel **{(df['Cancelled_By']=='Driver').mean():.1%}** of bookings vs "
        f"customers **{(df['Cancelled_By']=='Customer').mean():.1%}** — driver-side "
        "reliability is the biggest lever.",
    ]
    if len(top_drv_reason):
        bullets.append(f"Top driver reason: **{top_drv_reason.index[0]}** "
                       f"({top_drv_reason.iloc[0]:,}) → vehicle-maintenance support / "
                       "driver incentives.")
    if len(top_cus_reason):
        bullets.append(f"Top customer reason: **{top_cus_reason.index[0]}** "
                       f"({top_cus_reason.iloc[0]:,}) → live driver-tracking alerts and "
                       "auto-reassignment.")
    if len(top_pay):
        bullets.append(f"**{top_pay.idxmax()}** brings {top_pay.max()/top_pay.sum():.0%} "
                       "of revenue; nudging UPI adoption cuts cash-handling risk.")
    bullets.append("Demand is spread evenly across hours and weekdays, so driver supply "
                   "should be flat-loaded rather than surge-concentrated.")
    st.markdown("\n".join(f"- {b}" for b in bullets))

elif page == "🗂️ Data Explorer":
    st.title("Data Explorer")
    q = st.text_input("Search Booking ID, Customer ID or location", "")
    view = df
    if q:
        ql = q.strip().lower()
        view = df[df["Booking_ID"].str.lower().str.contains(ql, regex=False)
                  | df["Customer_ID"].str.lower().str.contains(ql, regex=False)
                  | df["Pickup_Location"].str.lower().str.contains(ql, regex=False)
                  | df["Drop_Location"].str.lower().str.contains(ql, regex=False)]
    default_cols = ["Booking_ID", "Booking_DateTime", "Booking_Status", "Customer_ID",
                    "Vehicle_Type", "Pickup_Location", "Drop_Location", "Booking_Value",
                    "Payment_Method", "Ride_Distance", "Driver_Ratings", "Customer_Rating",
                    "Cancellation_Reason"]
    cols = st.multiselect("Columns", list(df.columns), default=default_cols)
    st.caption(f"{len(view):,} rows")
    st.dataframe(view[cols].head(10000), hide_index=True, width="stretch")
    st.download_button("⬇️ Download filtered data (CSV)", view[cols].to_csv(index=False),
                       file_name="ola_filtered.csv", mime="text/csv")

st.sidebar.markdown("---")
st.sidebar.caption("Built with Python · Pandas · SQLite · Plotly · Streamlit") 
