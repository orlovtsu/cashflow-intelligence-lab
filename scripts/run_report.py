import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cashflow.evaluation import build_scenario_report
from cashflow.features import build_cashflow_features
from cashflow.income import build_income_features, detect_income
from cashflow.normalization import normalize_transactions
from cashflow.reporting import build_report
from cashflow.synthetic import SyntheticConfig, generate_transactions


def main():
    transactions = normalize_transactions(generate_transactions(SyntheticConfig()))
    enriched = detect_income(transactions)
    build_report(build_income_features(enriched), build_cashflow_features(enriched), transactions=enriched)
    build_scenario_report()
    print("report=reports/REPORT.md")


if __name__ == "__main__":
    main()
