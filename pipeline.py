"""Small, testable transformation pipeline for civic complaint data."""

from __future__ import annotations

import re
from datetime import date

import pandas as pd

CATEGORY_KEYWORDS = {
    "Electrical": ["wire", "spark", "electric", "pole", "power"],
    "Water": ["water", "leak", "pipe", "supply", "drain"],
    "Waste": ["garbage", "waste", "bin", "trash", "litter"],
    "Streetlights": ["streetlight", "lamp", "dark", "light"],
    "Roads": ["pothole", "road", "footpath", "crossing", "surface"],
}
SAFETY_KEYWORDS = ["exposed", "spark", "gas leak", "fire", "collapsed", "accident"]
REQUIRED_COLUMNS = {"complaint_id", "reported_at", "area", "description", "severity", "status"}
DUPLICATE_WINDOW_DAYS = 5
# High threshold: a house or pole number can identify a different physical issue.
DUPLICATE_SIMILARITY_THRESHOLD = 0.90


def infer_category(text: str) -> str:
    """Return the first matching category; use Other when text gives no clue."""
    text = str(text).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(word in text for word in keywords):
            return category
    return "Other"


def token_similarity(first: str, second: str) -> float:
    """Compare two descriptions using the overlap of their meaningful words.

    This is deliberately simple and explainable. Later, we can replace it with
    TF-IDF/cosine similarity once the MVP uses a real dataset.
    """
    first_words = set(first.split())
    second_words = set(second.split())
    if not first_words or not second_words:
        return 0.0
    return len(first_words & second_words) / len(first_words | second_words)


def find_duplicate_counts(df: pd.DataFrame) -> pd.Series:
    """Count likely duplicate reports within the same area/category and 5-day window.

    Requiring all three signals prevents old, unrelated reports with similar
    wording from being incorrectly treated as duplicates.
    """
    counts = pd.Series(0, index=df.index, dtype="int64")
    groups = df.groupby(["area", "predicted_category"], sort=False)

    for _, group in groups:
        records = group.sort_values("reported_at")
        for position, (index, row) in enumerate(records.iterrows()):
            candidates = records.iloc[position + 1 :]
            for other_index, other in candidates.iterrows():
                days_apart = (other.reported_at - row.reported_at).days
                if days_apart > DUPLICATE_WINDOW_DAYS:
                    break
                if token_similarity(row.text_key, other.text_key) >= DUPLICATE_SIMILARITY_THRESHOLD:
                    counts.loc[index] += 1
                    counts.loc[other_index] += 1
    return counts


def clean_and_score(raw: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    df = raw.copy()
    df["reported_at"] = pd.to_datetime(df["reported_at"], errors="coerce")
    df["severity"] = pd.to_numeric(df["severity"], errors="coerce").clip(1, 5)
    df["area"] = df["area"].fillna("Unknown").astype(str).str.strip()
    df["description"] = df["description"].fillna("").astype(str).str.strip()
    df = df.dropna(subset=["reported_at", "severity"])
    df = df[df["description"].str.len() >= 5].drop_duplicates(subset=["complaint_id"])

    # Prefer categories supplied by an official source; otherwise use our
    # transparent keyword classifier for free-text citizen reports.
    inferred = df["description"].map(infer_category)
    if "reported_category" in df.columns:
        source_category = df["reported_category"].fillna("").astype(str).str.strip()
        df["predicted_category"] = source_category.where(~source_category.isin(["", "Other"]), inferred)
    else:
        df["predicted_category"] = inferred
    df["text_key"] = (
        df["description"].str.lower()
        .str.replace(r"[^a-z0-9 ]", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    )
    # Only run text-based duplicate detection when the source contains a real
    # complaint narrative. Structured BBMP category labels are not narratives.
    duplicate_eligible = df.get("duplicate_eligible", pd.Series(True, index=df.index)).fillna(True).astype(bool)
    df["duplicate_count"] = 0
    if duplicate_eligible.any():
        df.loc[duplicate_eligible, "duplicate_count"] = find_duplicate_counts(df.loc[duplicate_eligible])
    df["age_days"] = (pd.Timestamp(date.today()) - df["reported_at"].dt.normalize()).dt.days.clip(lower=0)
    text_lower = df["description"].str.lower()
    df["safety_signal"] = text_lower.apply(lambda text: any(word in text for word in SAFETY_KEYWORDS))
    df["priority_score"] = (
        df["severity"] * 12
        + df["duplicate_count"] * 8
        + df["safety_signal"].astype(int) * 25
        + (df["age_days"] / 7).clip(upper=10).round()
    ).astype(int)
    df["priority_reason"] = df.apply(_reason, axis=1)
    return df.sort_values(["priority_score", "reported_at"], ascending=[False, True])


def _reason(row: pd.Series) -> str:
    reasons = [f"severity {int(row.severity)}/5"]
    if row.duplicate_count:
        reasons.append(f"{int(row.duplicate_count)} similar report(s)")
    if row.safety_signal:
        reasons.append("safety keyword")
    if row.age_days >= 7:
        reasons.append(f"open for {int(row.age_days)} days")
    return "; ".join(reasons)
