# Model Governance

## Output semantics

The Copenhagen Housing Model exposes three distinct classes of output:

1. **ML crash probability** — a statistical probability in `[0, 1]`, only when produced by the calibrated ML model.
2. **Early Warning Indicator (EWI) score** — a warning signal on the documented EWI scale. It is **not** a probability.
3. **Market Risk Score** — a composite index on a 0–100 scale. It is **not** a probability.

Scenario `ensemble_weight` values are model/analyst weights used to combine scenario forecasts. They are not empirical probabilities unless explicitly estimated and calibrated as such.

## Crash event definition

For evaluation purposes, a 12-month crash event is defined as a real housing-price decline of at least 10% over the subsequent 12 months. Evaluation must use only information that would have been available at the prediction date.

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

The checked-in `config/ews_ml_model.skops` artifact is not a production probability source: it was trained on synthetic feature rows and is deliberately isolated. The dashboard publishes `ml_crash_probability: null` with `ml_model_status: UNAVAILABLE_UNVALIDATED_MODEL` until a point-in-time live-feature, out-of-sample calibration gate passes. The price-only walk-forward benchmark in `scripts/evaluate_event_prediction.py` must not be described as validation of that artifact.

Automated pipeline runs must pass the repository quality gates before publishing a new data snapshot. If an authoritative source fails, the pipeline fails closed and retains the last generated artifact for investigation; it does not merge a fresh DST series with stale market inputs.
