# Architecture

```text
raw transactions -> normalize -> deduplicate -> classify -> match income cadence -> confidence -> temporal features
```

## Responsibility boundaries

The pipeline is split into single-purpose modules that each own one stage:

1. `synthetic.py` generates reproducible synthetic transactions with ground-truth `category` and `is_income` labels, so every downstream stage can be scored against a known-correct answer instead of a guess.
2. `normalization.py` parses dates and amounts, builds a normalized description key, and flags duplicate rows on `(entity_id, date, description_normalized, debit, credit)`. It does not classify or interpret transactions — it only makes them comparable.
3. `income.py` applies the rule-based income classifier: a transaction is income only if it is a positive credit whose normalized description matches an employment or benefit pattern, with lender-like credits explicitly excluded. It attaches a category, a stable reason code, and a confidence score.
4. `cadence.py` looks only at the transactions `income.py` already flagged as income and measures how regularly they recur per entity (median interval, interval coefficient of variation, a regularity flag, days since last income).
5. `features.py` aggregates entity-level cashflow behavior (net flow, credit/debit ratio, transaction density, duplicate rate) independent of the income classification, so cashflow behavior features remain available even for entities with no detected income.
6. `reconciliation.py` independently verifies that each entity's running balance is consistent with its own credit/debit history — a sanity check on the synthetic data generator itself, not on the classifier.
7. `evaluation.py` re-runs the whole pipeline under five controlled corruption scenarios (`clean`, `description_noise`, `missing_dates`, `duplicates`, `mixed`) and scores precision, recall, F1, and category accuracy against the synthetic ground truth.
8. `reporting.py` and `scripts/run_report.py` turn the above into a reproducible Markdown/PNG/JSON artifact set under `reports/`.
9. `api.py` exposes a minimal FastAPI benchmark endpoint over the same pipeline.

## Why classification, cadence, and features are separate stages

Income detection (`income.py`), cadence measurement (`cadence.py`), and cashflow feature aggregation (`features.py`) are kept as separate modules with separate outputs rather than one combined function. This means a change to the income-matching rules cannot silently change how cadence or cashflow density is computed, and cashflow behavior features stay available for entities where the classifier detects no income at all — a common real-world case (see Limitations in `MODEL_CARD.md`) that a combined function would make easy to lose track of.

## Why lender-like credits are excluded from income

`income.py` explicitly excludes description patterns that look like lender or short-term credit deposits from the employment/benefit income match, even when they are positive credits. Without this guard, a credit-line disbursement would be indistinguishable from a paycheck to a naive positive-credit filter. This is the same "explicit exclusion over implicit inference" pattern used by the sibling `open-decisioning-lab` repo's policy layer: the classifier does not try to be clever about ambiguous credits, it treats them as not-income by default.

## Why confidence and reason codes are attached per row

Every classified transaction carries both a numeric `income_confidence` and a categorical `income_reason` (e.g. `positive_credit_description_cadence`, `positive_credit_benefit_pattern`, `not_income_or_excluded`). This keeps every detection traceable to the specific rule that produced it, which is what `evaluation.py` and `reports/SCENARIO_REPORT.md` rely on to separate false positives, missed income, and category mistakes from each other instead of reporting a single opaque accuracy number.

## Why corruption scenarios are evaluated separately from the clean report

`reports/REPORT.md` describes pipeline behavior on the clean synthetic population. `reports/SCENARIO_REPORT.md` is a separate benchmark that re-generates the same synthetic truth, corrupts it five different ways (`corrupt_transactions` in `evaluation.py`), and re-runs the full pipeline on each corrupted copy. Keeping these as two reports makes it possible to see baseline behavior and degradation-under-corruption independently, rather than mixing them into one number that hides which failure mode is driving a metric change.

## Operational extension points

A production extension of this pipeline would need, at minimum:

- source-specific parsers per bank/data-aggregator feed instead of one synthetic schema;
- audited, human-reviewed income labels instead of synthetic ground truth;
- cadence validation that tolerates real pay-cycle irregularities (raises, bonuses, gig income, multiple employers) rather than a fixed interval-CV threshold;
- confidence calibration validated against real outcomes, not fixed rule-based scores;
- drift monitoring on description patterns as real-world formats change;
- persisted, versioned evaluation history instead of a single report run.
