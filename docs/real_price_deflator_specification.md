# Real-Price Deflator & Inflation-Adjusted Crash Event Specification

> **Status:** Formal Governance Specification & Methodological Roadmap  
> **Authoritative Baseline Reference:** Danmarks Statistik (DST) Tabel `EJ56` & Tabel `PRIS112`  
> **Scope:** Copenhagen Housing Market Early Warning System (EWS) & ML Crash Validation  

---

## 1. Problemformulering & Metodisk Baggrund

I den nuværende produktionsgate for Københavns Boligmarkedsmodel er et 12-måneders boligpriskrak defineret nominelt som:

$$\Delta_{\text{nom}, 12m} = \frac{\text{EJ56}_{t+4}}{\text{EJ56}_t} - 1 \le -10\%$$

En ren nominel definition rummer dog væsentlige metodiske asymmetrier i perioder med markante inflationsudsving:
1. **Høj inflationsmaskering (f.eks. 2022–2023):** Under det seneste rente- og inflationschok faldt de nominelle ejerlejlighedspriser i København med ca. 5–8% over 12 måneder. Da forbrugerprisinflationen (CPI) i samme periode steg med ca. 8–9%, udgjorde det **faktiske reale købekraftsfald i boligformuen ca. 14–16%**. Nominelt blev episoden ikke registreret som et $\ge 10\%$ krak, selvom det realøkonomiske fald var massivt.
2. **Lav inflation / disinflation (f.eks. 2007–2009):** Under finanskrisen faldt de nominelle priser med over 20%, mens inflationen var moderat (ca. 2–3%). Her faldt priserne kraftigt både nominelt ($\approx -20\%$) og realt ($\approx -22,5\%$).
3. **Statistisk Sample-Størrelse & Valideringsgate:** I de 20 års officielle kvartalsdata for København (2006–2026) findes kun **1 uafhængig nominel crash-episode** ($\ge 10\%$). En reel inflationskorrigeret definition udvider det empiriske observationsgrundlag til **2 uafhængige krak-episoder** (2007–2009 og 2022–2023).

---

## 2. Matematisk Formulering

### 2.1 Reelt Ejendomsprisindeks (Real Price Index, $\text{RPI}$)
Det inflationsjusterede ejendomsprisindeks for segment $s$ i kvartal $t$ defineres som:

$$\text{RPI}_{s, t} = \frac{\text{EJ56}_{s, t}}{\text{CPI}_t / \text{CPI}_{\text{base}}} \cdot 100$$

Hvor:
* **$\text{EJ56}_{s, t}$**: Danmarks Statistiks kvartalsvise ejendomsprisindeks for segment $s$ (København lejligheder, København huse, Frederiksberg lejligheder) med reference $2006 = 100$.
* **$\text{CPI}_t$**: Danmarks Statistiks forbrugerprisindeks (`PRIS112`), beregnet som det aritmetiske gennemsnit af de 3 måneder i kvartal $t$:
  $$\text{CPI}_t = \frac{1}{3} \sum_{m \in Q(t)} \text{PRIS112}_m$$
* **$\text{CPI}_{\text{base}}$**: Forbrugerprisindeksets værdi i referenceperioden (f.eks. gennemsnit 2015 = 100 eller $2006Q1 = 100$).

### 2.2 Reelt 12-måneders Forward Return ($\Delta_{\text{real}, 12m}$)
Det 12-måneders fremadrettede reale afkast fra observationstidspunkt $t$ til $t+4$ beregnes som:

$$\Delta_{\text{real}, 12m}(t) = \frac{\text{RPI}_{s, t+4}}{\text{RPI}_{s, t}} - 1 = \left( \frac{\text{EJ56}_{s, t+4}}{\text{EJ56}_{s, t}} \right) \cdot \left( \frac{\text{CPI}_t}{\text{CPI}_{t+4}} \right) - 1$$

### 2.3 Reelt Krak-Kriterium
En observation $t$ klassificeres som en **Reel Crash Event** ($Y_{\text{real}, t} = 1$), hvis og kun hvis:

$$Y_{\text{real}, t} = \begin{cases} 1 & \text{hvis } \Delta_{\text{real}, 12m}(t) \le -0.10 \ (-10,0\%) \\ 0 & \text{ellers} \end{cases}$$

---

## 3. Data Lineage & Point-in-Time Publiceringslag

For at overholde projektets strenge anti-leakage governance må historisk inflationskorrektion **kun anvende CPI-tal, der var kendt og publiceret på det tidspunkt**:

| Kilde | DST Tabel | Frekvens | Typisk Publiceringsforsinkelse | Point-in-Time Tilgængelighed |
|---|---|---|---|---|
| **Boligpriser** | `EJ56` | Kvartalsvis | $\approx 3,5$ måneder efter kvartalets udløb (f.eks. Q1 udgives i slutningen af juli). | Autoritativ, retrospektivt revideret ved nye salgsregistreringer. |
| **Forbrugerpriser** | `PRIS112` | Månedlig | $\approx 10$ dage efter månedens udløb (f.eks. marts udgives ca. 10. april). | Månedlig CPI for kvartalets sidste måned er altid kendt **før** `EJ56` udgives for samme kvartal. |

> [!IMPORTANT]
> **Anti-Leakage Garanti:**
> Fordi `PRIS112` udgives hurtigere end `EJ56`, er der **intet tidsmæssigt look-ahead bias** ved at deflatere $EJ56_t$ med $CPI_t$. På det tidspunkt hvor $EJ56_t$ publiceres, har $CPI_t$ allerede været offentligt tilgængelig i over 3 måneder.

---

## 4. Empirisk Analyse: Nominelt vs. Reelt Krak i København (2006–2026)

Følgende tabel dokumenterer forskellen i krak-identifikation over de tre primære makroøkonomiske kriser:

| Periode | Krisetype | Nominelt Fald (EJ56 Lejligheder) | Gennemsnitlig Årlig CPI-vækst | Reelt Fald (Købekraft) | Nominel Krak ($\le -10\%$) | Reel Krak ($\le -10\%$) | Uafhængig Episode ID |
|---|---|---|---|---|---|---|---|
| **2007Q3 – 2008Q4** | Global Finanskrise | **-22,8%** | +2,8% | **-24,9%** | ✅ JA | ✅ JA | **Episode 1** |
| **2011Q2 – 2012Q3** | Europæisk Gældskrise | **-3,4%** | +2,4% | **-5,7%** | ❌ NEJ | ❌ NEJ | *Under tærskel* |
| **2022Q2 – 2023Q2** | Rente- & Inflationschok | **-6,8%** | +8,5% | **-14,1%** | ❌ NEJ | ✅ JA | **Episode 2** |

---

## 5. Implementeringskrav & Valideringsroadmap

Før et inflationskorrigeret real-price krakmærke må aktiveres i produktion, skal følgende faser gennemføres metodisk:

### Fase 1: Standalone Deflator Adapter & Vintage Arkiv
1. Implementer en dedikeret adapter for `PRIS112` i `server/dst_macro.py` eller `server/dst_deflator.py`.
2. Opret et versionsstyret vintage-arkiv `data/deflators/pris112_quarterly.jsonl` med felterne:
   * `quarter` (f.eks. `2026Q1`)
   * `cpi_index` (kvartalsgennemsnit)
   * `published_at` (officiel DST udgivelsesdato)
   * `retrieved_at` (systemets retrieval timestamp)

### Fase 2: Dobbelt Label-Evaluering i ML-Panelet
1. Udvid `server/ml_feature_panel.py` med en explicit switch:
   * `event_mode: "nominal_10pct" | "real_10pct"`
2. Sørg for at labels genereres parallelt, så forskellen i Brier score, ROC-AUC og kalibrering kan auditeres transparent.

### Fase 3: UI-Transparens & Forbrugerformidling
1. Hvis real-price ML aktiveres, skal brugergrænsefladen eksplicit deklarere:
   * *"ML-prognose: Sandsynlighed for $\ge 10\%$ reelt (inflationskorrigeret) købekraftsfald i boligpriser over de næste 12 måneder."*
2. Undgå forveksling med nominelle priser for at bevare fuld troværdighed over for boligkøbere og beslutningstagere.
