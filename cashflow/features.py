import pandas as pd


def build_cashflow_features(transactions: pd.DataFrame) -> pd.DataFrame:
    frame = transactions.sort_values(["entity_id", "date"]).copy()
    frame["net_flow"] = frame["credit"] - frame["debit"]
    grouped = frame.groupby("entity_id")
    result = grouped.agg(
        active_days=("date", "nunique"),
        transaction_count=("date", "size"),
        total_credits=("credit", "sum"),
        total_debits=("debit", "sum"),
        min_daily_net_flow=("net_flow", "min"),
        max_daily_net_flow=("net_flow", "max"),
        duplicate_rate=("is_duplicate", "mean"),
    ).reset_index()
    result["credit_debit_ratio"] = result["total_credits"] / result["total_debits"].replace(0, 1)
    result["daily_transaction_density"] = result["transaction_count"] / result["active_days"].replace(0, 1)
    return result
