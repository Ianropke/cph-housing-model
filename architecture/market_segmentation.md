# Copenhagen Housing Market — Segmentation Model

> **Version**: 0.1.0  
> **Last Updated**: 2026-06-11  
> **Depends on**: `architecture/market_framework.md`  
> **MCP Server**: `CphHousingModel`

---

## 1. Segmentation Rationale

A metro-wide price index obscures the dynamics that matter for forecasting. Copenhagen's housing market is **structurally heterogeneous** along two orthogonal axes:

1. **Asset type** — apartments and houses have different buyer profiles, financing structures, supply elasticities, and price dynamics.
2. **Geography** — location determines substitution relationships, supply pipelines, demographic composition, and infrastructure exposure.

The model segments along both axes simultaneously, producing a matrix of **(type × zone)** cells, each with its own driver calibration and forecast.

---

## 2. Asset Type Segmentation

### 2.1 Apartments (Ejerlejligheder)

| Characteristic | Detail |
|---|---|
| **Dominant buyer** | Young professionals (25–35), single-person households, investors, downsizers |
| **Typical financing** | Higher LTV (often 80%+), higher IO share, rate-sensitive |
| **Supply elasticity** | Very low in existing stock (heritage, density limits); moderate in new development zones |
| **Price driver weighting** | Credit Conditions ↑↑, Expectations ↑↑, Supply Constraints ↑, Demographics ↑ |
| **Volatility profile** | Higher — leveraged buyers amplify rate sensitivity; expectations-driven momentum |
| **Key metric** | Price per m² (kr/m²) — standardised for comparability across sizes |

**Apartment sub-types** (tracked but not separately modelled in v0.1):

| Sub-type | Notes |
|---|---|
| Pre-war (før 1940) | Heritage buildings; fixed stock; renovation premium |
| Post-war (1940–1980) | Concrete blocks; lower desirability; lower price floor |
| Modern (1980–2010) | Mixed; often andelsbolig conversions |
| New-build (2010+) | Developer product in Nordhavn/Sydhavn/Ørestad; distinct pricing |

---

### 2.2 Houses (Villaer & Rækkehuse)

| Characteristic | Detail |
|---|---|
| **Dominant buyer** | Families (30–45), dual-income households, space-seekers |
| **Typical financing** | Moderate LTV; higher absolute debt; more amortising loans |
| **Supply elasticity** | Near-zero in established areas; low even in suburbs (land scarcity) |
| **Price driver weighting** | Purchasing Power ↑↑, Demographics ↑↑, Local Substitution ↑, Credit Conditions ↑ |
| **Volatility profile** | Lower — larger down payments, longer holding periods, less speculative |
| **Key metric** | Total price (kr) and price per m² — both tracked; land value separated where possible |

**House sub-types**:

| Sub-type | Notes |
|---|---|
| Detached villa (parcelhus) | Primarily suburban; largest ticket; garden premium |
| Row house (rækkehus) | Transition product between apartment and villa; family starter |
| Townhouse (byhus) | Central locations; scarce; heritage value |

---

### 2.3 Type Interaction: The Substitution Ladder

```
┌──────────────────────────────────────────────────────────┐
│                  SUBSTITUTION LADDER                      │
│                                                          │
│  Central apartment ←→ Frederiksberg apartment            │
│         ↕                      ↕                         │
│  Bridge Quarter apartment ←→ Near-suburb rækkehus        │
│         ↕                      ↕                         │
│  Suburban apartment ←→ Suburban parcelhus                 │
│                                                          │
│  ←→  Geographic substitution (same type)                 │
│  ↕   Type substitution (same approximate location)       │
└──────────────────────────────────────────────────────────┘
```

When the price spread between adjacent rungs on the ladder exceeds ~1.5σ of its historical distribution, substitution flows intensify and act as a mean-reverting force.

---

## 3. Geographic Segmentation

### 3.1 Zone Map

```
                    ┌─────────────────────┐
                    │   SURROUNDING       │
                    │   MUNICIPALITIES    │
                    │  (Gentofte, Lyngby, │
                    │   Gladsaxe,         │
                    │   Hvidovre, Tårnby) │
                    │                     │
                    │  ┌───────────────┐  │
                    │  │ BRIDGE        │  │
                    │  │ QUARTERS      │  │
                    │  │ (Valby,       │  │
                    │  │  Vanløse,     │  │
                    │  │  Amager Vest, │  │
                    │  │  Brønshøj)    │  │
                    │  │               │  │
                    │  │ ┌───────────┐ │  │
                    │  │ │ CENTRAL   │ │  │
                    │  │ │ (K,V,N,Ø) │ │  │
                    │  │ └───────────┘ │  │
                    │  │               │  │
                    │  │ ┌───────────┐ │  │
                    │  │ │FREDERIKS- │ │  │
                    │  │ │BERG       │ │  │
                    │  │ └───────────┘ │  │
                    │  │               │  │
                    │  └───────────────┘  │
                    │                     │
                    │  ╔═══════════════╗  │
                    │  ║ NEW DEV AREAS ║  │
                    │  ║ (Nordhavn,    ║  │
                    │  ║  Sydhavn)     ║  │
                    │  ╚═══════════════╝  │
                    └─────────────────────┘
```

---

### 3.2 Zone Definitions

#### Zone 1: Central Copenhagen (K, V, N, Ø)

| Attribute | Detail |
|---|---|
| **Postal codes** | 1000–1499 (K), 1500–1799 (V), 2200 (N), 2100 (Ø) |
| **Character** | Dense urban core; heritage buildings; mixed commercial/residential |
| **Dominant type** | Apartments (>95% of transactions) |
| **Supply elasticity** | Near-zero — virtually no buildable land; heritage protection |
| **Key driver emphasis** | Credit Conditions, Expectations, Supply Constraints |
| **Benchmark index** | Ejerlejlighed kr/m², weighted by postal code |

**Sub-zones**:

| Code | Name | Profile |
|---|---|---|
| **K** (København K / Indre By) | Inner City | Highest price/m²; tourist area; small units; investor-heavy |
| **V** (Vesterbro) | Vesterbro | Gentrified; young professional; café culture; pre-war stock |
| **N** (Nørrebro) | Nørrebro | Diverse; university-adjacent; rapid appreciation post-2015 |
| **Ø** (Østerbro) | Østerbro | Family-oriented; parks; highest-quality pre-war apartments |

---

#### Zone 2: Frederiksberg

| Attribute | Detail |
|---|---|
| **Postal codes** | 1800–1999, 2000 |
| **Character** | Independent municipality enclave within Copenhagen; high-quality residential |
| **Dominant type** | Apartments (~85%), with some villaer in western Frederiksberg |
| **Supply elasticity** | Extremely low — fully built out; strict local planning |
| **Key driver emphasis** | Purchasing Power, Local Substitution (vs. Østerbro / Vesterbro) |
| **Benchmark index** | Ejerlejlighed kr/m² |

**Structural note**: Frederiksberg Kommune operates its own planning authority, creating regulatory divergence from Copenhagen Kommune. Property tax rates, school quality, and municipal services differ, making Frederiksberg a distinct demand segment despite geographic contiguity.

---

#### Zone 3: New Development Areas (Nordhavn, Sydhavn)

| Attribute | Detail |
|---|---|
| **Postal codes** | 2150 (Nordhavn), parts of 2450 (Sydhavn / Teglholmen / Enghave Brygge) |
| **Character** | Large-scale masterplanned districts on former industrial/harbour land |
| **Dominant type** | New-build apartments (100% in Nordhavn; ~90% in Sydhavn) |
| **Supply elasticity** | **High in the medium term** — large pipeline of planned but unbuilt phases |
| **Key driver emphasis** | Supply pipeline (completion schedule), Demographics (absorption rate), Expectations |
| **Benchmark index** | New-build ejerlejlighed kr/m² (developer list price vs. resale) |

**Critical dynamics**:

- **Pipeline overshoot risk**: Nordhavn and Sydhavn together represent the largest supply injection into Copenhagen in decades. Simultaneous delivery of multiple phases can temporarily depress local prices even when metro-wide demand is strong.
- **Price discovery**: New-build pricing is set by developers using cost-plus and comparable-based models, creating a **distinct price formation mechanism** vs. the bid-driven resale market.
- **Maturation trajectory**: As districts mature (schools, retail, transit connections established), they transition from speculative new-development pricing toward neighbourhood-integrated pricing. Nordhavn is further along this curve than Sydhavn.
- **Metro dependency**: Both zones are critically dependent on M4 (Sydhavn) and M3/M4 Nordhavn extensions for commute-time competitiveness. Delays in transit delivery directly impact absorption and pricing.

---

#### Zone 4: Bridge Quarters (Brokvarterer & Transition Zones)

| Attribute | Detail |
|---|---|
| **Areas** | Valby, Vanløse, Amager (Vest / Øst), Brønshøj-Husum, Bispebjerg |
| **Postal codes** | 2500, 2720, 2300, 2400, 2700, 2400 |
| **Character** | Inner suburban ring; mix of pre-war and post-war stock; improving infrastructure |
| **Dominant type** | Mixed — apartments in denser nodes, rækkehuse and villaer in residential pockets |
| **Supply elasticity** | Low-to-moderate — some infill and conversion potential |
| **Key driver emphasis** | Local Substitution (price spread vs. Central), Demographics (family in-migration) |
| **Benchmark index** | Blended kr/m² by type; tracked separately for apartments and houses |

**Strategic role in the model**: Bridge Quarters are the **primary substitution release valve** for Central Copenhagen. When central prices spike, demand flows outward through the Bridge Quarters before reaching surrounding municipalities. The price spread (Central / Bridge Quarter) is a key model input for the Local Substitution driver.

**Infrastructure sensitivity**: Metro Cityringen (opened 2019) permanently re-priced parts of Amager and Valby. Future BRT / light rail connections will have similar effects. The model must track infrastructure project timelines as **exogenous structural breaks** in Bridge Quarter pricing.

---

#### Zone 5: Surrounding Municipalities

| Attribute | Detail |
|---|---|
| **Key municipalities** | Gentofte, Lyngby-Taarbæk, Gladsaxe, Herlev, Rødovre, Hvidovre, Tårnby, Dragør |
| **Character** | Suburban; predominantly low-density residential; municipal independence |
| **Dominant type** | Houses (parcelhuse, rækkehuse) ~60%; apartments ~40% (varies by municipality) |
| **Supply elasticity** | Low — established suburbs with limited infill; some densification near S-tog stations |
| **Key driver emphasis** | Purchasing Power (family budgets), Demographics (family formation), Credit Conditions |
| **Benchmark index** | Parcelhus total price and kr/m²; tracked per municipality |

**Heterogeneity warning**: This zone is internally diverse. Gentofte (affluent, high-price) and Hvidovre (middle-income, lower-price) have very different buyer profiles and price dynamics. The model tracks each municipality individually but aggregates to zone level for substitution analysis.

**Commute-time anchoring**: Prices in surrounding municipalities are fundamentally anchored to commute time to central Copenhagen employment zones. S-tog proximity is the dominant location premium factor, creating a **distance-decay pricing gradient** that the model exploits for substitution analysis.

---

## 4. Segmentation Matrix

The full model operates on the cross-product of **type × zone**, producing the following cell structure:

| | Central (K,V,N,Ø) | Frederiksberg | New Dev (Nordhavn, Sydhavn) | Bridge Quarters | Surrounding Municipalities |
|---|---|---|---|---|---|
| **Apartments** | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Secondary | ✅ Secondary |
| **Houses** | ⬜ Negligible | ⬜ Minor | ⬜ Negligible | ✅ Secondary | ✅ Primary |

- **✅ Primary**: Sufficient transaction volume for standalone modelling (>50 transactions/quarter)
- **✅ Secondary**: Modelled but with wider confidence intervals; may require pooling
- **⬜ Minor/Negligible**: Tracked for completeness but not independently forecast

---

## 5. Forecast Horizon × Segment Mapping

Different segments respond to different horizons with different sensitivity. The table below maps which **forecast horizon** is most decision-relevant for each segment:

### 5.1 Six-Month Horizon (Momentum / Flow)

> *Driven by: momentum, active supply, time-on-market*

| Segment | Sensitivity | Rationale |
|---|---|---|
| Central apartments | **Very High** | Highest liquidity; fastest expectation transmission; trend-followers dominate |
| Frederiksberg apartments | **High** | Tight market; low inventory amplifies momentum signals |
| New Development apartments | **Moderate** | Developer pricing is stickier; resale market is thin |
| Bridge Quarter apartments | **High** | Substitution inflows from central create lagged momentum |
| Bridge Quarter houses | **Moderate** | Lower transaction volume; slower price discovery |
| Surrounding municipalities houses | **Low** | Thinner markets; seasonal noise dominates at 6m |

**Key 6-month indicators per segment**:

```
Central apartments    → months-of-supply, sale-to-list ratio, trailing 3m return
Frederiksberg         → new listings flow, days-on-market
New Development       → developer price revisions, pre-sale absorption rate
Bridge Quarters       → Central-to-Bridge price spread velocity
Surrounding munic.    → (not primary horizon; use 12m)
```

---

### 5.2 Twelve-Month Horizon (Affordability / Credit)

> *Driven by: affordability ratios, interest rates, credit conditions*

| Segment | Sensitivity | Rationale |
|---|---|---|
| Central apartments | **High** | Highest leverage; IO-heavy; rate changes hit hard |
| Frederiksberg apartments | **High** | Similar financing profile to Central |
| New Development apartments | **Very High** | Buyers are rate-marginal; developer financing offers mask but don't eliminate rate sensitivity |
| Bridge Quarter apartments | **High** | Affordability-driven buyers; rate-sensitive first-time purchasers |
| Bridge Quarter houses | **High** | Family budgets stretched; DSI ratio is binding constraint |
| Surrounding municipalities houses | **Very High** | Most rate-sensitive segment — highest absolute debt, family-budget constrained |

**Key 12-month indicators per segment**:

```
All segments          → forward mortgage rate curve, Nationalbanken lending survey
Apartments            → DSI ratio for median apartment in segment
Houses                → price-to-household-income for dual-income family
New Development       → developer pre-sale velocity vs. pipeline delivery schedule
```

---

### 5.3 Twenty-Four-Month Horizon (Structural / Demographic)

> *Driven by: structural demography, new construction pipeline*

| Segment | Sensitivity | Rationale |
|---|---|---|
| Central apartments | **Moderate** | Demand is structurally robust; supply is zero; prices grind higher unless policy shock |
| Frederiksberg apartments | **Moderate** | Similar structural dynamics to Central |
| New Development apartments | **Very High** | Pipeline delivery is THE dominant 24m variable; overshoot risk is concentrated here |
| Bridge Quarter apartments | **High** | Beneficiary of central displacement; demographic tailwind from family formation |
| Bridge Quarter houses | **High** | Family formation directly drives demand; school catchment effects |
| Surrounding municipalities houses | **High** | Long-run population growth and infrastructure investment determine trajectory |

**Key 24-month indicators per segment**:

```
New Development       → permitted-but-unbuilt units; completion schedule by quarter
Central / Frb        → net migration trend; single-household formation rate
Bridge / Suburban     → age 28-35 cohort size; family formation rate
All segments          → legislative pipeline (tax reform, LTV changes, rent regulation)
```

---

## 6. Data Schema Contract

Each segment cell in the matrix exposes the following standardised interface to the `CphHousingModel` MCP server:

```
segment_id: "{type}_{zone}"
  e.g., "apartment_central_k", "house_surrounding_gentofte"

get_price_index(segment_id, frequency) → time series
get_transaction_volume(segment_id, frequency) → time series  
get_inventory(segment_id) → current snapshot
get_driver_features(segment_id, horizon) → feature vector
get_substitution_spread(segment_id, reference_segment_id) → spread series
```

---

## 7. Segment Lifecycle & Reclassification

Segments are **not static**. The model must handle:

1. **New Development → Bridge Quarter transition**: As Nordhavn and Sydhavn mature (10+ years post-first-delivery, established retail/schools, >70% build-out), they transition from "New Development" pricing dynamics to "Bridge Quarter" dynamics. The model should track maturation indicators and flag when reclassification is warranted.

2. **Bridge Quarter → Central creep**: Gentrification and metro connectivity can cause Bridge Quarter areas (e.g., parts of Amager Vest post-Cityringen) to exhibit Central-like pricing dynamics. Monitor via price convergence and buyer demographic shift.

3. **New zone emergence**: Future masterplan areas (e.g., Refshaleøen, Lynetteholmen) will require new segment creation when they enter the development pipeline. The model architecture must support dynamic segment addition.
