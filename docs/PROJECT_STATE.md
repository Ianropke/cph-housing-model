# Copenhagen Housing Model — current project state

Last reconciled: 2026-09-11.

The active system is the Python data/model pipeline plus the static React/Vite dashboard. Scheduled pipeline runs produce validated dashboard payloads; production does not depend on the local Python development middleware.

## Evidence status

- EWI and downside/risk scores are model indices, not event probabilities.
- Scenario outputs are conditional on configured assumptions; their weights are model weights.
- Monte Carlo values describe the distribution of simulated model outcomes. Simulation shares and P10–P90 ranges are sensitivity outputs, not calibrated real-world likelihoods.
- The separate ML event-probability field remains unavailable until the point-in-time out-of-sample validation gate is satisfied.
- Deterministic tests and price-only benchmarks verify implementation behavior but do not establish predictive validity.

## Data policy

Observed periods, retrieval timestamps and freshness remain distinct. Required missing data is surfaced explicitly rather than replaced by synthetic values. ML training uses the accumulated point-in-time live feature archive.
