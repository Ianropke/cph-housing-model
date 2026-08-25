# Point-in-time ML feature archive

`ml_feature_snapshots.jsonl` is generated autonomously by `scripts/daily_pipeline.py`.
Each row contains the seven ML-eligible live EWS inputs for one segment, the quarterly
price observation used for the later label, the pipeline timestamp, and the
source vintages used to construct each feature.

EWI-4 (active-listing price-reduction rate) remains a dashboard and EWI
indicator, but is intentionally excluded from the ML feature contract because
the repository has no historical point-in-time Boliga series for it.

## Passive Accumulation Lifecycle & Cadence

1. **Daily Scheduled Execution:** The GitHub Actions workflow (`.github/workflows/daily_update.yml`) runs daily at 03:00 AM UTC.
2. **Idempotent Append:** Daily snapshots are appended to `ml_feature_snapshots.jsonl` with an SHA-256 `snapshot_id` keyed on `(segment, observation_period, snapshot_timestamp)`.
3. **Quarterly Expansion:** As Danmarks Statistik updates table `EJ56` quarterly, new quarterly observations enter the archive with genuine, unrevised live vintages.
4. **Conservative Deduplication:** Daily snapshots are not treated as independent observations. `scripts/train_ews_model.py` selects the earliest recorded vintage per segment and observation quarter (`_dedupe_earliest_snapshot_per_period`), ensuring that no look-ahead revision leakage occurs.
5. **Validation Gate Requirement:** The model is prohibited from publishing any ML crash probability until the archive contains:
   - $\ge 24$ labelled historical observations
   - $\ge 24$ walk-forward out-of-sample predictions
   - $\ge 3$ independent crash episodes
   - Minimum coverage for each of the 3 market segments (`copenhagen_apartments`, `copenhagen_houses`, `frederiksberg_apartments`)

Until these conditions are genuinely met through empirical accumulation, the validation status remains `INSUFFICIENT_HISTORY` and the published probability remains `null`.

## Prohibition of Synthetic Backfill

The archive is not a historical backfill. Daily collection can only add the
currently published quarter. A historical backfill is allowed only when all
seven ML features can be reconstructed from authoritative, point-in-time
sources. Current Boliga active-listing data has no historical series in this
repository, so EWI-4 is not used for ML and cannot be fabricated or silently
proxied.
