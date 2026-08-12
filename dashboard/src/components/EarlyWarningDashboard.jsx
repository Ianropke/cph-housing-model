import { ResponsiveContainer, AreaChart, Area, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts';

const statusColors = {
  GREEN: '#00d4aa',
  AMBER: '#ffc107',
  RED: '#ff6b6b',
};

const statusGlow = {
  GREEN: 'rgba(0, 212, 170, 0.25)',
  AMBER: 'rgba(255, 193, 7, 0.25)',
  RED: 'rgba(255, 107, 107, 0.25)',
};

const ewiTooltips = {
  'EWI-2': 'Udbud vs. efterspørgsel: Antal måneder det tager at sælge alle boliger til udbudt. Lavt tal = knaphed (prispres op). GRØN: over 3,5 mdr. GUL: 2,5-3,5 mdr. RØD: under 2,5 mdr.',
  'EWI-3': 'Volumen-pris divergens: Hvis priserne stiger men handelsvolumen falder, kan det betyde at markedet drives af få handler til høje priser — et faresignal. GUL: volumen falder mere end 10% mens priser stiger. RØD: falder mere end 15%.',
  'EWI-4': 'Prisnedsættelser: Andelen af udbudte boliger hvor sælger har sat prisen ned. Højt tal = sælgerne kan ikke opnå deres udbudspris. GRØN: under 30%. GUL: 30-40%. RØD: over 40% med store nedsættelser.',
  'EWI-5': 'Liggetid: Hvor længe boliger ligger til salg. Tærsklerne beregnes dynamisk via en rullende Z-score over 12 kvartaler. GUL: 1,0σ over gennemsnittet. RØD: 2,0σ over gennemsnittet.',
  'EWI-6': 'Pris-til-leje ratio: Sammenligner boligpriser med lejeniveauet (HUS1). Tærsklerne beregnes dynamisk via en rullende Z-score over 12 kvartaler. GUL: 1,5σ over gennemsnittet. RØD: 2,5σ over gennemsnittet.',
  'EWI-7': 'Afdragsfrihed: Andelen af nye realkreditlån uden afdrag. Højt tal = låntagerne er sårbare overfor rentestigninger. GRØN: under 50%. GUL: 50-60%. RØD: over 60%.',
  'EWI-8': 'Debt-Servicing Ratio (DSR): Måler husholdningernes gældsbetjeningsbyrde (årlige renteomkostninger + bidrag divideret med disponibel indkomst). GRØN: under 30%. GUL: 30-40%. RØD: over 40% (Kritisk niveau ifølge IMF).',
};

const getEwi1Tooltip = (mode) => {
  if (mode === 'yoy_original') {
    return 'Pris vs. løn (Oprindelig YoY): Sammenligner det seneste års prisvækst med en fast lønvækst på 3,5%. Udløser advarsler i normale opgangsmarkeder på grund af volatilitets-asymmetri. AMBER: spread >3pp, RED: >5pp.';
  }
  if (mode === 'yoy_expanded') {
    return 'Pris vs. løn (Udvidet YoY): Sammenligner det seneste års prisvækst med lønvækst på 3,5%, men anvender bredere tærskler for at imødegå kortsigtede markedssvingninger. AMBER: spread >4pp, RED: >7pp.';
  }
  if (mode === 'structural_3y') {
    return 'Pris vs. løn (Strukturel 3-år): Sammenligner differencen baseret på et 3-års glidende gennemsnit af vækstraterne. Dette filtrerer kortsigtede rente- og sentiment-effekter fra. AMBER: spread >3pp, RED: >5pp.';
  }
  if (mode === 'structural_5y') {
    return 'Pris vs. løn (Strukturel 5-år): Sammenligner differencen baseret på et 5-års glidende gennemsnit af vækstraterne for at isolere langsigtede fundamentale ubalancer. AMBER: spread >3pp, RED: >5pp.';
  }
  return '';
};

function FreshnessBadge({ weight, lastUpdated }) {
  let badgeColor, badgeLabel;
  if (weight >= 0.8) {
    badgeColor = '#00d4aa';
    badgeLabel = 'Frisk';
  } else if (weight >= 0.5) {
    badgeColor = '#feca57';
    badgeLabel = 'OK';
  } else {
    badgeColor = '#ff9f43';
    badgeLabel = 'Aldrende';
  }

  return (
    <div className="freshness-badge"
      title={`Datakilde sidst opdateret: ${lastUpdated}\nFreshness-vægt: ${Math.round(weight * 100)}% — jo lavere, jo mindre tæller denne indikator i den samlede score`}
    >
      <div className="freshness-bar-bg">
        <div className="freshness-bar-fill" style={{
          width: `${weight * 100}%`,
          background: badgeColor,
        }} />
      </div>
      <span className="freshness-label" style={{ color: badgeColor }}>
        {badgeLabel} · {lastUpdated}
      </span>
    </div>
  );
}

function EWICard({ indicator, index, ewiMode }) {
  const color = statusColors[indicator.status];
  const glow = statusGlow[indicator.status];
  
  const tooltip = indicator.id === 'EWI-1'
    ? getEwi1Tooltip(ewiMode)
    : (ewiTooltips[indicator.id] || '');

  const statusLabels = { GREEN: 'Normal', AMBER: 'Advarsel', RED: 'Alarm' };

  return (
    <div
      className={`ewi-card fade-in ${tooltip ? 'tooltip' : ''}`}
      data-tooltip={tooltip}
      style={{
        animationDelay: `${0.2 + index * 0.08}s`,
        borderColor: `${color}33`,
      }}
    >
      <div className="ewi-header">
        <span className="ewi-id">{indicator.id}</span>
        <span
          className="ewi-status-badge"
          style={{ background: glow, color, borderColor: `${color}55` }}
        >
          <span className="ewi-dot" style={{ background: color }} />
          {statusLabels[indicator.status] || indicator.status}
        </span>
      </div>
      <h3 className="ewi-name">{indicator.name}</h3>
      <div className="ewi-values">
        <div className="ewi-value-group">
          <span className="ewi-label">Aktuel</span>
          <span className="ewi-value" style={{ color }}>
            {typeof indicator.value === 'number' && indicator.value > 100
              ? indicator.value.toLocaleString()
              : indicator.value}
          </span>
        </div>
        <div className="ewi-value-group">
          <span className="ewi-label">Grænse</span>
          <span className="ewi-value muted">
            {typeof indicator.baseline === 'number' && indicator.baseline > 100
              ? indicator.baseline.toLocaleString()
              : indicator.baseline}
          </span>
        </div>
      </div>
      <p className="ewi-description">{indicator.description}</p>
      {indicator.freshness_weight != null && (
        <FreshnessBadge weight={indicator.freshness_weight} lastUpdated={indicator.last_updated} />
      )}
    </div>
  );
}

function DataFreshnessTable({ dataFreshness }) {
  if (!dataFreshness) return null;
  const sources = Object.values(dataFreshness);

  return (
    <div className="freshness-table-wrap">
      <h3 className="freshness-table-title">Datakilde-oversigt</h3>
      <p className="freshness-table-explainer">
        Hver datakilde har en friskhedsvægt (0-100%). Jo mere opdateret data er, jo mere tæller den i modellens vurdering. 
        Kilder der er ældre end deres halverings-tid nedvægtes automatisk.
      </p>
      <table className="freshness-table">
        <thead>
          <tr>
            <th>Datakilde</th>
            <th>Sidst opdateret</th>
            <th>Frekvens</th>
            <th>Næste opdatering</th>
            <th>Friskhed</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((src) => {
            const w = src.freshness_weight;
            const barColor = w >= 0.8 ? '#00d4aa' : w >= 0.5 ? '#feca57' : '#ff9f43';
            return (
              <tr key={src.label}>
                <td className="freshness-source-name">{src.label}</td>
                <td>{src.last_updated}</td>
                <td>{src.frequency}</td>
                <td>{src.next_expected_update || 'Ukendt'}</td>
                <td>
                  <div className="freshness-cell">
                    <div className="freshness-bar-bg small">
                      <div className="freshness-bar-fill" style={{
                        width: `${w * 100}%`,
                        background: barColor,
                      }} />
                    </div>
                    <span style={{ color: barColor, fontSize: '11px', fontWeight: 600 }}>
                      {Math.round(w * 100)}%
                    </span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function EarlyWarningDashboard({ 
  ewiMode, 
  setEwiMode, 
  indicators, 
  compositeScore, 
  freshnessWeightedComposite, 
  alertLevel,
  mlCrashProbability,
  dataFreshness,
  mlProbabilityHistory,
  mlModelStatus,
}) {
  const alertColor = alertLevel === 'NORMAL' ? '#00d4aa' : alertLevel === 'ELEVATED' ? '#ffc107' : '#ff6b6b';
  const alertLabels = { NORMAL: 'Normal', ELEVATED: 'Forhøjet', HIGH: 'Høj', CRITICAL: 'Kritisk', EXTREME: 'Ekstrem' };

  return (
    <section className="glass-card panel-wide fade-in" style={{ animationDelay: '0.25s' }}>
      <div className="panel-header" style={{ flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2>Tidlig varsling (EWI)</h2>
          <span className="panel-explainer">
            9 indikatorer der tilsammen vurderer markedets sårbarhed. Hver indikator har en trafiklys-status
            (Normal / Advarsel / Alarm) og en friskhedsbar der viser hvor opdateret datakilden er.
            Hold musen over en indikator for at se hvad den måler og hvornår den udløses.
          </span>
        </div>
        
        {/* Dynamic Mode Selector */}
        <div className="ewi-mode-selector">
          <label htmlFor="ewi1-mode-select" className="ewi-mode-label">Metode for EWI-1 (Pris/Løn):</label>
          <select 
            id="ewi1-mode-select" 
            value={ewiMode} 
            onChange={(e) => setEwiMode(e.target.value)}
            className="ewi-mode-select"
          >
            <option value="yoy_expanded">Kortsigtet (YoY + Udvidede Grænser)</option>
            <option value="structural_3y">Strukturel (3-års Glidende Gennemsnit)</option>
            <option value="structural_5y">Strukturel (5-års Glidende Gennemsnit)</option>
            <option value="yoy_original">Kortsigtet (Oprindelig YoY)</option>
          </select>
        </div>

        <div className="ewi-summary-badges" style={{ alignItems: 'center' }}>
          <span className="panel-badge tooltip"
            data-tooltip="Statistisk vægtet sum af 9 indikatorer baseret på signalstyrke (Normal=0, Advarsel=1, Alarm=3). EWI-score er et indeks — ikke en procentchance. Maks 27.0 point."
          >
            Score: <strong>{compositeScore} / 27</strong>
          </span>
          <span className="panel-badge tooltip"
            data-tooltip="Samme score, men reguleret med datakildernes løbende friskhedsvægt. Indikatorer med gammel data tæller mindre. Det er stadig et indeks, ikke en sandsynlighed."
          >
            Friskheds-vægtet: <strong>{freshnessWeightedComposite} / 27</strong>
          </span>
          <span
            className="panel-badge"
            style={{ background: `${alertColor}18`, color: alertColor, borderColor: `${alertColor}44` }}
          >
            Niveau: <strong>{alertLabels[alertLevel] || alertLevel}</strong>
          </span>
        </div>
      </div>
      <div className="ewi-grid">
        {indicators.map((ind, i) => (
          <EWICard key={ind.id} indicator={ind} index={i} ewiMode={ewiMode} />
        ))}
      </div>

      {/* NEW ML PREDICTION SECTION */}
      {mlCrashProbability !== null && mlProbabilityHistory && mlProbabilityHistory.length > 0 && (
        <div className="ml-prediction-section fade-in" style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(156, 39, 176, 0.04)', borderRadius: '12px', border: '1px solid rgba(156, 39, 176, 0.2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#e040fb', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                Machine Learning Prognose
              </h3>
              <p style={{ margin: 0, fontSize: '0.9rem', color: 'rgba(255,255,255,0.6)', maxWidth: '600px' }}>
                Selvstændigt ML-modelestimat trænet på historiske EWI-data fra 2000-2026. Procentsatsen angiver den estimerede sandsynlighed for et mærkbart prisfald (&gt;10%) inden for de næste 12 måneder — ikke den forventede prisudvikling og ikke Risikobarometerets score.
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '3rem', fontWeight: 800, color: '#e040fb', lineHeight: 1, textShadow: '0 0 20px rgba(224, 64, 251, 0.4)' }}>
                {(mlCrashProbability * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.5)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>
                Modelestimat: prisfald &gt;10% (12 mdr.)
              </div>
            </div>
          </div>
          <div style={{ margin: '0 0 1.25rem', padding: '0.75rem 1rem', borderLeft: '3px solid #e040fb', background: 'rgba(156, 39, 176, 0.08)', color: 'rgba(255,255,255,0.72)', fontSize: '0.82rem', lineHeight: 1.5 }}>
            <strong style={{ color: '#f0b6ff' }}>Sådan læses tallet:</strong> Et højt ML-estimat kan godt forekomme samtidig med en lav forecast-score, hvis de aktuelle advarselssignaler ligner historiske faldperioder, men forecastets scenarier fortsat overvejende peger opad. Det er modeluenighed — ikke to modstridende procentchancer.
          </div>
          
          <div style={{ height: '260px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mlProbabilityHistory.map(h => ({ ...h, pct: h.probability * 100 }))} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="mlLargeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#e040fb" stopOpacity={0.6}/>
                    <stop offset="95%" stopColor="#e040fb" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="quarter" 
                  stroke="rgba(255,255,255,0.2)" 
                  tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} 
                  tickMargin={10} 
                  minTickGap={20}
                />
                <YAxis 
                  domain={[0, 100]} 
                  stroke="rgba(255,255,255,0.2)" 
                  tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} 
                  tickFormatter={(val) => `${val}%`}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(10, 14, 26, 0.95)', borderColor: 'rgba(156, 39, 176, 0.3)', borderRadius: '8px', color: '#fff', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}
                  itemStyle={{ color: '#e040fb', fontWeight: 600 }}
                  labelStyle={{ color: 'rgba(255,255,255,0.6)', marginBottom: '4px' }}
                  formatter={(value) => [`${value.toFixed(1)}%`, 'Sandsynlighed']}
                />
                <Area 
                  type="monotone" 
                  dataKey="pct" 
                  stroke="#e040fb" 
                  strokeWidth={3} 
                  fillOpacity={1} 
                  fill="url(#mlLargeGrad)" 
                  activeDot={{ r: 6, fill: '#e040fb', stroke: '#fff', strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {mlCrashProbability == null && (
        <div className="ml-prediction-section fade-in" style={{ marginTop: '2rem', padding: '1.25rem 1.5rem', background: 'rgba(255,193,7,0.04)', borderRadius: '12px', border: '1px solid rgba(255,193,7,0.2)' }}>
          <h3 style={{ margin: '0 0 0.5rem', color: '#ffc107' }}>ML-prognose ikke publiceret</h3>
          <p style={{ margin: 0, color: 'rgba(255,255,255,0.68)', fontSize: '0.88rem', lineHeight: 1.5 }}>
            Der vises ingen procentchance, fordi den nuværende ML-model er trænet på syntetiske feature-rækker og ikke er valideret out-of-sample på point-in-time live data. EWI-scoren og forecast-scenarierne ovenfor er de publicerede modeloutputs.
          </p>
          <span style={{ display: 'inline-block', marginTop: '0.75rem', color: 'rgba(255,255,255,0.45)', fontSize: '0.76rem' }}>
            Status: {mlModelStatus || 'UNAVAILABLE_UNVALIDATED_MODEL'}
          </span>
        </div>
      )}

      <DataFreshnessTable dataFreshness={dataFreshness} />
    </section>
  );
}
