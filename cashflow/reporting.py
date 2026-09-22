from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .reconciliation import reconciliation_metrics


def build_report(
    income_features: pd.DataFrame,
    cashflow_features: pd.DataFrame,
    output_dir: Path = Path("reports"),
    transactions: pd.DataFrame | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    merged = income_features.merge(cashflow_features, on="entity_id")
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    axes[0].hist(merged["total_detected_income"], bins=20, color="#2f6f9f")
    axes[0].set_title("Detected income distribution")
    axes[0].set_xlabel("Detected credits")
    axes[0].set_ylabel("Entities")
    axes[1].scatter(merged["income_amount_cv"], merged["mean_income_confidence"], alpha=0.7, color="#e07a3f")
    axes[1].set_title("Income stability vs confidence")
    axes[1].set_xlabel("Income amount CV")
    axes[1].set_ylabel("Mean confidence")
    axes[2].scatter(merged["duplicate_rate"], merged["income_share_of_credits"], alpha=0.7, color="#4c956c")
    axes[2].set_title("Data quality vs income share")
    axes[2].set_xlabel("Duplicate rate")
    axes[2].set_ylabel("Income share of credits")
    for axis in axes:
        axis.grid(alpha=0.2)
    figure.savefig(output_dir / "cashflow_dashboard.png", dpi=160)
    plt.close(figure)
    summary = merged.select_dtypes(include="number").describe().round(4)
    selected = ["income_events", "total_detected_income", "income_amount_cv", "income_share_of_credits", "duplicate_rate", "credit_debit_ratio"]
    rows = "\n".join(
        f"| {field} | {summary.loc['mean', field]:.4f} | {summary.loc['std', field]:.4f} |"
        for field in selected
    )
    reconciliation_section = ""
    if transactions is not None:
        reconciliation_section = f"## Balance reconciliation\n\n`{reconciliation_metrics(transactions)}`\n\nThe check verifies that previous balance plus credits minus debits matches the reported balance.\n\n"
    (output_dir / "REPORT.md").write_text(f"""# Cashflow Intelligence Report

All transactions are synthetic. This report evaluates normalization, income detection, confidence, recurring cashflow features, duplicate exposure, and balance integrity.

![Cashflow dashboard](cashflow_dashboard.png)

## Methodology

1. Generate synthetic salary, benefit, transfer, refund, purchase, and lender-like transactions.
2. Normalize dates, amounts, descriptions, and duplicate keys.
3. Detect income only when the transaction is a positive credit and matches a category pattern.
4. Exclude lender-like flows from income classification.
5. Aggregate entity-level temporal features.

## Summary statistics

| Feature | Mean | Std |
| --- | ---: | ---: |
{rows}


{reconciliation_section}
## Limitations

The generator is synthetic and does not represent real financial institutions, people, employers, or production performance. A production extension would add audited labels, cadence validation, source-specific parsers, and human-reviewed error analysis.
""", encoding="utf-8")
