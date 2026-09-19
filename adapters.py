"""Adapters that convert public city datasets into the project's common schema."""

import pandas as pd

BBMP_COLUMNS = {"Complaint ID", "Category", "Grievance Date", "Ward Name", "Grievance Status"}


def is_bbmp_dataset(df: pd.DataFrame) -> bool:
    return BBMP_COLUMNS.issubset(df.columns)


def _status(value: object) -> str:
    text = str(value).lower()
    if any(word in text for word in ["resolved", "closed", "completed", "disposed"]):
        return "Resolved"
    if any(word in text for word in ["progress", "assigned", "work"]):
        return "In progress"
    return "Open"


def _severity(category: object, sub_category: object) -> int:
    """A transparent estimate because the public source has no severity field."""
    text = f"{category} {sub_category}".lower()
    if any(word in text for word in ["electric", "wire", "fire", "drain", "sewage", "collapse"]):
        return 5
    if any(word in text for word in ["water", "road", "street", "tree"]):
        return 3
    return 2


def adapt_bbmp(df: pd.DataFrame) -> pd.DataFrame:
    """Convert official BBMP grievance data to the project's common schema."""
    sub_category = df.get("Sub Category", pd.Series("", index=df.index)).fillna("").astype(str)
    category = df["Category"].fillna("Other").astype(str)
    return pd.DataFrame(
        {
            "complaint_id": df["Complaint ID"].astype(str),
            "reported_at": df["Grievance Date"],
            "city": "Bengaluru",
            "area": df["Ward Name"].fillna("Unknown ward").astype(str),
            "description": "Category: " + category + ". Sub-category: " + sub_category,
            "reported_category": category,
            "severity": [_severity(cat, sub) for cat, sub in zip(category, sub_category)],
            "status": df["Grievance Status"].map(_status),
            "data_source": "BBMP public grievance data",
            # BBMP does not publish the original citizen narrative. Its
            # category/sub-category text cannot be used to infer duplicates.
            "duplicate_eligible": False,
        }
    )
