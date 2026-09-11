# Copenhagen Housing Market Model & Dashboard

Copenhagen Housing Model is an experimental early-warning and scenario-analysis system for Copenhagen and Frederiksberg. It combines observed housing/macro data, an Early Warning Indicator (EWI) framework, user-cost calculations and conditional scenario projections.

It is **not** a validated system for stating when a housing crash will occur. The dashboard deliberately separates observed data, heuristic indices, scenario outputs, simulation sensitivity and any future validated ML probability.

## Live architecture

Vercel hosts the dashboard as a static React/Vite application. The scheduled Python pipeline produces `dashboard/public/data/latest_pipeline.json`, which is validated before publication.

If required data is missing, stale or period-misaligned, the UI reports that state explicitly rather than substituting mock values. Python calls through Vite middleware are local-development integration only.

## How to read the outputs

| Output | Meaning | Must not be read as |
| --- | --- | --- |
| Observed market data | Sourced observations with explicit period/freshness | A forecast |
| EWI score | Weighted early-warning index | A percentage probability |
| Downside / Market Risk score | Composite model index on a 0–100 scale | “X% chance of a fall” |
| Scenario projection | Conditional model output under configured assumptions | The one expected future path |
| Scenario weight | Analyst/model aggregation weight | Empirically estimated scenario probability |
| Monte Carlo downside share | Fraction of simulated model runs with downside | Calibrated probability of a real market event |
| P10–P90 simulation range | Spread of simulated outputs | Predictive confidence interval |
| ML event probability | Statistical probability from the point-in-time model | Available before OOS validation passes |

The separate ML probability is currently unavailable until sufficient genuine point-in-time history has accumulated and the out-of-sample validation gate passes.

## User-cost model

The model uses a modified user-cost framework and deliberately separates expected house-price appreciation from the owner-cost formula to avoid circular “buy” signals.

For the configured reference property:

$$UC_{fund} = \left( r \cdot (1 - \tau_r) + \tau_p + \delta + rp \right) \cdot P$$

Where `r` is mortgage financing cost, `τr` the configured blended interest-deduction effect, `τp` property taxation, `δ` maintenance/depreciation and `rp` the modelled risk premium. These are modelling assumptions/components; the resulting value is a modelled owner-cost measure rather than an observed market price.

## Early Warning System

The EWI framework combines nine indicator families including price/wage divergence, inventory, volume/price divergence, price reductions, time-on-market, price/rent, credit conditions, debt-service burden and unemployment.

The configured threshold bands (`NORMAL`, `ELEVATED`, `HIGH`, `CRITICAL`, `EXTREME`) are **index categories**. Their names describe model states, not calibrated probabilities of a future event.

## Data and lineage

Primary pipeline sources include Danmarks Statistik, Finans Danmark/RKR and Boliga where configured in the implementation. For every source, keep these concepts distinct:

- observation period — when the economic activity occurred
- publication time — when the source released it
- retrieval time — when this system fetched it
- freshness/status — whether the published payload is suitable for current dashboard use

A fresh retrieval timestamp is not a fresh underlying observation.

## ML validation

The production ML field stays unavailable until genuine point-in-time features support the configured validation requirements. The pipeline archives live features in `data/ml_feature_snapshots.jsonl`; training must not manufacture historical feature rows.

The crash-event evaluation convention is documented in `docs/model_governance.md`. Synthetic fixtures, deterministic tests and the price-only walk-forward benchmark are useful implementation/model-behavior checks but do not establish predictive validity for the deployed multivariate model.

## Development

```bash
# Main repository checks
RUN_VISUAL_TESTS=0 ./manage.sh test

# Refresh live pipeline data
./manage.sh update

# Local dashboard/dev integration
./manage.sh start

# Focused probability-validation gate
pytest tests/test_crash_probability_validation.py

# Frontend
cd dashboard
npm run lint
npm run build
```

For UI changes, verify the rendered flow when the environment allows it. For model/data changes, run the affected lineage, forecast, EWI, payload and validation tests rather than treating documentation or compilation as model validation.

## Documentation

- [Model governance](docs/model_governance.md) — output semantics, event definition, lineage and ML-validation gate.
- [Current project state](docs/PROJECT_STATE.md) — canonical implementation and present evidence status.
- [Real-price deflator specification](docs/real_price_deflator_specification.md) — real-price event-label design and lag matching.
- [Point-in-time feature archive](data/README.md) — live ML feature-vintage accumulation.
- `architecture/` — theoretical/design material; it is not proof that every proposed mechanism is deployed.
