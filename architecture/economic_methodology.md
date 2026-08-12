# Økonomisk & Matematisk Metodedokumentation: CPH Housing Market Model

> **Implementation note (2026):** This methodology document contains the economic derivations. For current EWI weights, source lineage, payload validation and ML publication status, use `docs/model_governance.md` and the production code in `server/cph_housing_server.py`.

Dette dokument indeholder en dybdegående dokumentation af de økonomiske teorier, matematiske formler og empiriske antagelser, der ligger til grund for beregningerne i Københavns Boligmarkedsmodel.

---

## 1. Teoretisk Fundament (Theoretical Foundation)

### 1.1 Brugeromkostningsmodellen (User Cost of Housing)
Modellen er teoretisk forankret i den klassiske **User Cost-tilgang** (oprindeligt formuleret af Poterba, 1984, og løbende tilpasset af OECD samt Danmarks Nationalbank). I boligøkonomisk teori repræsenterer ejeromkostningen (*User Cost of Housing*) den reelle løbende pris, en forbruger betaler for at forbruge boligydelser (housing services) i én periode ved at eje frem for at leje.

I en friktionsfri ligevægtstilstand skal omkostningen ved at eje svare til omkostningen ved at leje:

$$\text{User Cost} \approx \text{Rent (Leje)}$$

Hvis brugeromkostningen er væsentligt lavere end markedslejen, er der et stærkt økonomisk incitament til at købe, hvilket presser ejerpriserne op. Omvendt, hvis brugeromkostningen overstiger markedslejen, vil efterspørgslen flytte mod lejeboliger, hvilket tvinger ejerboligpriserne ned.

### 1.2 Udskillelse af Prisforventninger ($\pi_e$) og Cirkulær Logik
I den standardiserede brugeromkostningsformel indgår de forventede prisstigninger ($\pi_e$) som et direkte fradrag:

$$UC_{standard} = r(1 - \tau) + \tau_p + \dots - \pi_e$$

Dette skaber et **metodisk paradoks** under markedsbobler:
1. Priserne stiger kraftigt $\rightarrow$ Køberne danner ekstrapolative (momentum-drevne) prisforventninger (høj $\pi_e$).
2. Den høje $\pi_e$ fratrækkes i formlen $\rightarrow$ Brugeromkostningen falder (ofte til under nul).
3. Modellen indikerer fejlagtigt, at det er "billigt" og fundamentalt sundt at købe bolig på trods af historisk høje prisniveauer.
4. Dette forstærker den spekulative feedback-sløjfe.

For at løse dette problem introducerer **Version 3.0** begrebet **Fundamental User Cost of Housing ($UC_{fund}$)**. Her adskilles prisforventningerne helt fra den fundamentale ejeromkostningsrate og behandles i stedet som et selvstændigt markedssentiment-signal. Dette sikrer en objektiv måling af de faktiske løbende omkostninger uden forstyrrende cirkulær adfærdslogik.

---

## 2. Matematisk Formel & Parameterfastsættelse

De fundamentale ejeromkostninger beregnes efter følgende formel:

$$UC_{fund} = \left( r \cdot (1 - \tau_r) + \tau_p + \delta + rp \right) \cdot P$$

Hvor:
* **$P$**: Ejendommens markedsværdi (referenceværdi sat til 3.000.000 DKK).
* **$r$**: Den nominelle realkreditrente (inklusiv bidragssats).
* **$\tau_r$**: Den effektive (blended) skatteværdi af rentefradraget.
* **$\tau_p$**: Den løbende ejendomsskattesats (ejendomsværdiskat + grundskyld).
* **$\delta$**: Den fysiske vedligeholdelses- og afskrivningsrate.
* **$rp$**: Den dynamiske risikopræmie.

---

### 2.1 Dynamisk Rentefradrag ($\tau_r$) med asymmetrisk beskatning
Danske skatteregler foreskriver en asymmetrisk (trinvis) fradragssats for renteudgifter. Skatteværdien af rentefradraget er:
* **$33,0\%$** for renteudgifter op til en fastsat grænse.
* **$25,0\%$** for renteudgifter ud over denne grænse.

Grænsen (tærskelværdien $T$) udgør:
* **$50.000\text{ DKK}$** for enlige ($is\_couple = \text{False}$).
* **$100.000\text{ DKK}$** for ægtepar ($is\_couple = \text{True}$).

Under antagelse af en belåningsgrad på **$80\%$ (LTV = 80%)** er den samlede realkreditgæld $D = 0,80 \cdot P$. De årlige renteudgifter udgør $I = D \cdot r$.

Den effektive blendede skattefradragssats $\tau_r$ beregnes som:

$$\tau_r = \begin{cases} 
0,33 & \text{hvis } I \le T \\
\frac{T \cdot 0,33 + (I - T) \cdot 0,25}{I} & \text{hvis } I > T 
\end{cases}$$

Dette sikrer, at store lån (eller lån i højrenteperioder) straffes med en lavere gennemsnitlig fradragsværdi, hvilket afspejler den reelle likviditetsbelastning for husholdningerne.

---

### 2.2 Segment-specifik Vedligeholdelse & Afskrivning ($\delta$)
Fysisk slid og løbende renoveringsomkostninger er ikke ens på tværs af boligtyper. Modellen differentierer vedligeholdelsesraten ($\delta$) baseret på bygningstype, gennemsnitlig alder og ejerstruktur:

1. **Enfamiliehuse (`copenhagen_houses`): $\delta = 1,9\%$ p.a.**  
   Enfamiliehuse (typisk placeret i Københavns omegn) har en højere direkte vedligeholdelsesbyrde (tag, facade, have, separat varmeinstallation), som fuldt ud bæres af den enkelte ejer.
2. **Ejerlejligheder på Frederiksberg (`frederiksberg_apartments`): $\delta = 1,7\%$ p.a.**  
   Ældre bygningsmasse med høje krav til vedligeholdelse og bevaringsværdige detaljer.
3. **Ejerlejligheder i København City (`copenhagen_apartments`): $\delta = 1,6\%$ p.a.**  
   En kombination af nyere byggeri (Ørestad, Havnestæderne) og etablerede ejerforeninger, hvor fælles opsparing i foreningen udjævner de akutte renoveringsomkostninger.

---

### 2.3 Dynamisk Ejendomsskat ($\tau_p$) under 2024-skattereformen
Med boligskattereformen fra 2024 er ejendomsbeskatningen (ejendomsværdiskat og grundskyld) bundet tættere til den løbende offentlige ejendomsvurdering. 

For at modellere dette uden at afvente forsinkede offentlige vurderinger, anvender modellen en dynamisk skatteregulering baseret på det seneste prisindeks fra Danmarks Statistik (EJ56):

$$\tau_p = \text{base\_rate} + 0,0003 \cdot \left( \frac{\text{EJ56\_Index}}{100} - 1 \right)$$

Hvor basissatserne ($\text{base\_rate}$) afspejler det gennemsnitlige skatteniveau i 2024:
* **København Ejerlejligheder**: $0,95\%$
* **Frederiksberg Ejerlejligheder**: $0,91\%$
* **København Omegn Huse**: $0,88\%$

Når prisindekset stiger over basisniveauet ($100$ svarende til år 2006), øges den effektive ejendomsskatterate marginalt for at simulere den løbende skattestigning på de urealiserede gevinster.

---

### 2.4 Dynamisk Risikopræmie ($rp$)
Risikopræmien kompenserer boligejeren for at binde kapital i et illikvidt aktiv med høj koncentrationsrisiko (sammenlignet med en diversificeret aktie- eller obligationsportefølje). 

Risikopræmien er dynamisk og afhænger af renteniveauet (alternativomkostningen) og markedsvolatiliteten ($\sigma$):

$$rp = 0,008 + 0,05 \cdot (r - 0,02) + 0,01 \cdot \sigma$$

* **Rente-følsomhed ($0,05 \cdot (r - 2\%)$)**: Når realkreditrenten stiger, øges kravene til risikopræmien, da investorer kan opnå et højere risikofrit afkast på statsobligationer.
* **Volatilitets-følsomhed ($0,01 \cdot \sigma$)**: Høj historisk prisusikkerhed i markedet øger den krævede risikopræmie som kompensation for den øgede tabsrisiko ved et potentielt tvangssalg.

---

## 3. Cash Flow (Likviditet) vs. User Cost (Økonomisk pris)

Modellen skelner skarpt mellem de **samlede månedlige likviditetsudgifter (Cash Flow)** og de **fundamentale ejeromkostninger (User Cost)**:

### 3.1 Månedligt Cash Flow (Nettoydelse)
Cash flowet måler den direkte månedlige likviditetsbelastning og afhænger af, om lånet er med afdrag eller afdragsfrit:

$$\text{Net Monthly Payment} = \frac{\text{Interest Expense} \cdot (1 - \tau_r) + \text{Amortisation} + \text{Property Tax} + \text{Maintenance}}{12}$$

Amortisationsraten (afdraget) beregnes som en fast procentdel af gælden (typisk $2,0\%$ til $3,0\%$ for lån med afdrag). Selvom afdraget er en likviditetsudgift, betragtes det økonomisk set som opsparing (overførsel af likvider til friværdi) og indgår derfor **ikke** som en nettoudgift i User Cost.

---

## 4. Early Warning System (EWS) Scoring Logik

Kompositscoren (Composite Score) beregnes som den vægtede sum af de 8 ledende indikatorers individuelle risikoscores ($S_i \in \{0, 1, 3\}$ for henholdsvis grøn, gul og rød status):

$$\text{Composite Score} = \sum_{i=1}^{8} w_i \cdot S_i$$

Hvor de empiriske vægte ($w_i$) er fastsat som følger:

| Indikator | Navn | Vægt ($w_i$) | Begrundelse |
|---|---|---|---|
| **EWI-1** | Price-to-Wage Spread | 1,4 | Kritisk mål for affordability-erosion. |
| **EWI-2** | Months of Supply | 1,2 | Direkte indikator for udbudssqueeze/mangel. |
| **EWI-3** | Volume-Price Divergence | 1,0 | Fanger faldende markedsbredde (likviditetssvigt). |
| **EWI-4** | Active Price Cuts | 1,3 | Fanger adfærdsændringer hos sælgere. |
| **EWI-5** | Time-on-Market (Z-score) | 0,8 | Vigtig, men ofte stærkt bagefterhaling. |
| **EWI-6** | Price-to-Rent Ratio | 1,1 | Måler den relative prissætning mod udlejning. |
| **EWI-7** | Interest-Only Share | 0,7 | Indikerer sårbarhed over for finansiel gearing. |
| **EWI-8** | Debt Service Ratio (DSR) | 1,5 | Det stærkeste mål for husholdningernes betalingsevne. |

Den maksimale teoretiske score er **$27,0\text{ point}$** (hvor alle 8 indikatorer er RØDE, dvs. $3 \cdot 9,0$ i sum af vægte).

---

## 5. Trin-for-trin Beregningseksempler

### Eksempel 1: København Ejerlejligheder (Baseline 12m)
* **Input-parametre**:
  * Ejendomsværdi $P = 3.000.000\text{ DKK}$
  * Rente $r = 3,7\%$ ($0,037$)
  * Segment: `copenhagen_apartments` (EJ56 indeks = $129,2$)
  * Husholdning: Ægtepar ($is\_couple = \text{True} \rightarrow T = 100.000\text{ DKK}$)
  * Volatilitet $\sigma = 0,0$

#### Trin 1: Beregn renteudgift og effektivt skattefradrag
* Realkreditgæld (80% LTV):  
  $$D = 3.000.000 \cdot 0,80 = 2.400.000\text{ DKK}$$
* Årlig renteudgift:  
  $$I = 2.400.000 \cdot 0,037 = 88.800\text{ DKK}$$
* Da årlige renteudgifter ($88.800\text{ DKK}$) er under par-grænsen for et ægtepar ($100.000\text{ DKK}$), udgør rentefradraget den maksimale sats på **$33,0\%$**:  
  $$\tau_r = 0,33$$

#### Trin 2: Beregn efter-skat rentesats
$$\text{Rentebelastning efter skat} = r \cdot (1 - \tau_r) = 0,037 \cdot (1 - 0,33) = 0,02479 \text{ (eller } 2,479\%)$$

#### Trin 3: Beregn segment-specifikke parametre
* **Depreciering ($\delta$)**: For lejlighed i byen:  
  $$\delta = 0,016 \text{ (eller } 1,60\%)$$
* **Ejendomsskat ($\tau_p$)**:  
  $$\tau_p = 0,0095 + 0,0003 \cdot (129,2 / 100 - 1) = 0,0095 + 0,0000876 = 0,0095876 \text{ (eller } 0,959\%)$$
* **Risikopræmie ($rp$)**:  
  $$rp = 0,008 + 0,05 \cdot (0,037 - 0,02) = 0,008 + 0,00085 = 0,00885 \text{ (eller } 0,885\%)$$

#### Trin 4: Beregn samlet User Cost rate og DKK-beløb
* **User Cost rate**:  
  $$UC_{rate} = 0,02479 + 0,0095876 + 0,016 + 0,00885 = 0,0592276 \text{ (eller } 5,92\%)$$
* **Årlig User Cost**:  
  $$UC_{årlig} = 3.000.000 \cdot 0,0592276 = 177.682,80\text{ DKK}$$
* **Månedlig User Cost**:  
  $$UC_{månedlig} = \frac{177.682,80}{12} = 14.806,90\text{ DKK (afrundet til 14.807 DKK)}$$

---

### Eksempel 2: København Ejerlejligheder (Max Risk 12m)
* **Input-parametre**:
  * Ejendomsværdi $P = 3.000.000\text{ DKK}$
  * Rente $r = 5,5\%$ ($0,055$ under stagflation)
  * Segment: `copenhagen_apartments` (EJ56 indeks = $129,2$)
  * Husholdning: Ægtepar ($T = 100.000\text{ DKK}$)
  * Volatilitet $\sigma = 0,0$

#### Trin 1: Beregn renteudgift og effektivt skattefradrag
* Realkreditgæld (80% LTV):  
  $$D = 2.400.000\text{ DKK}$$
* Årlig renteudgift:  
  $$I = 2.400.000 \cdot 0,055 = 132.000\text{ DKK}$$
* Da årlige renteudgifter ($132.000\text{ DKK}$) overstiger par-grænsen ($100.000\text{ DKK}$), falder fradragssatsen til $25,0\%$ for den overskydende del ($32.000\text{ DKK}$):  
  $$\text{Deduktionsværdi} = (100.000 \cdot 0,33) + (32.000 \cdot 0,25) = 33.000 + 8.000 = 41.000\text{ DKK}$$
  $$\text{Effektiv fradragssats } \tau_r = \frac{41.000}{132.000} \approx 0,3106 \text{ (eller } 31,06\%)$$

#### Trin 2: Beregn efter-skat rentesats
$$\text{Rentebelastning efter skat} = r \cdot (1 - \tau_r) = 0,055 \cdot (1 - 0,3106) = 0,037917 \text{ (eller } 3,792\%)$$

#### Trin 3: Beregn segment-specifikke parametre
* **Depreciering ($\delta$)**:  
  $$\delta = 0,016 \text{ (eller } 1,60\%)$$
* **Ejendomsskat ($\tau_p$)**:  
  $$\tau_p = 0,0095876 \text{ (eller } 0,959\%)$$
* **Risikopræmie ($rp$)**:  
  $$rp = 0,008 + 0,05 \cdot (0,055 - 0,02) = 0,008 + 0,00175 = 0,00975 \text{ (eller } 0,975\%)$$

#### Trin 4: Beregn samlet User Cost rate og DKK-beløb
* **User Cost rate**:  
  $$UC_{rate} = 0,037917 + 0,0095876 + 0,016 + 0,00975 = 0,0732546 \text{ (eller } 7,33\%)$$
* **Årlig User Cost**:  
  $$UC_{årlig} = 3.000.000 \cdot 0,0732546 = 219.763,80\text{ DKK}$$
* **Månedlig User Cost**:  
  $$UC_{månedlig} = \frac{219.763,80}{12} = 18.313,65\text{ DKK (afrundet til 18.314 DKK)}$$
