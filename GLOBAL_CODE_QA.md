# 📄 GLOBAL CODE QA & PROJECT LEARNINGS
> **Projekter:** Ian & Lars' 50th Birthday Bash / Copenhagen Housing Market Forecasting Ecosystem  
> **Dato:** August 2026  
> **Formål:** Global opsamling af tekniske erfaringer, arkitekturmønstre, database-sikkerhed, web scraping, finansiel modellering, Machine Learning validering, JSX-syntaks, Edge-caching, Playwright E2E visual inspection og UI/UX best practices til fremtidige projekter.

---

## 1. Supabase & PostgreSQL (Database & Security Best Practices)

### 🔴 Læring 1.1: Parameter-typer i RPC-funktioner skal matche tabellens reelle skjulte typer
* **Problem:** Ved reservation og afreservation fejlede kaldet med PostgreSQL-fejlen:  
  `operator does not exist: text = uuid`  
* **Årsag:** Supabase-tabellens kolonne `reserved_by` var oprettet som `TEXT`/`VARCHAR` (ikke `UUID`), men RPC-funktionen `cancel_wish(p_wish_id UUID, p_visitor_token UUID)` forventede en `UUID`. Sammenligningen `reserved_by = p_visitor_token` i SQL udløste en typefejl.
* **Løsning:** Opdater altid RPC-parametre til `TEXT`, hvis klienten sender genererede tokens/strenger (f.eks. `crypto.randomUUID()`), eller sørg for eksplicit type-casting i SQL (`p_visitor_token::text`).

### 🔴 Læring 1.2: Genoprettelse af PostgreSQL funktioner kræver `DROP FUNCTION IF EXISTS`
* **Problem:** Kørsel af `CREATE OR REPLACE FUNCTION reserve_wish(...)` fejlede i Supabase SQL Editor med:  
  `ERROR: 42P13: cannot change name of input parameter "p_reserved_by"` eller type-mismatch.
* **Årsag:** PostgreSQL tillader ikke at ændre parameternavne eller parametertyper på eksisterende funktioner via `CREATE OR REPLACE` alene.
* **Løsning:** Tilføj altid eksplicitte `DROP FUNCTION`-sætninger med alle tidligere signaturer før `CREATE OR REPLACE`:
  ```sql
  DROP FUNCTION IF EXISTS reserve_wish(UUID, UUID);
  DROP FUNCTION IF EXISTS reserve_wish(UUID, TEXT);
  
  CREATE OR REPLACE FUNCTION reserve_wish(p_wish_id UUID, p_visitor_token TEXT)
  RETURNS BOOLEAN
  LANGUAGE plpgsql
  SECURITY DEFINER
  AS $$ ... $$;
  ```

### 🔒 Læring 1.3: Server-side adgangskontrol med `SECURITY DEFINER` og RLS
* **Mønster:** For at forhindre at udefrakommende kan slette eller ændre ønsker via klientens anon-nøgle:
  1. Aktiver **Row Level Security (RLS)** på tabellen: `ALTER TABLE wishes ENABLE ROW LEVEL SECURITY;`
  2. Giv offentligheden kun `SELECT` rettigheder: `CREATE POLICY "Public Read" ON wishes FOR SELECT USING (true);`
  3. Udfør alle `INSERT`, `UPDATE` og `DELETE` via lukkede PL/pgSQL funktioner med `SECURITY DEFINER`, som validerer admin-kodeordet (`p_admin_password`) direkte på Supabase serveren.

---

## 2. CSS Animationer & 3D Baggrunde

### 🎨 Læring 2.1: Animer `background-position` frem for 3D `transform: translateY()` for sømløse mønstre
* **Problem:** 3D-neongitteret i baggrunden opførte sig uroligt og "blinkede" eller "hoppede" hvert 5. sekund.
* **Årsag:** Animationen rykkede elementet fysisk i 3D-perspektiv (`transform: perspective(500px) rotateX(60deg) translateY(50px)`), hvilket ændrede linjernes vinkler i forhold til kameraet og udløste et synligt skift ved loop-start (0%).
* **Løsning:** Hold selve 3D-containeren 100% statisk, og animer udelukkende mønstrets `background-position-y`:
  ```css
  .cyber-grid {
    position: fixed;
    bottom: 0;
    left: -50%;
    width: 200%;
    height: 60vh;
    background-image: 
      linear-gradient(rgba(0, 255, 255, 0.2) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 255, 255, 0.2) 1px, transparent 1px);
    background-size: 60px 60px;
    transform: perspective(300px) rotateX(65deg);
    transform-origin: center top;
    animation: gridMove 8s linear infinite;
  }

  @keyframes gridMove {
    0% { background-position: 0 0; }
    100% { background-position: 0 60px; }
  }
  ```

---

## 3. Web Audio API & Mobil UX i Arkadespil

### 🔊 Læring 3.1: Ekstern-fri lydsyntese med `AudioContext`
* **Mønster:** I stedet for at hente tunge MP3/WAV lydeffekter til interaktive spil kan man bruge browserens indbyggede `AudioContext` til at fremstille retro synth-lyde i realtid:
  - **Laser ("pew!")**: Sawtooth-oscillator med frekvens-sweep fra 800Hz til 120Hz over 0.15s.
  - **Eksplosion**: Hvid støj via `AudioBuffer` kombineret med et low-pass filter (800Hz ➔ 10Hz).
  - **Fejl-buzz**: Diskonteret kombination af triangle- og sawtooth-bølger.
* **Lazy Initialization**: Opret eller genoptag altid `AudioContext` i et bruger-initieret `onClick`-event for at overholde browserens autoplay-politiker:
  ```js
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  ```

### 📱 Læring 3.2: Undgå dobbelt-tap zoom på mobile touch-skærme
* **Problem:** Hurtigt klik/tap på arkade-targetknapper på telefoner fik browseren til at zoome ind på skærmen (dobbelt-tap zoom).
* **Løsning:** Tilføj `touchAction: 'none'` og CSS-klassen `touch-none` / `touch-action: manipulation` på spillets container-grid:
  ```jsx
  <div 
    ref={gridRef}
    style={{ touchAction: 'none' }}
    className="grid grid-cols-3 grid-rows-3 touch-none select-none"
  >
  ```

---

## 4. Medieoptimering & Performance

### ⚡ Læring 4.1: Automatiserede scripts til billed- og videokomprimering
* **Billeder (Python PIL)**: Ved at køre et simpelt PIL-script blev tunge kamera-/grafikbilleder (f.eks. `program.jpeg` 3.05 MB og `venue-map.jpeg` 2.47 MB) komprimeret til ~300-400 KB uden synligt tab ved at resample bredden til max 1920px med `quality=82` og `optimize=True`.
* **Videoer (macOS `avconvert`)**: Tunge MP4-filer (f.eks. `hero-drive.mp4` på 14 MB) kan reduceres med over 40% ved at køre macOS's indbyggede `avconvert`:
  ```bash
  avconvert -s public/hero-drive.mp4 -p Preset1280x720 -o public/hero-drive-compressed.mp4 --replace
  ```
* **Video Autoplay Best Practice**: Brug altid `muted`, `loop`, `autoPlay`, `playsInline` på baggrundsvideoer for at sikre, at iOS Safari og Android Chrome ikke blokerer afspilningen.

---

## 5. UI Resiliency & Tekst-Overflow i Admin/Lister

### 🛡️ Læring 5.1: Håndtering af ekstremt lange URL'er og titler
* **Problem:** Elementer med ekstremt lange webadresser (f.eks. Amazon/Pandora links på 200+ tegn) fik admin-listen til at bryde sit grid og skubbe redigerings- og sletteknapperne ud af skærmen.
* **Løsning:** Formater altid links inde i en kontrolleret badge-container med `truncate` og `break-all`:
  ```jsx
  <div className="max-w-full overflow-hidden">
    <a 
      href={wish.url} 
      className="block truncate text-xs font-mono text-neonCyan hover:underline max-w-[200px] sm:max-w-[350px]"
    >
      {wish.url}
    </a>
  </div>
  ```

---

## 6. CPH Housing Model (Data Pipelines, Web Scraping, Financial Modeling, React & Edge DevOps)

### 🌐 Læring 6.1: Bypass af WAF og Cloudflare ved Web Scraping (TLS Client Impersonation)
* **Problem:** Standard HTTP-kald med `urllib` eller `requests` mod offentlige ejendomssider (som Boliga.dk) udløste `403 Forbidden` eller Cloudflare JS-challenges.
* **Årsag:** Moderne WAF-løsninger analyserer SSL/TLS handshaket (JA3/TLS fingerprints), som i standard Python skiller sig ud fra rigtige browsere.
* **Løsning:** Anvend `curl_cffi` med eksplicit TLS client impersonation (`impersonate="chrome110"`):
  ```python
  from curl_cffi import requests
  
  response = requests.get(
      "https://api.boliga.dk/api/v2/search/results?...",
      impersonate="chrome110",
      timeout=15
  )
  ```

### 🛡️ Læring 6.2: HTTP User-Agent i Serverless & Sandbox Egress
* **Problem:** Automatisk kørsel af API-kald (f.eks. til Danmarks Statistik `api.statbank.dk`) returnerede `403 Forbidden` i visse headless serverless-miljøer (f.eks. Vercel) eller under sandboxed terminalkørsler.
* **Årsag:** Serverless egress-proxies eller DST API-netværksregler blokerer standard `Python-urllib/3.13` klient-headers.
* **Løsning:** Tilføj altid en gyldig browser `User-Agent` header i alle HTTP-requests:
  ```python
  headers = {
      "Content-Type": "application/json",
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
  }
  ```

### 📊 Læring 6.3: Skala-invarians og skift af Indeks-basisår (HUS1 vs PRIS111)
* **Problem:** Skift af lejeindeks-kilde fra `PRIS111` (base 2015=100) til det nyere `HUS1` (base 2021Q1=100) ændrede det absolutte lejeniveau fra ~120 til ~113.
* **Matematisk Indsigt:** Eftersom Z-scoren beregnes på historiske kvartalsvise forholdstal \(R_t = \frac{P_t}{Rent_t}\):
  \[ Z = \frac{R_{latest} - \mu_{12Q}}{\sigma_{12Q}} \]
  er indikatoren **skala-invariant** (scale-invariant). Enhver lineær skaleringsfaktor på lejeindekset forkortes væk i Z-score beregningen.

### 🧪 Læring 6.4: Isolation af Global Cache i Unit Testing (State Leakage)
* **Problem:** En unittest for et API-nedbrud (`test_fetch_dst_macro_data_failure`) fejlede med `AssertionError`, fordi den modtog data fra en tidligere unittest-kørsel i samme Python-proces.
* **Årsag:** `dst_macro.py` benyttede en global in-memory cache `_macro_data_cache`, som ikke blev nulstillet mellem testcases.
* **Løsning:** Tilføj altid en `setUp()` metode i `unittest.TestCase`, som nulstiller alle globale tilstandsvariabler før hver test:
  ```python
  def setUp(self):
      dst_macro._macro_data_cache = None
  ```

### ⏱️ Læring 6.5: Bypass af ikke-eksisterende API-endpoints for at undgå Latency
* **Problem:** Hver kørsel af testen eller pipelinen brugte over 6 sekunders timeout-ventetid på at lave HTTP POST-kald mod `rkr.statistikbank.dk`.
* **Løsning:** Bypass det fejlende HTTP-kald helt og returner den lokale højkvalitets-database direkte. Det fjerner 6 sekunders latency pr. kørsel og rydder logfilerne for falske advarsler.

### 🚀 Læring 6.6: Vercel C-Extension Build Caching & Git Commit Syncing
* **Problem 1 (Build Timeouts):** Tunge Python-pakker med C-udvidelser (`numpy`, `pandas`, `scikit-learn`, `scipy`) tog op mod 8 minutter at kompilere på Vercel under første deployment.
* **Løsning:** Vercel gemmer de kompilerede binære pakker i sin **build cache** efter første gennemførte udrulning. Efterfølgende udrulninger genbruger cachen og tager under 1 minut.
* **Problem 2 (Genbrug af Commit-tekster):** Udrulning direkte via Vercel CLI uden et forudgående git-commit fik Vercel til at genbruge den seneste commit-besked.
* **Løsning:** Lav altid `git commit` og `git push` *før* udrulning.

### ✍️ Læring 6.7: Webredaktionel & UX-Polering (Målgruppe-fokuseret Klarsprog)
* **UX Best Practice:**
  1. Oversæt alle UI-komponenter til konsekvent dansk (*Simuleret nedrisiko*, *Nedside-potentiale*, *Varslingsscore*, *Datakilde-friskhed*).
  2. Formater rå ISO-datostrenge (`2026-07-24`) til læselige datoer (`24. juli 2026`).
  3. Mærk u-implementerede muligheder (f.eks. byerne Aarhus/Odense i dropdown) som `(Kommer snart)` og deaktiver dem frem for at vise tomme fejlpaneler.

### 📉 Læring 6.8: Model Validering & Performance Metrikker (Directional Accuracy vs. $R^2$)
* **Læring:** I 1-step-ahead boligprisprognoser er $R^2$ sagligt set lav (~0,061), fordi kortsigtede prisbevægelser domineres af uobserverede stokastiske makrochok.
* **Best Practice:** Evaluer operationelle modeller på **Directional Accuracy / Hit Rate (>56%)**, **MAPE (<7,58%)**, **MAE (<6,79 pts)** og **Mean Bias Error (+2,92 pts)** frem for udelukkende at se på $R^2$.

### 🌲 Læring 6.9: Random Forest Validering på Små Tidsserier ($N \approx 100$)
* **Læring:** Standard K-Fold cross-validation lækker fremtidige data ind i fortidige forudsigelser.
* **Løsning:** Anvend altid **Walk-Forward Validation (`TimeSeriesSplit`)** kombineret med Out-of-Bag (`oob_score=True`) error estimation og stærk træ-regularisering (`max_depth=4`, `min_samples_leaf=3`) for at forhindre støj-overfitting på små tidsserier.

### 🎲 Læring 6.10: Deterministisk Reproducerbarhed
* **Læring:** Undgå at hævde "100% bit-eksakt reproducerbarhed på tværs af alle platforme".
* **Løsning:** Formuler det som **"deterministisk reproducerbarhed inden for et identisk softwaremiljø"** ved brug af faste pseudo-random seeds (`seed=42`).

### ⚠️ Læring 6.11: Undgå Rå JSX Token-fælder (`>` / `<`) i Vite / Rolldown Build
* **Problem:** Rå `>` eller `<` tegn i JSX brødtekst (f.eks. `(>10%)`) får Vite / Rolldown til at crashe Vercel-buildet med: `[builtin:vite-transform] Unexpected token. Did you mean '{'>'}' or '&gt;'?`.
* **Løsning:** Erstat altid rå sammentællingstegn med HTML-entiteter (`&gt;10%`), JavaScript string-udtryk `({'>'}10%)` eller naturligt sprog (`mere end 10%`).

### ⚡ Læring 6.12: Vercel Static Data Cache Invalidation (`Cache-Control: no-cache`)
* **Problem:** Statiske data-payloads (f.eks. `/data/latest_pipeline.json`) blev gemt aggressivt af Vercels Edge CDN og browserens cache. Det medførte, at brugere så gamle tidsstempler (f.eks. `24. juli`), selvom nattens pipeline var opdateret dags dato (5. august).
* **Løsning:** Tilføj altid eksplikte `Cache-Control` no-cache headers i `vercel.json` for statiske JSON data-endpoints:
  ```json
  {
    "source": "/data/(.*)",
    "headers": [
      { "key": "Cache-Control", "value": "no-cache, no-store, must-revalidate, max-age=0" }
    ]
  }
  ```

### 🧪 Læring 6.13: Integreret Frontend Build-validering i Test Runner
* **Mønster:** For at garantere at frontend-syntaksfejl eller u-escapede JSX-tegn aldrig rammer produktion, bør `manage.sh test` køre en dedikeret unittest (`test_frontend_jsx.py`), som udover syntaksskanning eksekverer `npm run build` i headless-tilstand.

### ⚓ Læring 6.14: Anchored Logit Calibration i Client-side Sandbox Simulatorer
* **Problem:** En klient-side interaktiv risikosimulator (Sandbox) beregnede ML-crash sandsynlighed via en fritstående surrogat-formel. Ved det aktuelle marked evaluerede den til 20,2%, mens den reelle Python Random Forest model på serveren outputtede 37,0%. Det udløste forvirrende uoverensstemmelser og et falsk baseline-delta (-16,8%).
* **Løsning:** Forankr altid klient-side surrogat-modeller i den reelle server-baseline via logit-transformation:
  \[ \text{baseLogit} = \ln\left(\frac{P_{live}}{1 - P_{live}}\right) \]
  Dermed evaluerer simuleringen til eksakt 37,0% ($P_{live}$) ved baseline ($0,0\%$ delta), og justeringer af slidere skalerer logit-afvigelsen ($\Delta Z$) direkte fra det sande udgangspunkt.

### 🎭 Læring 6.15: Automated Playwright E2E Visual Inspection & Modal State Handling
* **Mønster:** Playwright E2E visuelle tests mod SPA'er (React/Vite) skal tage højde for async data-loading (`fetch('/data/latest_pipeline.json')`) og første-besøgs onboarding modals.
* **Best Practice:** Sæt enten `localStorage.setItem('cph_housing_onboarded', 'true')` via `page.add_init_script(...)` før navigation for deterministiske visuelle skud, eller vent eksplicit på modal-lukning (`page.get_by_role("button", name="...").click()`). Brug altid `page.wait_for_selector("h2", timeout=...)` for at sikre, at async React hydration er fully mounted før dom-asserts.

### 🛠️ Læring 6.16: Vite / Rolldown Style Property Syntax (`fontWeight: 800`)
* **Problem:** En manglende kolonsyntaks i et inline CSS JS-objekt (`fontWeight 800` i stedet for `fontWeight: 800`) fejlede rolldown-transformeringen under `npm run build` med fejl: `[builtin:vite-transform] Expected , or } but found decimal`.
* **Løsning:** Integrer altid `test_frontend_jsx.py` i `./manage.sh test` for at fange syntaksfejl i inline stilobjekter og JSX tegn før push.

### 💡 Læring 6.17: UX Onboarding, Metodenoter & 100% Dansk Sprog-konsistens
* **Mønster:** Avancerede finansielle/kvantitative dashboards risikerer at fremstå uforståelige for målgruppen uden onboarding.
* **Best Practice:** Tilføj 1) En automatisk velkomst-modal (`OnboardingModal`) ved første besøg, 2) Et dedikeret metodenotat (`MethodologyModal`) som dokumenterer model-arkitektur, backtest hit-rate (56,2%) og data lineage, 3) 100% dansk sprog-konsistens på alle labels og tooltips, og 4) En juridisk ansvarsfraskrivelse i footeren.

---

## 7. Kvalitetssikring (PO Launch Checklist)

Før udrulning til produktion skal følgende tjekliste altid gennemføres:

- [x] **Sprogkontrol**: Er alle knapper, nedtællere, fejlbeskeder og ledetekster på det valgte sprog (dansk)?
- [x] **Responsivitet**: Er alle elementer testet på mobil (375px), tablet (768px) og desktop (1200px+)?
- [x] **Performance Check**: Er der ingen enkeltfiler over 1-2 MB i `public/` mappen?
- [x] **Touch & Interaktivitet**: Er dobbelt-tap zoom deaktiveret på hurtige klik-flader?
- [x] **Fallback & Error Boundaries**: Er der poster-billeder på videoer og meningsfulde fejlmeddelelser ved manglende netværk?
- [x] **No-Cache Data Headers**: Er `vercel.json` konfigureret med `no-cache` for statiske data-JSON filer?
- [x] **JSX Build Validation**: Er `npm run build` verifieret uden unescaped JSX-tokens?
- [x] **Anchored Logit Calibration**: Er risikosimulatorer kalibreret 1-til-1 mod serverens baseline?
- [x] **Playwright E2E Visual Inspection**: Er visuelle skud verificeret uden konsolfejl eller layout-skift?

---
*Filen gemt som en del af det globale læringskatalog.*
