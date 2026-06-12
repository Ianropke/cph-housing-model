import React, { useState } from 'react';

const componentTooltips = {
  mc_downside: 'Monte Carlo Downside måler sandsynligheden for at prisindekset falder under det nuværende niveau, baseret på 1.000 simulerede scenarier med tilfældig variation i renter, risikopræmie og vedligeholdelse.',
  severity: 'Scenarie-alvor viser hvor kraftigt boligpriserne falder i worst-case (Max Risk) scenariet. Jo højere tal, jo mere dramatisk er det beregnede prisfald.',
  ewi: 'EWI-signal sammenfatter de 7 tidlige varslingsindikatorer (pris vs. løn, udbud, salgstider mv.) til ét tal. Vægtet med datakilde-friskhed, så ældre data tæller mindre.',
  freshness: 'Data-friskhed viser hvor opdaterede datakilderne er i gennemsnit. 100% = alle kilder opdateret i dag. Lavere værdier betyder at nogle kilder er ældre, og modellens usikkerhed stiger.',
};

const horizonExplainers = {
  '6m': 'Risiko for prisfald de næste 6 måneder. Kort horisont — primært drevet af renteudvikling og likviditet.',
  '12m': 'Risiko for prisfald det næste år. Længere horisont — inkluderer makroøkonomiske stresscenarier.',
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
    mc_downside: 'Simul. downside',
    severity: 'Scenarie-alvor',
    ewi: 'EWI-signal',
    freshness: 'Data-friskhed',
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
            {/* Background arc */}
            <path
              d="M 10 90 A 70 70 0 0 1 150 90"
              fill="none"
              stroke="rgba(255,255,255,0.08)"
              strokeWidth="12"
              strokeLinecap="round"
            />
            {/* Score arc */}
            <path
              d="M 10 90 A 70 70 0 0 1 150 90"
              fill="none"
              stroke={color}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${(score / 100) * 220} 220`}
              style={{ filter: `drop-shadow(0 0 6px ${color}40)` }}
            />
            {/* Tick marks */}
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
            {/* Score text */}
            <text x="80" y="82" textAnchor="middle" fill="white"
              fontSize="28" fontWeight="700" fontFamily="Inter, system-ui">
              {score}
            </text>
            <text x="80" y="96" textAnchor="middle" fill="rgba(255,255,255,0.5)"
              fontSize="9" fontFamily="Inter, system-ui">
              af 100
            </text>
          </svg>
        </div>
        {/* Component breakdown */}
        <div className="risk-gauge-components">
          {['mc_downside', 'severity', 'ewi', 'freshness'].map((key) => {
            const val = key === 'freshness'
              ? data.components[key] * 100
              : key === 'mc_downside'
              ? data.components[key]
              : data.components[key];
            const displayVal = key === 'freshness'
              ? `${Math.round(data.components[key] * 100)}%`
              : `${data.components[key]}${key !== 'ewi' ? '%' : ''}`;
            const barWidth = key === 'freshness'
              ? data.components[key] * 100
              : key === 'mc_downside'
              ? Math.min(100, data.components[key] * 10)
              : key === 'severity'
              ? Math.min(100, data.components[key] * 3)
              : Math.min(100, data.components[key]);
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
            <p>Scoren beregnes som et vægtet gennemsnit af tre signaler: hvor mange Monte Carlo-simuleringer der viser prisfald (40%), hvor alvorligt worst-case scenariet er (30%), og hvad de tidlige varslingsindikatorer siger (30% × data-friskhed).</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="glass-card panel risk-barometer-panel fade-in" style={{ animationDelay: '0.1s' }}>
      <div className="panel-header">
        <div>
          <h2>Risikobarometer</h2>
          <span className="panel-subtitle">
            Samlet risikoscore for negativ prisudvikling (1-100). Kombinerer Monte Carlo-simuleringer, stress-scenarier og markedsindikatorer. Klik på en gauge for detaljer.
          </span>
        </div>
      </div>
      <div className="risk-barometer-gauges">
        {renderGauge('6m', maxRiskIndex['6m'])}
        {renderGauge('12m', maxRiskIndex['12m'])}
      </div>
      <div className="risk-barometer-legend">
        <span className="risk-legend-item"><span className="risk-dot" style={{background:'#00d4aa'}} />1-24: Lav risiko</span>
        <span className="risk-legend-item"><span className="risk-dot" style={{background:'#feca57'}} />25-49: Moderat</span>
        <span className="risk-legend-item"><span className="risk-dot" style={{background:'#ff9f43'}} />50-74: Forhøjet</span>
        <span className="risk-legend-item"><span className="risk-dot" style={{background:'#ff4757'}} />75-100: Høj risiko</span>
      </div>
    </div>
  );
};

export default RiskBarometer;
