# 📄 Københavns Boligmarkedsmodel — Architectural & Model Design Specification (v3.3 review baseline)

> **Formål:** Dette dokument udgør den samlede arkitektur-, model- og testplanspecifikation for *Copenhagen Housing Market Forecasting & Early Warning Ecosystem*. Det beskriver ønsket metodik og de kontroller, der løbende skal dokumenteres mod den faktiske kode.

> **Statusnote:** Dette er en review-/designspecifikation, ikke runtime-bevis. Den normative produktionskontrakt er `docs/model_governance.md`, og faktisk drift følger `server/`, `scripts/`, tests og `.github/workflows/daily_update.yml`. Uimplementerede ønsker i dette dokument må ikke præsenteres som aktive produktionskontroller.

---

## 1. 🎯 Projektets Formål & Systemarkitektur

**Københavns Boligmarkedsmodel (v3.2)** er en selvkørende, autonom analyse- og prognoseplatform designet til at overvåge og forudsige prisudviklingen samt identificere boble- og nedrisici på det københavnske ejerboligmarked (København & Frederiksberg).

### 🏗️ Hovedkomponenter & Drift
```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SYSTEMARKITEKTUR                              │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Data Ingestion & Data Lineage Engine                                │
│    • DST API REST (EJ56, HUS1, AUS07, DNRENTM, INDKP107)                │
│    • Boliga Web Scraper via TLS Client Impersonation (curl_cffi)        │
│    • RKR Finance Denmark Statistikbank (live, fail-closed)              │
│                                                                         │
│ 2. Core Calculation & Modeling Server (server/cph_housing_server.py)   │
│    • EWI 1–9 Traffic Light & Freshness Decay Engine ($fw = e^{-\lambda t}$) │
│    • Fundamental User Cost (2024 Skattereform + Blended fradrag)        │
│    • Expert-Weighted Ensemble & Monte Carlo Confidence Bounds             │
│    • Walk-forward price-only benchmark; production ML probability gated │
│                                                                         │
│ 3. Automated CI/CD, Observability & Data Governance                     │
│    • Nattelig kørsel via GitHub Actions med payload-schema og lint gates │
│    • Static Vercel deployment fra genererede artefakter                  │
│                                                                         │
│ 4. React Frontend Dashboard (dashboard/src/)                            │
│    • Glassmorphism UI, risikobarometre, konsekvent dansk klarsprog      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 📐 Økonomiske & Statistiske Modeller (Methodology & Calibration)

### A. Model Calibration Methodology
Initial weights for the Early Warning Indicators (EWI) and scenario ensembles were informed by historical Danish housing market episodes (the 2007–2009 collapse and the 2022 inflation/interest shock) and subsequently refined through expert judgment and cross-validation across macro priors.

### B. Machine Learning Crash Classifier (publication-gated)
* Det tidligere `config/ews_ml_model.skops`-artefakt er trænet på syntetiske feature-rækker og bruges ikke til produktionstal.
* `scripts/evaluate_event_prediction.py` evaluerer i stedet et transparent, price-only walk-forward benchmark med crash-eventdefinitionen fra governance-dokumentet. Det er ikke validation af den deployede ML-model.
* Dashboardet viser derfor ingen ML-procent, før en model med historiske point-in-time live features og out-of-sample kalibrering består quality gate.

### C. Tidlig Varslingssystem (EWI 1–9)
Komposit-scoren (\(\max 27,0\) point) beregnes som:
\[ \text{Composite Score} = \sum_{i=1}^{8} w_i \cdot S_i \cdot fw_i \]
hvor \(S_i \in \{0 (\text{GRØN}), 1 (\text{ADVARSLE}), 3 (\text{ALARM})\}\), \(fw_i = e^{-\lambda \cdot t}\), og ekspert-kalibrerede vægte:
* **EWI-1 (Pris vs. Løn)**: \(w_1 = 1,4\)
* **EWI-2 (Udbud vs. Efterspørgsel)**: \(w_2 = 1,2\)
* **EWI-3 (Volumen-Pris Divergens)**: \(w_3 = 0,5\)
* **EWI-4 (Prisnedsættelser)**: \(w_4 = 1,3\)
* **EWI-5 (Liggetid / DOM)**: \(w_5 = 0,3\) (Rullende Z-score)
* **EWI-6 (Pris-til-Leje Ratio HUS1)**: \(w_6 = 1,1\) (Rullende Z-score, skala-invariant)
* **EWI-7 (Afdragsfrihed)**: \(w_7 = 0,2\)
* **EWI-8 (Debt-Servicing Ratio / DSR)**: \(w_8 = 1,5\) (IMF-tærskel >40% = ALARM)
* **EWI-9 (Ledighed)**: \(w_9 = 1,5\)

### D. Fundamental User Cost (2024 Skattereform)
\[ UC_{fund} = P \times \left[ r(1 - \tau_r) + \tau_p + \delta + rp \right] \]
Inkluderer 2024-boligskattereformen med boligskatterabat, indefrysningsordning, skatteloft og kommunale grundskyldspromiller.

### E. Forecast Ensemble & Monte Carlo Residuals
Ensemble-prognoserne anvender et **Expert-Weighted Ensemble informed by macro priors** (Baseline 55%, Min Risk 20%, Max Risk 25%).
Konfidensintervallerne (p10, p50, p90) estimeres i den nuværende kode ved 1.000 reproducerbare Monte Carlo-træk med seed 42. Det er en modelbaseret scenarievariation, ikke et empirisk konfidensinterval fra en residual-bootstrap.

---

## 3. 📊 Sensitivity & Uncertainty Analysis

Tabellen nedanfor viser følsomheden i 12-måneders prisprognosen ved en isolated \(\pm 10\%\) relativ ændring i nøglevariablerne (lokal følsomhedsmatrix):

| Model Parameter | Parameter Ændring | Relativ Effekt på 12m Forecast | Operational Vigtighed |
|---|---|---|---|
| **Realkreditrente (\(r\))** | \(\pm 10\%\) (f.eks. 3,5% \(\rightarrow\) 3,85%) | **\(\mp 4,2\%\)** | KRITISK (Hoveddriver i kreditkanalen) |
| **Debt-Servicing Ratio (DSR)** | \(\pm 10\%\) relativ ændring | **\(\mp 3,9\%\)** | HØJ (Købekraftsbegrænsning) |
| **Disponibel Indkomst** | \(\pm 10\%\) relativ ændring | **\(\pm 2,8\%\)** | MODERAT (Understøttende fundament) |
| **Huslejeindeks (HUS1)** | \(\pm 10\%\) relativ ændring | **\(\pm 0,6\%\)** | LAV (Langsigtet strukturelt anker) |

---

## 4. 🧪 Udvidet Testplan & Valideringsmatrix

Systemet anvender en 9-lags teststrategi med interne operationelle KPI-grænser (Acceptance Thresholds):

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      UDVIDET TESTMATIX (PRODUCTION)                     │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Unit & Formula Tests (test_tools.py, test_dst_macro.py)            │
│ 2. Data Governance, Pydantic Schema & Anomaly Detection (>3σ)           │
│ 3. Historisk Backtesting Engine (test_backtest.py - Full Metric Suite)   │
│ 4. Regression Testing & Golden Dataset Alignment                        │
│ 5. Data Drift & DST API Schema Change Detection                         │
│ 6. Monte Carlo Reproducibility (1.000 simulationer) & Sensitivity Review │
│ 7. Stress Testing (2008 Finanskrise, COVID-19, 2022 Inflationschok)     │
│ 8. Property-Based Testing (Hypothesis: User Cost > 0 ved r > 0)         │
│ 9. Disaster Recovery & Fallback Audit (5-dags DST nedbrud)              │
│ 10. Playwright E2E Visual Inspection & Scenario Sandbox Audit           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Backtest Performance Results (2007–2024, 17 Årlige Evalueringer)
*Evalueringen foretages 1-step-ahead på 17 årlige observationer (2007–2024) afledt af den underliggende kvartalsserie:*

| Metric | Målt Værdi | Internt KPI Krav / Operationel Kontext |
|---|---|---|
| **MAPE (Mean Absolute Pct Error)** | **7,58%** | < 10,0% (Godkendt internt KPI) |
| **RMSE (Root Mean Squared Error)** | **11,54 pts** | < 15,0 pts (Godkendt internt KPI) |
| **MAE (Mean Absolute Error)** | **6,79 pts** | < 10,0 pts (Godkendt internt KPI) |
| **Mean Bias Error** | **+2,92 pts** | Svagt over-forudsigende under historisk genopretning |
| **Directional Accuracy (Hit Rate)** | **56,2%** | > 50,0% (Hovedfunktions-metrik for retningsændring) |
| **R-squared (\(R^2\))** | **0,061** | *One-step-ahead prisprognoser domineres af stokastiske makrochok; lave R² værdier forventes, hvormed Hit Rate er den primære operationelle metrik.* |

---

## 5. 🛡️ Data Lineage & Governance

### Data Lineage Map
```
[DST / Boliga API / RKR Database]
       │
       ▼
[Data Extraction & Schema Validation (Pydantic)]
       │
       ▼
[Feature Transformation & Z-Score Normalization]
       │
       ▼
[Calculation Server & ML Ensemble Execution]
       │
       ▼
[Payload Generation & Vercel Dashboard Sync]
```

---

## 6. ⚠️ Model Risk Management & Limitations

1. **Kendte Begrænsninger**:
   * Stikprøvestørrelsen for historiske danske boligkriser er lille. Den tidligere syntetiske Random Forest-model er derfor isoleret og leverer ikke en produktionssandsynlighed.
   * Modellen forudsætter uændret lovgivning på boligskatteområdet ud over 2024-reformen.
2. **Kriterier for hvornår prognoser IKKE bør anvendes uændret**:
   * Ved pludselige geopolitiske chok eller reguleringsændringer (f.eks. nye indgrebsregler for afdragsfrihed), som ikke er fanget i de historiske EWI-tidsserier.

---

## 7. 🔒 DevOps, Monitoring & Reproducerbarhed

* **Deterministic Reproducibility**: Forecastets Monte Carlo-del bruger seed 42.
* **Observability & Alerting**: Nattelig workflow-validering sker via GitHub Actions. Sentry-integration er ikke en aktiv kontrol i dette repository.

---
*Dokument opdateret til v3.2 specifikation.*
