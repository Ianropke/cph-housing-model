# Copenhagen Housing Market Model & Dashboard (v3.0)

Dette repository indeholder kildekoden til Københavns Boligmarkedsmodel og det tilhørende styringsdashboard (version 3.0). Modellen fungerer som et Early Warning System (EWS) og beregner de fundamentale ejeromkostninger (User Cost of Housing) for at identificere systemiske ubalancer og bobletendenser.

## 🚀 Live Demo (Vercel)
Dashboardet er implementeret og udgivet på Vercel:
* **Produktions-URL:** [https://dashboard-pi-ten-15.vercel.app](https://dashboard-pi-ten-15.vercel.app)
* **Vercel Project:** `dashboard` under `ianropkes-projects`

> [!NOTE]
> Vercel hoster dashboardet som en statisk frontend-applikation. Knapperne "Opdatér Data", "Kør Backtest" og "Systemstatus" kalder API-endpoints. Ved lokal kørsel afvikles disse via en integreret Python-backend (Vite server middleware), mens de på det statiske Vercel-miljø falder tilbage på præ-genererede datasæt og simuleringsresultater.

---

## 📖 Systemarkitektur & Økonomisk Model

### 1. Fundamental User Cost of Housing ($UC_{fund}$)
Modellen anvender en modificeret udgave af den klassiske brugeromkostningsmodel (inspireret af OECD og Danmarks Nationalbank). For at bryde den cirkulære feedback-logik, hvor stigende prisforventninger reducerer de beregnede ejeromkostninger og derved skaber kunstige "købssignaler", er prisforventningerne ($\pi_e$) blevet separeret helt fra formlen.

Ejeromkostningen beregnes som den **fundamentale nettoudgift** ved at eje:

$$UC_{fund} = \left( r \cdot (1 - \tau_r) + \tau_p + \delta + rp \right) \cdot P$$

Hvor:
* **$P$**: Ejendommens markedsværdi (referenceejendom på 3.000.000 DKK).
* **$r$**: Nominel realkreditrente (fastforrentet 30-årigt lån + bidragssats).
* **$\tau_r$**: Dynamisk blended rentefradragssats. I henhold til danske skatteregler udgør fradragets skatteværdi 33,0% op til 50.000 DKK for enlige (100.000 DKK for ægtepar) og 25,0% for renteudgifter derover.
* **$\tau_p$**: Dynamisk ejendomsskat (grundskyld + ejendomsværdiskat). For at afspejle 2024-boligskattereformen reguleres skattesatsen løbende i forhold til ejendomsprisindeksets udvikling ud fra segmentets basissats.
* **$\delta$**: Segment-specifik vedligeholdelses- og afskrivningsrate (Villaer: 1,9% p.a., Frederiksberg lejligheder: 1,7% p.a., København lejligheder: 1,6% p.a.).
* **$rp$**: Dynamisk risikopræmie, der er rente- og volatilitetsfølsom:
  $$rp = 0,8\% + 0,05 \cdot (r - 2\%)$$

---

### 2. Early Warning System (EWS)
Risikovurderingen foretages på tværs af **8 ledende indikatorer (EWIs)**. Hver indikator tildeles en statistisk vægt baseret på dens historiske evne til at varsle priskorrektioner (f.eks. under finanskrisen i 2006-2008):

| Indikator | Beskrivelse | Statistisk Vægt |
|---|---|---|
| **EWI-1** | Prisudvikling vs. Lønvækst (YoY spread) | 1,4 |
| **EWI-2** | Udbudslager (måneder af salg) | 1,2 |
| **EWI-3** | Volumen-Pris Divergens (YoY) | 1,0 |
| **EWI-4** | Prisnedslag (andel nedsat + gns. nedslag) | 1,3 |
| **EWI-5** | Liggetid (median-liggetid i forhold til Z-score) | 0,8 |
| **EWI-6** | Pris/Leje-forhold (Z-score afvigelse) | 1,1 |
| **EWI-7** | Kreditvækst & Afdragsfri andel (RKR) | 0,7 |
| **EWI-8** | Gældsbetjeningsgrad (Debt Service Ratio) | 1,5 |

Den samlede kompositscore beregnes som summen af de vægtede indikatorscores (0 for grøn, 1 for gul, 3 for rød), hvilket giver en maksimal samlet risikoscore på **27,0 point**.

Alarmtærsklerne er defineret som:
* 🟢 **NORMAL**: $< 4.5$
* 🟡 **ELEVATED**: $\ge 4.5$
* 🟠 **HIGH**: $\ge 9.0$
* 🔴 **CRITICAL**: $\ge 15.5$
* 💀 **EXTREME**: $\ge 21.0$

---

### 3. Dataingestion & Friskhed (Data Freshness)
Data hentes direkte fra **Danmarks Statistik (DST) API (Tabel EJ56)** og **Finansdanmark (RKR)**.
Modellen anvender et **eksponentielt friskhedsforfald** på datakilderne for at straffe forældede oplysninger:

$$W_{fresh} = e^{-\lambda \cdot t_{age}}$$

Hvor $t_{age}$ er antallet af dage siden seneste opdatering, og $\lambda$ er tilpasset kildens frekvens (daglig, månedlig, kvartalsvis, årlig).

---

## 🛠️ Teknisk Implementering & Udvikling

### Projektstruktur
```
cph-housing-model/
├── architecture/          # Dokumentation af det teoretiske framework og EWS
├── config/                # Konfigurationsfiler til scenarier
├── dashboard/             # React + Vite frontend
│   ├── src/
│   │   ├── components/    # UI Paneler (UserCost, EarlyWarning, Forecast)
│   │   ├── data/          # Genererede data-assets (housingData.js)
│   │   └── App.jsx        # Hovedkomponent & Vercel API mock/fallbacks
│   └── index.html
├── reports/               # Automatiske daglige rapporter (Markdown)
├── scripts/               # Datapipeline-scripts (daily_pipeline.py)
├── server/                # Beregningskerne i Python (cph_housing_server.py)
├── tests/                 # Unit- og integrationstests
├── manage.sh              # Styringsscript til start, test og opdatering
└── vercel.json            # Vercel byggekonfiguration
```

### Lokal Kørsel & Udvikling
For at afvikle hele systemet med live Python-integration i dashboardet:

1. **Kør testsuiten for at verificere beregninger:**
   ```bash
   ./manage.sh test
   ```
2. **Kør datapipelinen manuelt for at hente friske tal:**
   ```bash
   ./manage.sh update
   ```
3. **Start dashboardet lokalt (Vite Dev Server):**
   ```bash
   ./manage.sh start
   ```
   Dette vil starte dashboardet på `http://localhost:5173/` og automatisk proxy'e API-kaldene (`/api/update`, `/api/backtest`, `/api/status`) til Python-miljøet.

### Testdækning
Integrationstests dækker:
* Korrekt beregning af den dynamiske ejendomsskat ($\tau_p$) og det blandede rentefradrag ($\tau_r$).
* Backtesting på tværs af perioden **2000–2026** for at validere modellens evne til at fange it-boblen, finanskrisen og COVID-boomet.
* Korrekt skalering af EWS til den nye vægtede 27,0-pointskala.
