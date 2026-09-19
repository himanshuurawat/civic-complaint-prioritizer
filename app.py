from pathlib import Path
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from pipeline import clean_and_score
from adapters import adapt_bbmp, is_bbmp_dataset

st.set_page_config(page_title="Civic Complaint Prioritizer", page_icon="🏙️", layout="wide")
ROOT = Path(__file__).parent
DEFAULT_DATA = ROOT / "data" / "complaints.csv"


@st.cache_data
def load_and_process(file_bytes: bytes | None = None) -> pd.DataFrame:
    if file_bytes is None:
        return clean_and_score(pd.read_csv(DEFAULT_DATA))
    raw = pd.read_csv(BytesIO(file_bytes))
    if is_bbmp_dataset(raw):
        return clean_and_score(adapt_bbmp(raw))
    return clean_and_score(raw)


st.title("🏙️ Civic Complaint Prioritizer")
st.caption("An explainable action queue for municipal complaint teams. Demo data is synthetic.")

uploaded = st.sidebar.file_uploader("Upload complaint CSV", type="csv")
st.sidebar.caption("BBMP Bengaluru grievance CSVs are detected and converted automatically.")
try:
    data = load_and_process(uploaded.getvalue() if uploaded else None)
except Exception as error:
    st.error(f"Could not process this file: {error}")
    st.stop()

if uploaded:
    st.info("Using your uploaded dataset. BBMP severity is a transparent project estimate because the source does not publish a severity field.")

st.sidebar.header("Filters")
areas = st.sidebar.multiselect("Area", sorted(data.area.unique()), default=sorted(data.area.unique()))
statuses = st.sidebar.multiselect("Status", sorted(data.status.unique()), default=sorted(data.status.unique()))
categories = st.sidebar.multiselect("Category", sorted(data.predicted_category.unique()), default=sorted(data.predicted_category.unique()))
filtered = data[data.area.isin(areas) & data.status.isin(statuses) & data.predicted_category.isin(categories)]

open_items = filtered[filtered.status != "Resolved"]
duplicates_available = filtered.get("duplicate_eligible", pd.Series(True, index=filtered.index)).astype(bool).any()
first, second, third, fourth = st.columns(4)
first.metric("Reports", len(filtered))
second.metric("Open / in progress", len(open_items))
third.metric("Safety signals", int(filtered.safety_signal.sum()))
fourth.metric("Likely duplicates", int((filtered.duplicate_count > 0).sum()) if duplicates_available else "N/A")
if not duplicates_available:
    st.caption("Duplicate detection is unavailable for this source because it does not include original complaint narratives.")

left, right = st.columns(2)
with left:
    category_counts = filtered.predicted_category.value_counts().rename_axis("Category").reset_index(name="Reports")
    st.plotly_chart(px.bar(category_counts, x="Category", y="Reports", color="Category", title="Issues by category"), use_container_width=True)
with right:
    area_counts = filtered.area.value_counts().rename_axis("Area").reset_index(name="Reports")
    st.plotly_chart(px.bar(area_counts, x="Area", y="Reports", color="Reports", title="Reports by area"), use_container_width=True)

st.subheader("Wards needing attention")
st.caption("The 10 wards with the most open or in-progress grievances in the selected data.")
ward_backlog = (
    open_items.groupby("area").size().rename("Open complaints")
    .sort_values(ascending=False).head(10).rename_axis("Ward").reset_index()
)
if ward_backlog.empty:
    st.info("No unresolved complaints match the selected filters.")
else:
    ward_chart = px.bar(
        ward_backlog.sort_values("Open complaints"),
        x="Open complaints",
        y="Ward",
        orientation="h",
        text="Open complaints",
        title="Top 10 unresolved-complaint backlogs",
    )
    ward_chart.update_traces(textposition="outside")
    st.plotly_chart(ward_chart, use_container_width=True)
    ward_backlog.insert(0, "Rank", range(1, len(ward_backlog) + 1))
    st.dataframe(ward_backlog, use_container_width=True, hide_index=True)

st.subheader("Action queue")
st.write("Ranked with a transparent score: severity, repeat reports, safety signals, and time waiting.")
columns = ["complaint_id", "reported_at", "area", "description", "predicted_category", "status", "priority_score", "priority_reason"]

st.subheader("🚨 Top priority complaints")
st.caption("Open and in-progress reports ranked for immediate human review.")
top_priority = filtered[filtered.status != "Resolved"].head(10).copy()
top_priority.insert(0, "rank", range(1, len(top_priority) + 1))
if top_priority.empty:
    st.info("No open complaints match the selected filters.")
else:
    st.dataframe(
        top_priority[["rank", *columns]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "rank": st.column_config.NumberColumn("Priority rank", format="#%d"),
            "reported_at": st.column_config.DatetimeColumn("Reported", format="D MMM YYYY"),
            "priority_score": st.column_config.ProgressColumn("Priority score", min_value=0, max_value=150),
        },
    )

st.subheader("All filtered complaints")
st.dataframe(filtered[columns], use_container_width=True, hide_index=True, column_config={"reported_at": st.column_config.DatetimeColumn("Reported", format="D MMM YYYY")})

st.download_button("Download ranked queue", filtered[columns].to_csv(index=False), "ranked_complaints.csv", "text/csv")
