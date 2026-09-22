# Model Card

## Scope

This project is a synthetic transaction-normalization and income-detection pipeline, not a risk or decisioning model. It ingests raw bank-transaction-like rows, normalizes and deduplicates them, applies a rule-based income classifier, matches recurring income cadence, assigns a confidence score, and aggregates entity-level temporal cashflow features. It must not be used to make real decisions about people, income eligibility, underwriting, or employment, and it contains no real banks, employers, customers, accounts, or production data.

## Data

All transactions are generated locally by `cashflow/synthetic.py` from a seeded random generator (`SyntheticConfig`, default seed `42`, 120 synthetic entities, 90 days each). Each row carries a ground-truth `category` (`employment`, `benefit`, `transfer`, `refund`, `lender_like`, `purchase`) and a ground-truth `is_income` label, which lets the evaluation code check the classifier's output against known-correct answers instead of guessing. `cashflow/reporting.py` additionally generates five controlled corruption scenarios on top of the same synthetic truth — `clean`, `description_noise`, `missing_dates`, `duplicates`, and `mixed` — to test the pipeline under degraded raw data.

## Method

Detection is rule-based, not a trained statistical model. `cashflow/income.py` flags a transaction as income only when it is a positive credit whose normalized description matches an employment or benefit pattern, and explicitly excludes lender-like credits (e.g. short-term credit deposits) from being counted as income. Each detected transaction gets a fixed confidence score (0.9 for a matched category, 0.35 for an unmatched positive credit, 0.05 otherwise) and a stable `income_reason` code (`positive_credit_description_cadence`, `positive_credit_benefit_pattern`, `not_income_or_excluded`). `cashflow/cadence.py` then measures the interval between an entity's income events (median interval, coefficient of variation, a boolean `income_is_regular` flag) and `cashflow/features.py` aggregates entity-level cashflow behavior (net flow bounds, credit/debit ratio, transaction density). `cashflow/reconciliation.py` independently checks that each entity's running balance is consistent with its credit/debit history.

## Evaluation

Running `python scripts/run_report.py` with the default seeded configuration (120 entities, 90 days, seed 42) produces `reports/REPORT.md` and `reports/SCENARIO_REPORT.md` from an actual execution of the pipeline. On the clean synthetic population: mean detected income events per entity 7.0, mean total detected income per entity ≈ $11,694, mean income-amount coefficient of variation ≈ 0.16, income share of detected credits 1.00, duplicate rate 0.00, and balance reconciliation passes for all 2,531 transactions (pass rate 1.0, max absolute error ≈ 1.8e-12, i.e. floating-point noise only).

Under the five corruption scenarios in `reports/SCENARIO_REPORT.md`:

| Scenario | Precision | Recall | F1 | Category accuracy | Duplicate rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| clean | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| description_noise | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| missing_dates | 0.907 | 1.000 | 0.951 | 1.000 | 0.000 |
| duplicates | 1.000 | 1.000 | 1.000 | 1.000 | 0.017 |
| mixed | 0.902 | 1.000 | 0.949 | 1.000 | 0.017 |

Recall stays at 1.0 across every scenario because the classifier never fails to flag a transaction whose description pattern is intact; precision drops under `missing_dates` and `mixed` because the join used to score the scenario matches predicted rows back to ground truth on `(entity_id, date, credit)`, and a corrupted/missing date breaks that match, which the evaluation code counts as a false positive rather than as an evaluation artifact. Category accuracy is 1.0 in every scenario: whenever the pipeline does detect income, it never assigns the wrong category. These numbers came from one actual run of `scripts/run_report.py` against the code in this repository; they are not hand-written.

## Limitations

This is not evidence of production performance. The classifier is a small set of hand-written regex patterns over synthetic descriptions ("PAYROLL", "DIRECT DEPOSIT", "BENEFIT", "GOVERNMENT", etc.) that would not generalize to real bank-statement text, real merchant naming conventions, or adversarial description obfuscation beyond the specific corruption modes simulated here. Precision degradation under `missing_dates` and `mixed` is partly a property of the synthetic evaluation harness (which matches on date) rather than purely a property of the classifier, so those numbers should be read as a demonstration of scenario-based benchmarking, not a claim about real-world date-loss robustness. The synthetic generator produces a narrow, well-separated set of transaction categories; real transaction populations are far messier, and a production system would need audited labels, cadence validation against real pay-cycle irregularities (mid-cycle raises, bonuses, gig income, multiple employers), source-specific parsers per data provider, and human-reviewed error analysis before any of these metrics could be treated as reliable.

## Explanations

Every transaction the classifier acts on carries a stable `income_reason` code (`positive_credit_description_cadence`, `positive_credit_benefit_pattern`, or `not_income_or_excluded`) alongside its `income_confidence` score, so a detection or non-detection can always be traced back to the specific rule that produced it. These reason codes explain which rule fired, not a causal claim about the transaction, and a production system would need to validate that the underlying description patterns remain stable as real-world formats drift.
