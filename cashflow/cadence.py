import numpy as np
import pandas as pd


def cadence_features(income_transactions: pd.DataFrame, as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    rows = []
    for entity_id, group in income_transactions.groupby("entity_id", sort=True):
        ordered = group.sort_values("date")
        dates = ordered["date"].dropna().drop_duplicates()
        intervals = np.diff(dates.astype("int64") / 86_400_000_000_000) if len(dates) > 1 else np.array([])
        mean_interval = float(np.mean(intervals)) if len(intervals) else 0.0
        interval_cv = float(np.std(intervals) / mean_interval) if mean_interval else 0.0
        reference_date = as_of if as_of is not None else ordered["date"].max()
        rows.append({
            "entity_id": entity_id,
            "income_events": len(ordered),
            "median_income_interval_days": float(np.median(intervals)) if len(intervals) else 0.0,
            "income_interval_cv": interval_cv,
            "income_is_regular": bool(len(intervals) >= 2 and interval_cv <= 0.35),
            "days_since_income": int((reference_date - ordered["date"].max()).days) if len(ordered) else 0,
        })
    return pd.DataFrame(rows)
