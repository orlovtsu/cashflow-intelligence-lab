import numpy as np
import pandas as pd


def detect_income(transactions: pd.DataFrame) -> pd.DataFrame:
    result = transactions.copy()
    description = result["description_normalized"]
    result["income_category_detected"] = "none"
    employment = description.str.contains(r"payroll|salary|direct deposit", regex=True)
    benefit = description.str.contains(r"benefit|government", regex=True)
    lender = description.str.contains(r"lender|credit_provider|short_term_credit", regex=True)
    result.loc[employment & result["is_positive_credit"] & ~lender, "income_category_detected"] = "employment"
    result.loc[benefit & result["is_positive_credit"] & ~lender, "income_category_detected"] = "benefit"
    result["income_detected"] = result["income_category_detected"] != "none"
    result["income_reason"] = np.select(
        [result["income_detected"] & (result["income_category_detected"] == "employment"), result["income_detected"] & (result["income_category_detected"] == "benefit")],
        ["positive_credit_description_cadence", "positive_credit_benefit_pattern"],
        default="not_income_or_excluded",
    )
    result["income_confidence"] = np.where(result["income_detected"], 0.9, np.where(result["is_positive_credit"], 0.35, 0.05))
    return result


def build_income_features(transactions: pd.DataFrame) -> pd.DataFrame:
    income = transactions[transactions["income_detected"]].copy()
    grouped = income.groupby("entity_id")
    result = grouped.agg(
        income_events=("income_detected", "sum"),
        total_detected_income=("credit", "sum"),
        mean_income_confidence=("income_confidence", "mean"),
        income_sources=("income_category_detected", "nunique"),
    ).reset_index()
    result["income_amount_cv"] = grouped["credit"].agg(lambda values: float(np.std(values) / np.mean(values)) if np.mean(values) else 0.0).values
    result["income_share_of_credits"] = result["total_detected_income"] / grouped["credit"].sum().reset_index()["credit"].replace(0, np.nan).fillna(1).values
    return result
