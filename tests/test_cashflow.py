from fastapi.testclient import TestClient

from cashflow.api import app
from cashflow.evaluation import (
    SCENARIOS,
    build_scenario_report,
    confidence_calibration_summary,
    evaluate_scenario,
    feature_family_summary,
)
from cashflow.features import build_cashflow_features
from cashflow.income import build_income_features, detect_income
from cashflow.normalization import normalize_transactions
from cashflow.reconciliation import reconciliation_metrics
from cashflow.synthetic import SyntheticConfig, generate_transactions

client = TestClient(app)


def enriched():
    return detect_income(normalize_transactions(generate_transactions(SyntheticConfig(seed=7, entities=20, days=90))))


def test_normalization_is_reproducible_and_deduplicates():
    raw = generate_transactions(SyntheticConfig(seed=7, entities=5, days=30))
    first = normalize_transactions(raw)
    second = normalize_transactions(raw)
    assert first.equals(second)
    assert "description_normalized" in first
    assert first["is_duplicate"].mean() == 0


def test_income_detection_has_positive_credit_guard_and_categories():
    frame = enriched()
    assert frame["income_detected"].any()
    assert set(frame.loc[frame["income_detected"], "income_category_detected"]) <= {"employment", "benefit"}
    assert (frame.loc[frame["income_detected"], "credit"] > 0).all()


def test_feature_engineering_is_finite_and_entity_level():
    frame = enriched()
    income = build_income_features(frame)
    cashflow = build_cashflow_features(frame)
    assert len(income) == len(cashflow)
    assert income["income_events"].ge(0).all()
    assert cashflow["duplicate_rate"].between(0, 1).all()
    assert income["median_income_interval_days"].ge(0).all()
    assert income["income_interval_cv"].ge(0).all()


def test_running_balance_reconciles():
    frame = normalize_transactions(generate_transactions(SyntheticConfig(seed=11, entities=5, days=30)))
    metrics = reconciliation_metrics(frame)
    assert metrics["pass_rate"] == 1.0
    assert metrics["max_absolute_error"] <= 0.01


def test_api_benchmark():
    response = client.get("/benchmark")
    assert response.status_code == 200
    assert response.json()["detected_income_events"] > 0


def test_income_metrics_are_bounded():
    result = evaluate_scenario(SyntheticConfig(seed=4, entities=10, days=60), "mixed")
    assert result["scenario"] == "mixed"
    assert 0 <= result["precision"] <= 1
    assert 0 <= result["recall"] <= 1
    assert 0 <= result["f1"] <= 1


def test_scenario_report_covers_all_corruption_modes(tmp_path):
    result = build_scenario_report(SyntheticConfig(seed=5, entities=10, days=60), tmp_path)
    assert set(result["scenario"]) == set(SCENARIOS)
    assert (tmp_path / "SCENARIO_REPORT.md").exists()


def test_feature_family_summary_is_stable_and_explainable():
    frame = detect_income(normalize_transactions(generate_transactions(SyntheticConfig(seed=3, entities=12, days=45))))
    summary = feature_family_summary(frame)
    assert set(summary["family"]) == {"income_signal", "cadence", "cashflow_behavior", "quality_control"}
    assert summary["coverage"].between(0, 1).all()


def test_confidence_calibration_summary_is_bounded():
    frame = detect_income(normalize_transactions(generate_transactions(SyntheticConfig(seed=9, entities=18, days=60))))
    summary = confidence_calibration_summary(frame)
    assert len(summary) >= 3
    assert summary["mean_confidence"].between(0, 1).all()
    assert summary["observed_rate"].between(0, 1).all()
