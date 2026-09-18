from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .income import detect_income
from .normalization import normalize_transactions
from .synthetic import SyntheticConfig, generate_transactions

SCENARIOS = ["clean", "description_noise", "missing_dates", "duplicates", "mixed"]


def corrupt_transactions(frame: pd.DataFrame, seed: int, scenario: str, rate: float = 0.18) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    result = frame.copy()
    if scenario in {"description_noise", "mixed"}:
        mask = rng.random(len(result)) < rate
        result.loc[mask, "description"] = result.loc[mask, "description"].str.replace("PAYROLL", "PAYRO11", regex=False)
    if scenario in {"missing_dates", "mixed"}:
        mask = rng.random(len(result)) < rate / 2
        result.loc[mask, "date"] = pd.NaT
    if scenario in {"duplicates", "mixed"}:
        count = max(1, int(len(result) * rate / 10))
        result = pd.concat([result, result.sample(count, random_state=seed)], ignore_index=True)
    return result


def evaluate_scenario(config: SyntheticConfig, scenario: str) -> dict:
    truth = generate_transactions(config)
    noisy = corrupt_transactions(truth, config.seed + 100, scenario)
    normalized = normalize_transactions(noisy)
    predicted = detect_income(normalized)
    matched = predicted.merge(
        truth[["entity_id", "date", "description", "credit", "category", "is_income"]],
        left_on=["entity_id", "date", "credit"],
        right_on=["entity_id", "date", "credit"],
        how="left",
        suffixes=("_pred", "_true"),
    )
    actual = matched["is_income_true"].eq(True)
    guess = matched["income_detected"].astype(bool)
    tp = int((actual & guess).sum())
    fp = int((~actual & guess).sum())
    fn = int((actual & ~guess).sum())
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    category_match = float(
        (matched.loc[actual & guess, "income_category_detected"] == matched.loc[actual & guess, "category_true"]).mean()
    ) if (actual & guess).any() else 0.0
    return {
        "scenario": scenario,
        "rows": len(noisy),
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / max(precision + recall, 1e-9),
        "category_accuracy": category_match,
        "duplicate_rate": float(normalized["is_duplicate"].mean()),
        "true_income_events": int(actual.sum()),
        "detected_income_events": int(guess.sum()),
    }


def build_scenario_report(config: SyntheticConfig = SyntheticConfig(), output_dir: Path = Path("reports")) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = pd.DataFrame([evaluate_scenario(config, scenario) for scenario in SCENARIOS])
    figure, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
    results.plot.bar(x="scenario", y=["precision", "recall", "f1"], ax=axes[0], color=["#2f6f9f", "#e07a3f", "#4c956c"])
    axes[0].set_ylim(0, 1)
    axes[0].set_title("Income detection quality")
    axes[0].tick_params(axis="x", rotation=25)
    axes[1].bar(results["scenario"], results["duplicate_rate"], color="#c94c4c")
    axes[1].set_ylim(0, max(0.05, results["duplicate_rate"].max() * 1.3))
    axes[1].set_title("Duplicate exposure")
    axes[1].tick_params(axis="x", rotation=25)
    figure.savefig(output_dir / "scenario_matrix.png", dpi=160)
    plt.close(figure)
    rows = "\n".join(
        f"| {row.scenario} | {row.precision:.3f} | {row.recall:.3f} | {row.f1:.3f} | {row.category_accuracy:.3f} | {row.duplicate_rate:.3f} |"
        for row in results.itertuples()
    )
    (output_dir / "SCENARIO_REPORT.md").write_text(f"""# Cashflow Scenario Report

All transactions are synthetic. This report measures income detection under controlled raw-data corruption.

![Scenario matrix](scenario_matrix.png)

| Scenario | Precision | Recall | F1 | Category accuracy | Duplicate rate |
| --- | ---: | ---: | ---: | ---: | ---: |
{rows}

The benchmark separates false income detections from missed income and measures whether detected income is assigned to the correct category.
""", encoding="utf-8")
    results.to_json(output_dir / "scenario_matrix.json", orient="records", indent=2)
    return results


def feature_family_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    families = {
        "income_signal": ["income_detected", "income_confidence", "income_category_detected"],
        "cadence": ["income_events", "median_income_interval_days", "income_interval_cv", "income_is_regular", "days_since_income"],
        "cashflow_behavior": ["total_credits", "total_debits", "credit_debit_ratio", "daily_transaction_density", "min_daily_net_flow", "max_daily_net_flow"],
        "quality_control": ["is_duplicate", "duplicate_rate", "is_positive_credit", "description_normalized", "balance"],
    }
    rows = []
    for family_name, columns in families.items():
        available = len([column for column in columns if column in transactions.columns])
        coverage = available / len(columns) if columns else 1.0
        rows.append({
            "family": family_name,
            "coverage": float(np.clip(coverage, 0.0, 1.0)),
            "available_features": available,
            "expected_features": len(columns),
        })
    return pd.DataFrame(rows)


def confidence_calibration_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions.empty or "income_confidence" not in transactions.columns:
        return pd.DataFrame({
            "bin": ["bin_0", "bin_1", "bin_2"],
            "mean_confidence": [0.0, 0.0, 0.0],
            "observed_rate": [0.0, 0.0, 0.0],
        })

    scores = pd.to_numeric(transactions["income_confidence"], errors="coerce").fillna(0.0)
    if scores.nunique() <= 1:
        bins = pd.Series(["all"] * len(transactions), index=transactions.index)
    else:
        bins = pd.qcut(scores, q=min(5, len(scores.unique())), duplicates="drop")

    summary = (
        transactions.assign(_bin=bins, _score=scores)
        .groupby("_bin", observed=False)
        .agg(
            mean_confidence=("_score", "mean"),
            observed_rate=("income_detected", "mean"),
        )
        .reset_index()
    )
    summary = summary.rename(columns={"_bin": "bin"})
    summary["bin"] = summary["bin"].astype(str)
    summary["mean_confidence"] = summary["mean_confidence"].clip(0.0, 1.0)
    summary["observed_rate"] = summary["observed_rate"].clip(0.0, 1.0)
    if len(summary) < 3:
        fill = pd.DataFrame({
            "bin": [f"bin_{idx}" for idx in range(len(summary), 3)],
            "mean_confidence": [0.0] * max(0, 3 - len(summary)),
            "observed_rate": [0.0] * max(0, 3 - len(summary)),
        })
        summary = pd.concat([summary, fill], ignore_index=True)
    return summary[["bin", "mean_confidence", "observed_rate"]]
