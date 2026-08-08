from dataclasses import dataclass

import numpy as np
import pandas as pd

CATEGORIES = ["employment", "benefit", "transfer", "refund", "lender_like", "purchase"]


@dataclass(frozen=True)
class SyntheticConfig:
    seed: int = 42
    entities: int = 120
    days: int = 90


def generate_transactions(config: SyntheticConfig = SyntheticConfig()) -> pd.DataFrame:
    rng = np.random.default_rng(config.seed)
    rows = []
    start = pd.Timestamp("2025-01-01")
    for entity in range(config.entities):
        entity_id = f"entity-{entity:04d}"
        for day in range(config.days):
            date = start + pd.Timedelta(days=day)
            if day in {14, 28, 42, 56, 70, 84}:
                amount = round(float(rng.normal(1850, 90)), 2)
                rows.append({"entity_id": entity_id, "date": date, "description": "PAYROLL DIRECT DEPOSIT", "debit": 0.0, "credit": amount, "category": "employment", "is_income": True})
            if day in {5, 35, 65} and entity % 3 == 0:
                amount = round(float(rng.normal(620, 35)), 2)
                rows.append({"entity_id": entity_id, "date": date, "description": "GOVERNMENT BENEFIT PAYMENT", "debit": 0.0, "credit": amount, "category": "benefit", "is_income": True})
            if rng.random() < 0.16:
                category = rng.choice(["purchase", "transfer", "refund", "lender_like"])
                amount = round(float(rng.uniform(12, 480)), 2)
                credit = amount if category in {"refund", "lender_like"} and rng.random() < 0.25 else 0.0
                debit = 0.0 if credit else amount
                rows.append({"entity_id": entity_id, "date": date, "description": category.upper() + " TRANSACTION", "debit": debit, "credit": credit, "category": category, "is_income": False})
    return pd.DataFrame(rows)
