from fastapi import FastAPI

from .features import build_cashflow_features
from .income import build_income_features, detect_income
from .normalization import normalize_transactions
from .synthetic import SyntheticConfig, generate_transactions

app = FastAPI(title="Cashflow Intelligence Lab", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/benchmark")
def benchmark() -> dict:
    normalized = normalize_transactions(generate_transactions(SyntheticConfig()))
    enriched = detect_income(normalized)
    return {
        "transactions": len(enriched),
        "detected_income_events": int(enriched["income_detected"].sum()),
        "income_features": len(build_income_features(enriched)),
        "cashflow_features": len(build_cashflow_features(enriched)),
    }
