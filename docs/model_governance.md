# Model Governance

## Output semantics

The Copenhagen Housing Model exposes three distinct classes of output:

1. **ML crash probability** — a statistical probability in `[0, 1]`, only when produced by the calibrated ML model.
2. **Early Warning Indicator (EWI) score** — a warning signal on the documented EWI scale. It is **not** a probability.
3. **Market Risk Score** — a composite index on a 0–100 scale. It is **not** a probability.

Scenario `ensemble_weight` values are model/analyst weights used to combine scenario forecasts. They are not empirical probabilities unless explicitly estimated and calibrated as such.

## Crash event definition

For evaluation purposes, a 12-month crash event is currently defined as a nominal DST EJ56 housing-price-index decline of at least 10% over the subsequent four quarters. A real-price label requires a separately versioned deflator series and is not enabled in the current gate. Evaluation must use only information that would have been available at the prediction date. See `docs/real_price_deflator_specification.md` for the formal mathematical definition, CPI (DST PRIS112) lag matching, empirical historical analysis (2007–2009 vs. 2022–2023), and the roadmap for future real-price crash label activation.

## Passive live vintage accumulation lifecycle

The live feature archive `data/ml_feature_snapshots.jsonl` is continuously updated by the daily scheduled pipeline (`scripts/daily_pipeline.py`) running autonomously via GitHub Actions (`.github/workflows/daily_update.yml`).

1. **Daily Cadence:** Daily runs record the current live market indicators with immutable timestamps and authoritative source vintages.
2. **Quarterly Expansion:** As Danmarks Statistik publishes new quarterly EJ56 housing price index values (approx. 4 times per year), the archive accumulates genuine, verified point-in-time training rows without look-ahead leakage.
3. **Conservative Deduplication:** `scripts/train_ews_model.py` selects the earliest recorded vintage per segment and quarter (`_dedupe_earliest_snapshot_per_period`), ensuring that later revisions retrieved after the label horizon cannot corrupt historical evaluation.
4. **Zero Fabrication:** The system never synthesizes past quarters to artificially accelerate validation. ML probability remains `null` with `INSUFFICIENT_HISTORY` until the required 24 labeled rows, 24 OOS predictions, and 3 independent crash episodes are genuinely achieved.

## Multi-agent & Codex interoperability

This repository is designed for full cognitive and operational portability across AI agents (Codex, Antigravity, Claude) and human maintainers:
- **No Chat-Specific State:** All architectural invariants, economic formulas, validation gates, and pipeline commands are self-contained in the repository files.
- **Fail-Closed Verification:** Any agent operating on this codebase must execute `./manage.sh test` and respect the validation gates before staging commits or deploying payloads.

## Data lineage

For each source, distinguish:

- `observation_period`: period the data describes
- `published_at`: source publication timestamp, where available
- `retrieved_at`: timestamp when this system retrieved the data
- `revision`: source revision/version, where available

`retrieved_at` must never be presented as the observation date.

## Production safety

The production dashboard must not silently replace unavailable pipeline data with mock or synthetic data. If the latest payload is unavailable or invalid, the UI must show an explicit unavailable/stale state.

The generated payload uses `schema_version: 1` and must contain all three market segments, all three forecast horizons, all four EWI-1 modes, a live `market_data_status`, and matching DST/forecast `current_period` and `current_index` values. A payload older than 48 hours is stale for dashboard publication, even when its underlying quarterly observation is still the latest available source observation.

The checked-in `config/ews_ml_model.skops` artifact is not a production probability source unless it is accompanied by a `VALIDATION_AVAILABLE` report from `scripts/train_ews_model.py`. The old artifact was trained on synthetic feature rows and is deliberately isolated. The dashboard publishes `ml_crash_probability: null` with `ml_model_status: UNAVAILABLE_UNVALIDATED_MODEL` until the point-in-time live-feature, out-of-sample calibration gate passes.

The live feature archive is `data/ml_feature_snapshots.jsonl`. It is populated by the daily pipeline and must contain all eight model features plus source vintages for every row. Training selects the earliest recorded vintage per segment and observation quarter, rejects snapshots retrieved after the forward-label horizon, derives the 12-month crash label only from subsequent DST EJ56 observations, and evaluates expanding-window predictions. The validation gate requires minimum labelled and walk-forward coverage for every segment, and calibration folds are grouped by quarter so same-period segment rows cannot leak across train and test. Repeated quarters from the same downturn are clustered as one event episode; five overlapping rows from 2008 do not count as five independent crises. The price-only walk-forward benchmark in `scripts/evaluate_event_prediction.py` must not be described as validation of the deployed ML artifact.

Daily collection does not create historical feature history retroactively. A backfill may only use authoritative point-in-time vintages for all eight features. Current Boliga active-listing data is live-only in this repository, so the model remains unavailable until a compliant historical source or archive exists for EWI-4; no synthetic or proxy backfill is permitted.

Automated pipeline runs must pass the repository quality gates before publishing a new data snapshot. If an authoritative source fails, the pipeline fails closed and retains the last generated artifact for investigation; it does not merge a fresh DST series with stale market inputs.
