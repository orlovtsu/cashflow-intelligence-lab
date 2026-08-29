import pandas as pd


def reconciliation_metrics(transactions: pd.DataFrame, tolerance: float = 0.01) -> dict[str, float]:
    ordered = transactions.sort_values(["entity_id", "date"]).copy()
    previous = ordered.groupby("entity_id")["balance"].shift(1).fillna(500.0)
    expected = previous + ordered["credit"] - ordered["debit"]
    errors = (ordered["balance"] - expected).abs()
    return {
        "rows": int(len(ordered)),
        "pass_rate": float((errors <= tolerance).mean()) if len(ordered) else 1.0,
        "mean_absolute_error": float(errors.mean()) if len(ordered) else 0.0,
        "max_absolute_error": float(errors.max()) if len(ordered) else 0.0,
    }