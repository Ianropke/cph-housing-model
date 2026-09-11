import { useState } from 'react';

const componentTooltips = {
  mc_downside: 'Simuleret nedsideandel viser, hvor stor en andel af de 1.000 modelsimuleringer der ender med et prisindeks under det nuværende niveau under de valgte antagelser. Det er en simulationsfrekvens/sensitivitetsmåling, ikke en kalibreret sandsynlighed for et faktisk prisfald.',
  severity: 'Nedside-potentiale viser hvor kraftigt boligpriserne falder i Max Risk-scenariet. Tallet er et betinget scenario-output, ikke en prognose for hvad der faktisk vil ske.',
  ewi: 'Varslingsscore sammenfatter de tidlige varslingsindikatorer (pris vs. løn, udbud, salgstider mv.) til ét indeks. Det er ikke en procentchance.',
  freshness: 'Datakilde-friskhed viser hvor opdaterede datakilderne er i gennemsnit. 100% betyder ikke 100% sikkerhed; tallet beskriver kun datakildernes alder/friskhed.',
};

const horizonExplainers = {
  '6m': 'Scenario- og EWI-baseret nedsideindeks for 6-måneders horisonten. Ikke en sandsynlighed for prisfald.',
  '12m': 'Scenario- og EWI-baseret nedsideindeks for 12-måneders horisonten. Ikke en sandsynlighed for prisfald.',
};

const RiskBarometer = ({ maxRiskIndex }) => {
  const [expandedGauge, setExpandedGauge] = useState(null);

  if (!maxRiskIndex) return null;

  const getColor = (score) => {
    if (score >= 75) return '#ff4757';
    if (score >= 50) return '#ff9f43';
    if (score >= 25) return '#feca57';
    return '#00d4aa';
  };

  const getGradient = (score) => {
    if (score >= 75) return 'linear-gradient(135deg, #ff4757, #ff6b81)';
    if (score >= 50) return 'linear-gradient(135deg, #ff9f43, #ffbe76)';
    if (score >= 25) return 'linear-gradient(135deg, #feca57, #f9e852)';
    return 'linear-gradient(135deg, #00d4aa, #26de81)';
  };

  const componentLabels = {
    mc_downside: 'Simuleret nedsideandel',
    severity: 'Scenario-nedside',
    ewi: 'Varslingsscore',
    freshness: 'Datakilde-friskhed',
  };

  const renderGauge = (horizon, data) => {
    const score = data.score;
    const label = data.label;
    const color = getColor(score);
    const isExpanded = expandedGauge === horizon;

    return (
      <div className="risk-gauge" key={horizon}
        onClick={() => setExpandedGauge(isExpanded ? null : horizon)}
        style={{ cursor: 'pointer' }}
      >
        <div className="risk-gauge-header">
          <div className="risk-gauge-header-left">
            <span className="risk-gauge-horizon">{horizon}</span>
            <span className="risk-gauge-explainer">{horizonExplainers[horizon]}</span>
          </div>
          <span className="risk-gauge-label" style={{ color }}>{label}</span>
        </div>
        <div className="risk-gauge-visual">
          <svg viewBox="0 0 160 100" className="risk-gauge-svg">
            <path
              d="M 10 90 A 70 70 0 0 1 150 90"
              fill="none"
              stroke="rgba(255,255,255,0.08)"
              strokeWidth="12"
              strokeLinecap="round"
            />
            <path
              d="M 10 90 A 70 70 0 0 1 150 90"
              fill="none"
              stroke={color}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${(score / 100) * 220} 220`}
              style={{ filter: `drop-shadow(0 0 6px ${color}40)` }}
            />
            {[0, 25, 50, 75, 100].map((tick) => {
              const angle = ((tick / 100) * 180 - 180) * (Math.PI / 180);
              const x1 = 80 + 60 * Math.cos(angle);
              const y1 = 90 + 60 * Math.sin(angle);
              const x2 = 80 + 54 * Math.cos(angle);
              const y2 = 90 + 54 * Math.sin(angle);
              return (
                <line key={tick} x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" />
              );
            })}
            <text x="80" y="82" textAnchor="middle" fill="white"
              fontSize="28" fontWeight="700" fontFamily="Inter, system-ui">
              {score}
            </text>
            <text x="80" y="96" textAnchor="middle" fill="rgba(255,255,255,0.5)"
              fontSize="9" fontFamily="Inter, system-ui">
              indeks / 100
            </text>
          </svg>
        </div>
        <div className="risk-gauge-components">
          {['mc_downside', 'severity', 'ewi', 'freshness'].map((key) => {
            const dataKey = key === 'severity'
              ? 'max_risk_severity_pct'
              : key === 'ewi'
              ? 'ewi_contribution'
              : key === 'freshness'
              ? 'avg_data_freshness'
              : 'mc_downside';
            const componentValue = data.components?.[dataKey] ?? 0;

            const displayVal = key === 'freshness'
              ? `${Math.round(componentValue * 100)}%`
              : `${componentValue.toFixed(1)}${key !== 'ewi' ? '%' : ''}`;
            const barWidth = key === 'freshness'
              ? componentValue * 100
              : key === 'mc_downside'
              ? Math.min(100, componentValue * 10)
              : key === 'severity'
              ? Math.min(100, componentValue * 3)
              : Math.min(100, componentValue);
            const barGrad = key === 'freshness'
              ? 'linear-gradient(135deg, #3b82f6, #60a5fa)'
              : getGradient(barWidth);

            return (
              <div className="risk-component tooltip" key={key}
                data-tooltip={componentTooltips[key]}
              >
                <span className="risk-component-label">{componentLabels[key]}</span>
                <div className="risk-component-bar-wrap">
                  <div className="risk-component-bar" style={{
                    width: `${barWidth}%`,
                    background: barGrad,
                  }} />
                </div>
                <span className="risk-component-value">{displayVal}</span>
              </div>
            );
          })}
        </div>
        {isExpanded && (
          <div className="risk-gauge-detail">
            <p>Indekset kombinerer tre modelsignaler: simuleret nedsideandel (40%), scenario-nedside (30%) og EWI-signalet (30% × data-friskhed). Vægtene og simulationsfrekvensen er modelkonstruktioner og skal ikke læses som en kalibreret sandsynlighed for et fremtidigt prisfald.</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="glass-card panel risk-barometer-panel fade-in" style={{ animationDelay: '0.1s' }}>
      <div className="panel-header">
        <div>
          <h2>Nedsidebarometer</h2>
          <span className="panel-subtitle">
            Forecast- og EWI-baseret indeks (1-100) for modelberegnet nedside under de valgte antagelser. Det er ikke en procentchance og kan ikke sammenlignes direkte med en valideret ML-sandsynlighed. Klik på en gauge for detaljer.
          </span>
        </div>
      </div>
      <div className="risk-barometer-gauges">
        {renderGauge('6m', maxRiskIndex['6m'])}
        {renderGauge('12m', maxRiskIndex['12m'])}
      </div>
      <div className="risk-barometer-legend">
        <span className="risk-legend-item"><span className="risk-dot" style={{background:'#00d4aa'}} />1-24: Lavt indeks</span>
        <span className="risk-legend-item"><span className="risk-dot" style={{background:'#feca57'}} />25-49: Moderat</span>
        <span className="risk-legend-item"><span className="risk-dot" style={{background:'#ff9f43'}} />50-74: Forhøjet</span>
        <span className="risk-legend-item"><span className="risk-dot" style={{background:'#ff4757'}} />75-100: Højt indeks</span>
      </div>
    </div>
  );
};

export default RiskBarometer;
