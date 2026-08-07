# 📄 Københavns Boligmarkedsmodel — Architectural & Model Design Specification (v3.2)

> **Formål:** Dette dokument udgør den samlede arkitektur-, model- og testplanspecifikation for *Copenhagen Housing Market Forecasting & Early Warning Ecosystem (v3.2)*. Dokumentet indeholder metodisk dokumentation for modelkalibrering, Random Forest interpretability (OOB & Permutation Importance), Data Lineage, Model Risk Management, Følsomhedsanalyse, Observability & Disaster Recovery samt udvidede statistiske valideringsmetrikker.

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
│    • RKR Finance Denmark High-Fidelity Local Baseline                   │
│                                                                         │
│ 2. Core Calculation & Modeling Server (server/cph_housing_server.py)   │
│    • EWI 1–8 Traffic Light & Freshness Decay Engine ($fw = e^{-\lambda t}$) │
│    • Fundamental User Cost (2024 Skattereform + Blended fradrag)        │
│    • Expert-Weighted Ensemble & Monte Carlo Confidence Bounds             │
│    • Machine Learning Random Forest Crash Classifier (Walk-Forward)     │
│                                                                         │
│ 3. Automated CI/CD, Observability & Data Governance                     │
│    • Nattelig kørsel via GitHub Actions med Schema Validation & Sentry  │
│    • Automatic Vercel deployment med build caching                       │
│                                                                         │
│ 4. React Frontend Dashboard (dashboard/src/)                            │
│    • Glassmorphism UI, risikobarometre, konsekvent dansk klarsprog      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 📐 Økonomiske & Statistiske Modeller (Methodology & Calibration)

### A. Model Calibration Methodology
Initial weights for the Early Warning Indicators (EWI) and scenario ensembles were informed by historical Danish housing market episodes (the 2007–2009 collapse and the 2022 inflation/interest shock) and subsequently refined through expert judgment and cross-validation across macro priors.

### B. Machine Learning Crash Classifier (Walk-Forward & Interpretability)
* **Feature Set & Permutation Importance**: 8 EWI indikatorer, \(\Delta r\), DSR, pris-til-løn spread og rullende 12-kvartalers Z-scores. Permutation Feature Importance anvendes til at vurdere den relative effekt af hver indikator.
* **Tidsserie-validering & OOB Score**: Anvender **Walk-Forward Validation (`TimeSeriesSplit` med 5 folds)** for at eliminere data leakage. Out-of-Bag (OOB) error estimation (`oob_score=True`) anvendes som en uafhængig valideringsmetrik på den begrænsede prøvestørrelse.
* **Regulering & Hyperparametre**: Max trædybde (`max_depth=4`), minimum prøver pr. blad (`min_samples_leaf=3`) og `n_estimators=100`.
* **Class Imbalance & Kalibrering**: Balanceret vægtning (`class_weight="balanced"`) og **Isotonic Regression** for sandsynlighedskalibrering.

### C. Tidlig Varslingssystem (EWI 1–8)
Komposit-scoren (\(\max 27,0\) point) beregnes som:
\[ \text{Composite Score} = \sum_{i=1}^{8} w_i \cdot S_i \cdot fw_i \]
hvor \(S_i \in \{0 (\text{GRØN}), 1 (\text{ADVARSLE}), 3 (\text{ALARM})\}\), \(fw_i = e^{-\lambda \cdot t}\), og ekspert-kalibrerede vægte:
* **EWI-1 (Pris vs. Løn)**: \(w_1 = 1,4\)
* **EWI-2 (Udbud vs. Efterspørgsel)**: \(w_2 = 1,2\)
* **EWI-3 (Volumen-Pris Divergens)**: \(w_3 = 1,0\)
* **EWI-4 (Prisnedsættelser)**: \(w_4 = 1,3\)
* **EWI-5 (Liggetid / DOM)**: \(w_5 = 0,8\) (Rullende Z-score)
* **EWI-6 (Pris-til-Leje Ratio HUS1)**: \(w_6 = 1,1\) (Rullende Z-score, skala-invariant)
* **EWI-7 (Afdragsfrihed)**: \(w_7 = 0,7\)
* **EWI-8 (Debt-Servicing Ratio / DSR)**: \(w_8 = 1,5\) (IMF-tærskel >40% = ALARM)

### D. Fundamental User Cost (2024 Skattereform)
\[ UC_{fund} = P \times \left[ r(1 - \tau_r) + \tau_p + \delta + rp \right] \]
Inkluderer 2024-boligskattereformen med boligskatterabat, indefrysningsordning, skatteloft og kommunale grundskyldspromiller.

### E. Forecast Ensemble & Monte Carlo Residuals
Ensemble-prognoserne anvender et **Expert-Weighted Ensemble informed by macro priors** (Baseline 55%, Min Risk 20%, Max Risk 25%).
Konfidensintervallerne (p10, p50, p90) estimeres ved **Block Bootstrap (bloklængde = 4 kvartaler)** kombineret med 10.000 Monte Carlo-simuleringer på den empiriske residualfordeling.

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
│ 6. Monte Carlo Convergence (10.000 simulationer) & Sensitivity Analysis │
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
   * Stikprøvestørrelsen for historiske danske boligkriser er lille. Random Forest-klassifikatoren bør ses som et supplerende supplement til EWI-indikatorerne.
   * Modellen forudsætter uændret lovgivning på boligskatteområdet ud over 2024-reformen.
2. **Kriterier for hvornår prognoser IKKE bør anvendes uændret**:
   * Ved pludselige geopolitiske chok eller reguleringsændringer (f.eks. nye indgrebsregler for afdragsfrihed), som ikke er fanget i de historiske EWI-tidsserier.

---

## 7. 🔒 DevOps, Monitoring & Reproducerbarhed

* **Deterministic Reproducibility**: Garanterer deterministisk reproducerbarhed inden for et identisk softwaremiljø ved hjælp af faste pseudo-random seeds (`seed=42`).
* **Observability & Alerting**: Nattelig workflow-overvågning via GitHub Actions alerts, Sentry fejlsporing og automatisk Vercel deployment status.

---
*Dokument opdateret til v3.2 specifikation.*
