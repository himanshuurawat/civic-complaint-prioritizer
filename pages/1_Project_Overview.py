import streamlit as st

st.set_page_config(page_title="Project Overview", page_icon="📘", layout="wide")

st.title("📘 Project Overview")
st.caption("Civic Complaint Prioritizer | A data-science engineering portfolio project")

st.header("The problem")
st.write(
    "Municipal teams receive large numbers of civic grievances, but raw spreadsheets make it hard "
    "to see which wards have the largest unresolved backlog. This project transforms complaint "
    "records into an interactive, explainable action dashboard."
)

first, second, third = st.columns(3)
first.metric("Input", "Complaint CSV")
second.metric("Process", "Clean + standardize")
third.metric("Output", "Actionable ward backlog")

st.header("What the dashboard does")
st.markdown(
    """
- Validates and cleans complaint records before analysis.
- Converts BBMP Bengaluru grievance data into one consistent schema.
- Shows issue categories, ward-level volume, and unresolved backlog.
- Ranks reports through a transparent priority score.
- Lets users filter results and download the ranked queue.
"""
)

st.header("Data source and responsible use")
st.write(
    "The dashboard supports public BBMP Bengaluru grievance CSV files. The source provides "
    "complaint ID, category, sub-category, date, ward, and status. It does not provide the original "
    "citizen complaint narrative or an official severity score."
)
st.warning(
    "Severity for BBMP uploads is a documented project estimate, not an official BBMP value. "
    "Text-based duplicate detection is disabled because the source does not include complaint narratives."
)

st.header("How the priority score works")
st.code("priority = severity × 12 + recent similar reports × 8 + safety signal + age bonus", language="text")
st.write(
    "The rules are visible so an official can understand and override the result. The score supports "
    "human decision-making; it must not make final public-safety decisions automatically."
)

st.header("Technical architecture")
st.code(
    "CSV upload → BBMP adapter → validation/cleaning → priority pipeline → Streamlit dashboard",
    language="text",
)

st.header("Next improvements")
st.markdown(
    """
1. Add compatible datasets from more Indian cities.
2. Use complaint narratives and coordinates, where legally available, for duplicate clustering.
3. Train and evaluate a text-category model against a labeled dataset.
4. Add automated tests and deploy the dashboard.
"""
)
