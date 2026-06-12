import { earlyWarningIndicators, compositeScore, freshnessWeightedComposite, alertLevel, dataFreshness } from '../data/housingData';

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
  'EWI-1': 'Pris vs. løn: Hvis boligpriserne stiger markant hurtigere end lønningerne, risikerer købere at blive strakt ud over evne. GRØN: priserne stiger max 3 procentpoint hurtigere end lønnen. GUL: 3-5 pp. RØD: over 5 pp.',
  'EWI-2': 'Udbud vs. efterspørgsel: Antal måneder det tager at sælge alle boliger til udbudt. Lavt tal = knaphed (prispres op). GRØN: over 3,5 mdr. GUL: 2,5-3,5 mdr. RØD: under 2,5 mdr.',
  'EWI-3': 'Volumen-pris divergens: Hvis priserne stiger men handelsvolumen falder, kan det betyde at markedet drives af få handler til høje priser — et faresignal. GUL: volumen falder >10% mens priser stiger. RØD: falder >15%.',
  'EWI-4': 'Prisnedsættelser: Andelen af udbudte boliger hvor sælger har sat prisen ned. Højt tal = sælgerne kan ikke opnå deres udbudspris. GRØN: under 30%. GUL: 30-40%. RØD: over 40% med store nedsættelser.',
  'EWI-5': 'Liggetid: Hvor længe boliger ligger til salg. Lang liggetid = faldende momentum. GRØN: under 70 dage. GUL: 70-82 dage. RØD: over 82 dage.',
  'EWI-6': 'Pris-til-leje ratio: Sammenligner boligpriser med lejeniveauet. Hvis det er meget dyrere at eje end at leje, kan der være en boble. GUL: 1,5σ over gennemsnit. RØD: 2,5σ over gennemsnit.',
  'EWI-7': 'Afdragsfrihed: Andelen af nye realkreditlån uden afdrag. Højt tal = låntagerne er sårbare overfor rentestigninger. GRØN: under 50%. GUL: 50-60%. RØD: over 60%.',
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

function EWICard({ indicator, index }) {
  const color = statusColors[indicator.status];
  const glow = statusGlow[indicator.status];
  const tooltip = ewiTooltips[indicator.id] || '';

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

function DataFreshnessTable() {
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
            <th>Friskhed</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((src) => {
            const w = src.weight;
            const barColor = w >= 0.8 ? '#00d4aa' : w >= 0.5 ? '#feca57' : '#ff9f43';
            return (
              <tr key={src.label}>
                <td className="freshness-source-name">{src.label}</td>
                <td>{src.last_updated}</td>
                <td>{src.frequency}</td>
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

export default function EarlyWarningDashboard() {
  const alertColor = alertLevel === 'NORMAL' ? '#00d4aa' : alertLevel === 'ELEVATED' ? '#ffc107' : '#ff6b6b';
  const alertLabels = { NORMAL: 'Normal', ELEVATED: 'Forhøjet', HIGH: 'Høj', CRITICAL: 'Kritisk', EXTREME: 'Ekstrem' };

  return (
    <section className="glass-card panel-wide fade-in" style={{ animationDelay: '0.25s' }}>
      <div className="panel-header">
        <div>
          <h2>Tidlig varsling (EWI)</h2>
          <span className="panel-explainer">
            7 indikatorer der tilsammen vurderer risikoen for et kommende prisfald. Hver indikator har en trafiklys-status
            (Normal / Advarsel / Alarm) og en friskhedsbar der viser hvor opdateret datakilden er.
            Hold musen over en indikator for at se hvad den måler og hvornår den udløses.
          </span>
        </div>
        <div className="ewi-summary-badges">
          <span className="panel-badge tooltip"
            data-tooltip="Summen af alle 7 indikatorer: Normal=0, Advarsel=1, Alarm=3 point. Maks 21 point."
          >
            Score: <strong>{compositeScore} / 21</strong>
          </span>
          <span className="panel-badge tooltip"
            data-tooltip="Samme score, men vægtet med datakilde-friskhed. Indikatorer med gammel data tæller mindre. Giver et mere retvisende billede."
          >
            Friskheds-vægtet: <strong>{freshnessWeightedComposite} / 21</strong>
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
        {earlyWarningIndicators.map((ind, i) => (
          <EWICard key={ind.id} indicator={ind} index={i} />
        ))}
      </div>
      <DataFreshnessTable />
    </section>
  );
}
