# 📄 Københavns Boligmarkedsmodel — Projekt- & Testplanspecifikation (Review-dokument)

> **Formål:** Dette dokument giver en komplet, teknisk og økonomisk gennemgang af *Copenhagen Housing Market Forecasting & Early Warning Ecosystem*. Dokumentet kan kopieres direkte ind i ChatGPT eller sendes til en ekstern reviewer for uvildig auditering af arkitektur, økonomiske modeller, datakvalitet og testplan.

---

## 1. 🎯 Projektets Formål & Systemarkitektur

**Københavns Boligmarkedsmodel (v3.0)** er et selvkørende, autonomt analyse- og prognosesystem designet til at overvåge og forudsige prisudviklingen samt identificere boble- og nedrisici på det københavnske ejerboligmarked (København & Frederiksberg).

### 🏗️ Hovedkomponenter
1. **Data Ingestion Engine (`scripts/market_data_agent.py` & `server/dst_macro.py`)**:
   * **Danmarks Statistik (DST)**: Automatisk hentning af kvartalsvise prisindeks (`EJ56`), huslejeindeks (`HUS1`), ledighed (`AUS07`), indskudsbevisrente (`DNRENTM`) og disponibel indkomst (`INDKP107`).
   * **Boliga Custom Scraper**: Daglige realtidsdata for udbudte ejerlejligheder og villaer (postnr. 1000–2999) vha. TLS-impersonation (`curl_cffi` chrome110) til måling af udbudsmåneder, liggetider (DOM) og prisnedsættelsesrater.
2. **Model & Calculation Server (`server/cph_housing_server.py`)**:
   * **Tidlig Varsling (EWI 1–8)**: Statistisk vægtet trafiklys-system (GRØN / ADVARSLE / ALARM).
   * **Fundamental User Cost**: 12-måneders ejeromkostningsberegning ud fra OECD/Nationalbankens formel tilpasset danske skatteregler.
   * **Forecast Ensemble & Monte Carlo**: Probabilistiske 6-, 12- og 24-måneders prisprognoser med 90% konfidensintervaller (p10, p50, p90).
   * **Machine Learning Crash Classifier**: Random Forest-model trænet på historiske EWI-data (2000–2026) til forudsigelse af sandsynligheden for prisfald >10% over 12 måneder.
3. **Automated CI/CD Pipeline (`.github/workflows/daily_update.yml` & `scripts/daily_pipeline.py`)**:
   * Kører automatisk hver nat via GitHub Actions. Opdaterer `latest_pipeline.json`, regenererer `housingData.js` og udgiver daglige markedsrapporter (`reports/daily_YYYY-MM-DD.md`).
4. **React Frontend Dashboard (`dashboard/`)**:
   * Moderne Glassmorphism UI udrullet på Vercel med realtidssignaler, interaktive risikobarometre og konsekvent dansk terminologi.

---

## 2. 📐 Økonomiske & Statistiske Modeller

### A. Tidlig Varslingssystem (EWI 1–8)
Modellen måler 8 uafhængige risikoindikatorer:
* **EWI-1 (Pris vs. Løn)**: Sammenligner boligprisstigning med lønvækst (med kortsigtede og 3-5 års strukturelle glidende gennemsnit).
* **EWI-2 (Udbud vs. Efterspørgsel)**: Antal udbudsmåneder baseret på live Boliga-udbud og historiske salgstal.
* **EWI-3 (Volumen-Pris Divergens)**: Måler om stigende priser ledsages af faldende handelsvolumen (spekulativt tegn).
* **EWI-4 (Prisnedsættelser)**: Andelen af aktive udbud på Boliga med registrerede prisafslag og gennemsnitlig afslagsstørrelse.
* **EWI-5 (Liggetid / DOM)**: Rullende Z-score over 12 kvartaler for median liggetid (\(Z = \frac{X - \mu_{12Q}}{\sigma_{12Q}}\)).
* **EWI-6 (Pris-til-Leje Ratio)**: Rullende Z-score for boligpriser i forhold til DST lejeindekset (`HUS1`). *Skala-invariant metode.*
* **EWI-7 (Afdragsfrihed)**: Andelen af nye realkreditlån uden afdrag (RKR UL10).
* **EWI-8 (Debt-Servicing Ratio / DSR)**: Samlet gældsbetjeningsbyrde (renter + bidrag) i forhold til disponibel indkomst (IMF-tærskel >40% = RØD).

#### Dynamisk Data Freshness Weighting
Hver datakilde vægtes med en eksponentiel forfaldsformel:
\[ fw = e^{-\lambda \cdot t}, \quad \text{hvor } \lambda = \frac{\ln(2)}{\text{half\_life}} \]
Datakilder, der er ældre end deres halveringstid (f.eks. årlige indkomstdata), nedvægtes automatisk i den samlede composite score (max 27,0 point).

### B. Fundamental User Cost (Brugeromkostning)
Beregnes ud fra ejerens løbende finansielle byrde adskilt fra spekulativt sentiment:
\[ UC_{fund} = P \times \left[ r(1 - \tau_r) + \tau_p + \delta + rp \right] \]
* \(r\): Realkreditrente (30-årigt fast lån)
* \(\tau_r\): Effektiv rentefradragssats i Danmark (trinvist vægtet: 33% under DKK 50k/100k grænsen, 25% over)
* \(\tau_p\): Dynamisk ejendomsværdi- og grundskyldssats
* \(\delta\): Vedligeholdelse (segmenteret for huse vs. ejerlejligheder)
* \(rp\): Rente- og likviditetsrisikopræmie

### C. Forecast Ensemble & Scenarier
Beregnes som et vægtet gennemsnit af tre scenarier:
1. **Baseline (55% vægt)**: Moderat rentesænkning, stabil lønvækst og trendmæssig prisstigning.
2. **Min Risk / Optimistisk (20% vægt)**: Rentesænkninger og høj efterspørgsel.
3. **Max Risk / Stagflation (25% vægt)**: Rentestigninger, faldende rådighedsbeløb og prisfald.

---

## 3. 🧪 Testplan & Validering (Test Matrix)

Systemet er underlagt en omfattende automatiserede testmatrix bestående af 4 testlag:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AUTOMATISERET TESTSUITE                          │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Unit Tests (test_tools.py, test_dst_macro.py)                        │
│    • Validerer matematiske formler (UC, Z-score, Freshness decay)      │
│    • Cache-isolation via setUp() state reset                            │
│                                                                         │
│ 2. Data Integrity Tests (test_data_integrity.py)                       │
│    • Validerer JSON-schema struktur og opdateringstidsstempler          │
│    • Tjekker at prisindeks og udbudstal er inden for gyldige bounds    │
│                                                                         │
│ 3. Historisk Backtesting Engine (test_backtest.py)                       │
│    • 1-step-ahead historisk simulering (2007 - 2024)                    │
│    • Betinget fejlanalyse uden fejl-akkumulering                        │
│                                                                         │
│ 4. Network & Resilience Integration (test_dst_403.py)                  │
│    • Validerer TLS-impersonation & User-Agent mod Cloudflare / WAF      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Detailed Test Specifications

| Testkategori | Testfil / Metode | Testformål & Godkendelseskriterie (Acceptance Criteria) |
|---|---|---|
| **Formel-validering** | `tests/test_tools.py` | Bekræfter at User Cost formlen leverer korrekte månedlige DKK-beløb og marginalskattesatser. |
| **Cache-isolation** | `tests/test_dst_macro.py` | `setUp()` nulstiller `_macro_data_cache = None` for at forhindre at opnåede testresultater lækker ind i fejltest-cases. |
| **Datagrundlag** | `tests/test_data_integrity.py` | Verificerer at `latest_pipeline.json` har opdaterede datoer, gyldige postnumre og ikke indeholder `NaN` eller `null` felter. |
| **Historisk Backtest** | `tests/test_backtest.py` | Evaluerer modellens forudsigelsesevne 2007–2024. **Resultat: MAPE = 7,58%, RMSE = 11,54 pts.** |
| **WAF Resilience** | `scripts/market_data_agent.py` | Tester 3-attempt retry-loop og Chrome 110 TLS fingerprint mod Boliga API. |

---

## 4. 📋 Review-Spørgsmål til ChatGPT / Ekstern Auditor

Når du sender dette dokument til review hos ChatGPT eller en ekstern ekspert, kan du med fordel bede om feedback på følgende specifikke spørgsmål:

1. **Metodisk Vurdering af EWI Systemet**:
   * *Er den rullende Z-score på 12 kvartaler den optimale metode til at sikre skala-invarians ved skift i lejeindeks-basisår, eller bør vinduesstørrelsen tilpasses?*
2. **Økonomisk User Cost Rigor**:
   * *Er adskillelsen af prisforventninger (sentiment) fra de fundamentale ejeromkostninger (\(UC_{fund}\)) tilstrækkelig til at forhindre cirkulær logik i opgangsmarkeder?*
3. **Robusthed af Scraper & API Egress**:
   * *Yder brugen af `curl_cffi` TLS impersonation samt eksplicitte User-Agent headers tilstrækkelig beskyttelse mod fremtidige WAF-ændringer i et serverless miljø som Vercel?*
4. **Testplan Dækning**:
   * *Er der uafdækkede hjørnetilfælde (edge cases) i testplanen — f.eks. ved ekstreme rentehop eller manglende DST-kvartalsrapporter?*

---
*Dokument oprettet og klar til kopi/export.*
