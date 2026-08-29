import re

import pandas as pd


def normalize_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result["description_normalized"] = result["description"].fillna("").astype(str).str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    for column in ["debit", "credit"]:
        result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0.0)
    result["balance"] = pd.to_numeric(result["balance"], errors="coerce")
    result["is_positive_credit"] = result["credit"] > 0
    result["is_duplicate"] = result.duplicated(["entity_id", "date", "description_normalized", "debit", "credit"], keep="first")
    return result
