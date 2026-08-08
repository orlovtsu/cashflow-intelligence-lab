from fastapi.testclient import TestClient

from cashflow.api import app
from cashflow.features import build_cashflow_features
from cashflow.income import build_income_features, detect_income
from cashflow.normalization import normalize_transactions
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


def test_api_benchmark():
    response = client.get("/benchmark")
    assert response.status_code == 200
    assert response.json()["detected_income_events"] > 0
