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

Open `reports/REPORT.md` for the benchmark analysis and `http://127.0.0.1:8000/docs` for the API.

Open `reports/SCENARIO_REPORT.md` for precision/recall/F1, category accuracy, duplicate exposure, and corruption-scenario analysis.

All data is synthetic and intended to demonstrate methodology, not production performance.
