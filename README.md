# Cashflow Intelligence Lab

A domain-neutral synthetic laboratory for raw transaction normalization, income detection, recurring-cashflow analysis, and model-ready feature engineering.

```text
raw transactions -> normalize -> deduplicate -> classify -> match income cadence -> confidence -> temporal features
```

The project contains no real banks, employers, customers, accounts, or production data.

## Demonstrated capabilities

- synthetic transaction generation with ground truth labels;
- OCR-like text/date/amount corruption;
- normalization and duplicate detection;
- income category detection with reason codes;
- cadence and amount stability features;
- positive-credit and lender-like exclusion controls;
- confidence score and precision/recall metrics;
- rolling windows and cashflow behavior features;
- Markdown/PNG benchmark report;
- FastAPI, Docker, CI, and tests.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
python scripts/run_report.py
uvicorn cashflow.api:app --reload
```

Open [reports/REPORT.md](reports/REPORT.md) for the benchmark analysis and `http://127.0.0.1:8000/docs` for the API.

Open [reports/SCENARIO_REPORT.md](reports/SCENARIO_REPORT.md) for precision/recall/F1, category accuracy, duplicate exposure, and corruption-scenario analysis. Both reports, their PNG charts, and the underlying JSON metrics are committed in this repository and were produced by an actual run of `scripts/run_report.py` with the default seeded configuration — they are not hand-written.

See [docs/architecture.md](docs/architecture.md) for the pipeline design and module boundaries, and [MODEL_CARD.md](MODEL_CARD.md) for scope, data, evaluation numbers, and limitations.

All data is synthetic and intended to demonstrate methodology, not production performance.
