# Agent Operating Contract

Dette repository indeholder Copenhagen Housing Model: en Python-baseret boligmarkedsmodel og en statisk React/Vite-dashboard-app for København og Frederiksberg. De vigtigste korrekthedskrav er, at beregninger kan spores til deres kilder, at outputtyper ikke forveksles med sandsynligheder, og at manglende eller ugyldige data ikke skjules med fabrikerede tal.

## Autoritative kilder

Læs kun de dokumenter, der er relevante for opgaven, men brug denne prioritering:

1. `docs/model_governance.md` er normativ for outputsemantik, crash-event-definition, data lineage og produktionssikkerhed.
2. `config/scenarios.yaml` sammen med `server/config_loader.py` er den kanoniske kilde til scenarier og ensemblevægte. Duplikér ikke scenarier i frontend eller Python.
3. `server/`, `scripts/`, tests og `.github/workflows/daily_update.yml` beskriver den faktiske implementering, pipeline og quality gates.
4. `architecture/` beskriver den teoretiske og ønskede modelarkitektur. `cph_housing_project_review_spec.md` er en review-/designspecifikation, ikke bevis på at alle beskrevne kontroller findes i koden.
5. `manage.sh`, `README.md` og `dashboard/README.md` er onboarding- og driftsvejledning. Kontrollér altid kommandoer, URLs og fallbackbeskrivelser mod kode og workflow; de indeholder historiske oplysninger.
6. `GLOBAL_CODE_QA.md` er historiske engineering-learnings. Brug mønstrene, men antag ikke at alle nævnte kontroller er implementeret.

Hvis dokumenter og kode modsiger hinanden, må konflikten ikke skjules. Bevar governance-semantikken, dokumentér afvigelsen, og afklar større domæneændringer før implementering. Genererede payloads og daglige rapporter er artefakter, ikke kilder til modelregler.

## Arkitektoniske invariants

- Produktions-Vercel-appen er en statisk frontend. Python-kald via `dashboard/vite.config.js` er kun lokal udviklingsintegration; de må ikke behandles som produktions-API.
- `scripts/daily_pipeline.py` henter kildedata, beregner modeloutput og skriver dashboard-payloads. `dashboard/public/data/latest_pipeline.json` og `dashboard/src/data/housingData.js` er genererede filer og må ikke redigeres manuelt for at ændre tal.
- `config/scenarios.yaml` ejer scenario- og ensemblevægte. En `ensemble_weight` er en model-/analystvægt, ikke en empirisk sandsynlighed.
- Hold modelgrænserne adskilt: ML crash probability er en sandsynlighed i `[0, 1]`; EWI-score er en advarselsskala; Market Risk Score er et indeks på 0–100. Ingen af de sidste to må præsenteres som procentchancer.
- Der er ingen database eller migrationslag i det nuværende repository. Introducer ikke persistent schema/state uden en separat design- og migrationsplan.

## Data integrity og provenance

- Autoritative kilder er DST, Finans Danmarks Statistikbank/RKR og Boliga, som angivet i pipeline-koden. Bevar kildeidentitet, observationens periode, retrieval-tidspunkt og status adskilt.
- `retrieved_at` må aldrig vises som observationstidspunkt. Nye payloadfelter skal følge lineage-reglerne i `docs/model_governance.md`.
- En fejlet eller ufuldstændig autoritativ kilde må ikke erstattes af en lokal mock, syntetisk værdi eller urelateret kilde. Pipeline skal fejle lukket eller udgive en eksplicit unavailable/stale-status.
- Retries, timeouts og user agents for eksterne read-only-kilder skal være begrænsede og dokumenterede. Respektér upstream-rate limits.
- ML-modellen og historiske features må ikke kaldes empirisk validerede, medmindre out-of-sample-validering faktisk er kørt. `tests/test_event_backtest.py` markerer aktuelt den deployede model som ikke valideret, og `scripts/train_ews_model.py` træner kun på det point-in-time live-featurepanel og fejler lukket ved utilstrækkelig historik.

## Implementerede correctness-gates

Følgende gates er en del af den nuværende implementering og skal bevares ved ændringer:

- `scripts/daily_pipeline.py` sender den samme live `dst_data` til forecast og EWI. `scripts/payload_validation.py` afviser manglende schema, stale/live-status og periodemismatch mellem DST og forecast, og der findes regressionstests for alignment.
- `CityProvider` validerer schema, freshness og `market_data_status`. `App.jsx` og simulatoren viser eksplicit unavailable/stale eller ML-unavailable-status; de bruger ikke fallbacktal som friske data.
- `config/ews_ml_model.skops` og proxy-baserede historiske ML-kurver er isoleret fra produktion. ML-sandsynlighed er `null`, indtil live-feature out-of-sample-validering består.
- `scripts/daily_pipeline.py` arkiverer live ML-features i `data/ml_feature_snapshots.jsonl`. `scripts/train_ews_model.py` må kun bruge dette point-in-time-panel, skal deduplikere gentagne kvartalsvintages før evaluering og må ikke genindføre syntetiske træningsdata.
- `.github/workflows/daily_update.yml` kører payload-gate, crash-probability-kontrakt, build, lint og testdriver. Sentry og andre kontroller, der kun omtales i reviewspecifikationen, er stadig ikke aktive kontroller.

## Eksterne tjenester og secrets

- Commit aldrig tokens, credentials, `.env`-filer eller andre secrets. Brug godkendte miljøvariabler/Vercel- eller GitHub-secrets.
- Ændr ikke auth-, deploy- eller workflow-permissions uden særskilt begrundelse. CI-workflowet har bevidst `contents: write`, fordi det publicerer genererede data.
- Eksponér ikke rå upstream-fejl eller interne stack traces i produktions-UI. Log tekniske detaljer internt og giv brugeren en forståelig status.

## Arbejdsform og scope

For substantielle opgaver: forstå repositoryet, afgræns scope og acceptance criteria, lav en kort plan ved arkitektur-/data-/sikkerhedsændringer, implementér mindst muligt, valider, gennemgå diffen og rapportér evidens. Undgå opportunistiske dependency-opgraderinger, store formatteringer, nye frameworks og redesign af urelaterede moduler.

Opdatér dokumentation, når en ændring ændrer en varig arkitekturregel, et domæne-/outputcontract, pipeline-drift, configuration eller validation. Tilføj kun en scoped `AGENTS.md`, hvis en subsystemregel ikke kan dækkes klart her; frontend og data/modeling er de oplagte kandidater, men de er ikke nødvendige endnu.

## Kommandoer og definition of done

Kør fra repository-roden:

```bash
# Lokal pipeline med live kilder
./manage.sh update

# Repositoryets samlede testdriver; RUN_VISUAL_TESTS=0 matcher CI
RUN_VISUAL_TESTS=0 ./manage.sh test

# Den separate pytest-baserede sandsynlighedsvalidering
pytest tests/test_crash_probability_validation.py

# Frontend build og lint
(cd dashboard && npm run build)
(cd dashboard && npm run lint)

# Sidste diffkontrol
git diff --check
```

Ved ændringer i brugerfladen skal den faktiske rendered flow verificeres med Playwright, når miljøet tillader det; compilation alene er ikke tilstrækkeligt. Ved data- eller modelændringer skal relevante data-integritets-, EWI-, forecast-, backtest- og event-valideringer køres. Hvis en kontrol ikke kan køres, rapportér præcist hvilken, hvorfor og hvilken residual risiko der står tilbage.

Før commit: inspicér `git status`, `git diff --stat` og den fulde relevante diff. Stag kun filer, der hører til opgaven. En ændring er først færdig, når den observerede adfærd, regressionstests, build/lint-resultater og eventuelle eksterne deploy-/pipeline-statusser er rapporteret faktuelt.
