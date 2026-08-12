import { useMemo, useState } from 'react';
import { useCity } from '../context/CityContext';

export default function ScenarioSandboxPanel() {
  const { pipelineData, activeCity } = useCity();
  const activeSegment = `${activeCity}_apartments`;

  // The pipeline payload is the sole source of truth for the actual-market
  // preset. Never substitute historical constants for incomplete live data.
  const liveIndicators = pipelineData?.early_warnings?.[activeSegment]?.indicators || {};
  const liveComposite = Number(pipelineData?.early_warnings?.[activeSegment]?.composite_score);
  const liveMlValue = pipelineData?.early_warnings?.[activeSegment]?.ml_crash_probability;
  const liveMlCrash = typeof liveMlValue === 'number' && Number.isFinite(liveMlValue) ? liveMlValue : null;
  const liveForecastChangePct = Number(
    pipelineData?.forecasts?.[activeSegment]?.horizons?.['12m']?.ensemble?.probability_weighted_change_pct,
  );
  const liveDom = Number(liveIndicators['EWI-5_time_on_market']?.median_dom_days);
  const liveSupply = Number(liveIndicators['EWI-2_supply_demand']?.months_of_supply);
  const liveReductions = Number(liveIndicators['EWI-4_price_reductions']?.reduction_rate_pct);
  const liveMortgageRate = Number(pipelineData?.user_costs?.baseline?.['12m']?.input?.mortgage_rate) * 100;
  const liveWageSpread = Number(liveIndicators['EWI-1_price_vs_wages']?.spread_pp);
  const liveAmortFreeShare = Number(liveIndicators['EWI-7_credit_growth']?.amortization_free_share_pct);
  const liveDsrPct = Number(liveIndicators['EWI-8_dsr']?.dsr_pct);
  const liveInputs = useMemo(() => ({
    dom: liveDom,
    supply: liveSupply,
    reductions: liveReductions,
    mortgageRate: liveMortgageRate,
    wageSpread: liveWageSpread,
    amortFreeShare: liveAmortFreeShare,
    dsrPct: liveDsrPct,
  }), [liveDom, liveSupply, liveReductions, liveMortgageRate, liveWageSpread, liveAmortFreeShare, liveDsrPct]);
  const hasLiveBaseline = [
    liveComposite,
    liveForecastChangePct,
    ...Object.values(liveInputs),
  ].every(Number.isFinite);

  // Preset definitions
  const PRESETS = {
    actual: {
      label: 'Aktuelt Marked (Live Data)',
      ...liveInputs,
    },
    maegler: {
      label: 'Mægler-Scenariet (+700 Udbudte Boliger)',
      dom: 74,
      supply: 6.5,
      reductions: 42,
      mortgageRate: 3.7,
      wageSpread: 14.5,
      amortFreeShare: 47.5,
      dsrPct: 36.5,
    },
    rateShock: {
      label: 'Rentestød (+1,5% Rente)',
      dom: 82,
      supply: 7.8,
      reductions: 48,
      mortgageRate: 5.2,
      wageSpread: 19.5,
      amortFreeShare: 54.0,
      dsrPct: 42.5,
    },
    goldilocks: {
      label: 'Rentedyk & Rekordboom (2,5% Rente)',
      dom: 35,
      supply: 2.1,
      reductions: 18,
      mortgageRate: 2.5,
      wageSpread: 8.0,
      amortFreeShare: 42.0,
      dsrPct: 28.5,
    },
    stagflation: {
      label: 'Stagflationskrise (6,0% Rente)',
      dom: 98,
      supply: 9.2,
      reductions: 58,
      mortgageRate: 6.0,
      wageSpread: 22.0,
      amortFreeShare: 62.0,
      dsrPct: 46.0,
    },
  };

  // Sandbox state initialized to actual live baseline
  const [dom, setDom] = useState(PRESETS.actual.dom);
  const [supply, setSupply] = useState(PRESETS.actual.supply);
  const [reductions, setReductions] = useState(PRESETS.actual.reductions);
  const [mortgageRate, setMortgageRate] = useState(PRESETS.actual.mortgageRate);
  const [wageSpread, setWageSpread] = useState(PRESETS.actual.wageSpread);
  const [amortFreeShare, setAmortFreeShare] = useState(PRESETS.actual.amortFreeShare);
  const [dsrPct, setDsrPct] = useState(PRESETS.actual.dsrPct);
  const [activePreset, setActivePreset] = useState('actual');

  const applyPreset = (key) => {
    const p = PRESETS[key];
    if (!p) return;
    setDom(p.dom);
    setSupply(p.supply);
    setReductions(p.reductions);
    setMortgageRate(p.mortgageRate);
    setWageSpread(p.wageSpread);
    setAmortFreeShare(p.amortFreeShare);
    setDsrPct(p.dsrPct);
    setActivePreset(key);
  };

  // Real-time calculation engine
  const simResults = useMemo(() => {
    // 1. EWI-1 (Price vs Wages)
    let ewi1Level = 'NORMAL';
    let ewi1Score = 0;
    if (wageSpread > 4.0) {
      ewi1Level = 'RED';
      ewi1Score = 4.2;
    } else if (wageSpread > 0) {
      ewi1Level = 'AMBER';
      ewi1Score = 1.4;
    }

    // 2. EWI-2 (Supply-Demand Balance)
    let ewi2Level = 'NORMAL';
    let ewi2Score = 0;
    if (supply < 2.5) {
      ewi2Level = 'RED'; // Extreme scarcity
      ewi2Score = 3.6;
    } else if (supply < 3.5 || supply > 6.0) {
      ewi2Level = 'AMBER'; // Tight or inventory overhang
      ewi2Score = 1.2;
    } else if (supply > 8.0) {
      ewi2Level = 'RED'; // Severe overhang
      ewi2Score = 3.6;
    }

    // 3. EWI-4 (Price Reductions)
    let ewi4Level = 'NORMAL';
    let ewi4Score = 0;
    if (reductions >= 40) {
      ewi4Level = 'RED';
      ewi4Score = 3.9;
    } else if (reductions >= 30) {
      ewi4Level = 'AMBER';
      ewi4Score = 1.3;
    }

    // 4. EWI-5 (Time on Market / DOM)
    let ewi5Level = 'NORMAL';
    let ewi5Score = 0;
    if (dom > 75) {
      ewi5Level = 'RED';
      ewi5Score = 2.4;
    } else if (dom > 62) {
      ewi5Level = 'AMBER';
      ewi5Score = 0.8;
    }

    // 5. EWI-7 (Amortization-Free Share)
    let ewi7Level = 'NORMAL';
    let ewi7Score = 0;
    if (amortFreeShare >= 60) {
      ewi7Level = 'RED';
      ewi7Score = 2.1;
    } else if (amortFreeShare >= 50) {
      ewi7Level = 'AMBER';
      ewi7Score = 0.7;
    }

    // 6. EWI-8 (Debt-Servicing Ratio / DSR)
    let ewi8Level = 'NORMAL';
    let ewi8Score = 0;
    if (dsrPct >= 40) {
      ewi8Level = 'RED';
      ewi8Score = 4.5;
    } else if (dsrPct >= 30) {
      ewi8Level = 'AMBER';
      ewi8Score = 1.5;
    }

    // Total Composite Score
    const compositeScore = activePreset === 'actual' ? liveComposite : (ewi1Score + ewi2Score + ewi4Score + ewi5Score + ewi7Score + ewi8Score);

    // Alert Level
    let alertLevel = 'NORMAL';
    let alertColor = '#00d4aa';
    if (compositeScore >= 14.0) {
      alertLevel = 'KRITISK (CRITICAL)';
      alertColor = '#ff3366';
    } else if (compositeScore >= 10.0) {
      alertLevel = 'HØJ (HIGH)';
      alertColor = '#ff6b6b';
    } else if (compositeScore >= 6.0) {
      alertLevel = 'FORHØJET (ELEVATED)';
      alertColor = '#ffc107';
    }

    // A probability is only calculated when the pipeline supplies a validated
    // ML probability. The simulator remains useful without it and never
    // recreates a probability from synthetic or fallback inputs.
    let mlCrashProb = null;
    if (liveMlCrash !== null && liveMlCrash > 0 && liveMlCrash < 1) {
      const baseLogit = Math.log(liveMlCrash / (1 - liveMlCrash));
      const deltaZ = 0.15 * (compositeScore - liveComposite)
                   + 0.30 * (mortgageRate - liveInputs.mortgageRate)
                   + 0.02 * (dom - liveInputs.dom)
                   + 0.03 * (reductions - liveInputs.reductions)
                   + 0.08 * (wageSpread - liveInputs.wageSpread);
      const zMl = baseLogit + deltaZ;
      mlCrashProb = activePreset === 'actual'
        ? liveMlCrash
        : Math.min(0.95, Math.max(0.02, 1 / (1 + Math.exp(-zMl))));
    }

    // Anchor the price scenario to the live 12m ensemble. Inputs use native
    // units / percentage points, preventing the former decimal-rate mix-up.
    const sim12mChangePct = liveForecastChangePct
      - 4.5 * (mortgageRate - liveInputs.mortgageRate)
      - 1.2 * (supply - liveInputs.supply)
      - 0.05 * (dom - liveInputs.dom);

    return {
      compositeScore,
      alertLevel,
      alertColor,
      mlCrashProb,
      sim12mChangePct,
      ewi1Level,
      ewi2Level,
      ewi4Level,
      ewi5Level,
      ewi7Level,
      ewi8Level,
    };
  }, [dom, supply, reductions, mortgageRate, wageSpread, amortFreeShare, dsrPct, activePreset, liveComposite, liveMlCrash, liveForecastChangePct, liveInputs]);

  // Status helper badge renderer
  const renderStatusBadge = (level) => {
    if (level === 'RED') return <span style={{ padding: '2px 8px', borderRadius: '6px', background: 'rgba(255, 107, 107, 0.2)', color: '#ff6b6b', fontSize: '0.75rem', fontWeight: 700 }}>🔴 ALARM</span>;
    if (level === 'AMBER') return <span style={{ padding: '2px 8px', borderRadius: '6px', background: 'rgba(255, 193, 7, 0.2)', color: '#ffc107', fontSize: '0.75rem', fontWeight: 700 }}>🟡 ADVARSEL</span>;
    return <span style={{ padding: '2px 8px', borderRadius: '6px', background: 'rgba(0, 212, 170, 0.2)', color: '#00d4aa', fontSize: '0.75rem', fontWeight: 700 }}>🟢 NORMAL</span>;
  };

  const deltaScore = simResults.compositeScore - liveComposite;
  const deltaMl = simResults.mlCrashProb !== null && liveMlCrash !== null
    ? simResults.mlCrashProb - liveMlCrash
    : null;

  if (!hasLiveBaseline) {
    return (
      <section className="glass-card panel-wide fade-in" style={{ marginTop: '1rem' }}>
        <h2>🧪 Interaktiv Risikosimulator</h2>
        <p className="panel-explainer">
          Simulatoren afventer et komplet live-payload. Den bruger ikke fallback-tal som aktuelt marked.
        </p>
      </section>
    );
  }

  return (
    <section className="glass-card panel-wide fade-in" style={{ animationDelay: '0.65s', marginTop: '1rem' }}>
      {/* Panel Header */}
      <div className="panel-header">
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>🧪</span> Interaktiv Risikosimulator (Hvad-Nu-Hvis Sandbox)
          </h2>
          <span className="panel-explainer">
            Juster markedsparametre for at se hvordan risikoscoren, advarselssignalerne og 12-måneders forecastet reagerer i forhold til det aktuelt opdaterede marked. En ML-procent vises kun, hvis en valideret model leverer den.
          </span>
        </div>
        <span className="panel-badge" style={{ background: 'rgba(167, 139, 250, 0.15)', color: '#a78bfa', borderColor: 'rgba(167, 139, 250, 0.3)' }}>
          Interaktiv Sandbox
        </span>
      </div>

      {/* Preset Action Buttons */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        {Object.keys(PRESETS).map((key) => (
          <button
            key={key}
            onClick={() => applyPreset(key)}
            style={{
              padding: '8px 14px',
              borderRadius: '8px',
              border: activePreset === key ? '1px solid #a78bfa' : '1px solid rgba(255,255,255,0.1)',
              background: activePreset === key ? 'rgba(167, 139, 250, 0.2)' : 'rgba(255,255,255,0.03)',
              color: activePreset === key ? '#ffffff' : 'rgba(255,255,255,0.7)',
              fontSize: '0.82rem',
              fontWeight: activePreset === key ? 600 : 400,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            {PRESETS[key].label}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        {/* LEFT COLUMN: Interactive Sliders */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', background: 'rgba(0,0,0,0.2)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <h4 style={{ color: '#a78bfa', fontSize: '0.95rem', margin: '0 0 8px 0', textTransform: 'uppercase', letterSpacing: '1px' }}>
            🎛️ Juster Markedsparametre
          </h4>

          {/* Slider 1: DOM / Liggetid */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.85rem' }}>
              <span style={{ color: 'rgba(255,255,255,0.8)' }}>Liggetid (Days on Market / DOM):</span>
              <strong style={{ color: '#00d4aa' }}>{dom} dage</strong>
            </div>
            <input
              type="range"
              min="15"
              max="120"
              value={dom}
              onChange={(e) => { setDom(Number(e.target.value)); setActivePreset('custom'); }}
              style={{ width: '100%', accentColor: '#00d4aa', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)' }}>
              <span>15d (Glohedt)</span>
              <span>62d (AMBER)</span>
              <span>120d (Fastlåst)</span>
            </div>
          </div>

          {/* Slider 2: Supply / Udbudsmåneder */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.85rem' }}>
              <span style={{ color: 'rgba(255,255,255,0.8)' }}>Udbudsmåneder (Months of Supply):</span>
              <strong style={{ color: '#3b82f6' }}>{supply.toFixed(1)} mdr</strong>
            </div>
            <input
              type="range"
              min="1.0"
              max="10.0"
              step="0.1"
              value={supply}
              onChange={(e) => { setSupply(Number(e.target.value)); setActivePreset('custom'); }}
              style={{ width: '100%', accentColor: '#3b82f6', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)' }}>
              <span>1.0m (Knaphed)</span>
              <span>4.5m (Baseline)</span>
              <span>10.0m (Udbudsoverskud)</span>
            </div>
          </div>

          {/* Slider 3: Price Reductions % */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.85rem' }}>
              <span style={{ color: 'rgba(255,255,255,0.8)' }}>Prisnedsættelses-andel (% opslag med afslag):</span>
              <strong style={{ color: '#ffc107' }}>{reductions.toFixed(1)}%</strong>
            </div>
            <input
              type="range"
              min="10"
              max="70"
              step="0.1"
              value={reductions}
              onChange={(e) => { setReductions(Number(e.target.value)); setActivePreset('custom'); }}
              style={{ width: '100%', accentColor: '#ffc107', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)' }}>
              <span>10% (Sælgers marked)</span>
              <span>30% (AMBER)</span>
              <span>70% (Købers afslag)</span>
            </div>
          </div>

          {/* Slider 4: Mortgage Rate % */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.85rem' }}>
              <span style={{ color: 'rgba(255,255,255,0.8)' }}>Realkreditrente (30-årigt fast):</span>
              <strong style={{ color: '#e040fb' }}>{mortgageRate.toFixed(1)}%</strong>
            </div>
            <input
              type="range"
              min="1.5"
              max="7.0"
              step="0.1"
              value={mortgageRate}
              onChange={(e) => { setMortgageRate(Number(e.target.value)); setActivePreset('custom'); }}
              style={{ width: '100%', accentColor: '#e040fb', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)' }}>
              <span>1.5% (Lavrente)</span>
              <span>3.7% (Nuværende)</span>
              <span>7.0% (Kreditstramning)</span>
            </div>
          </div>

          {/* Slider 5: Wage Spread pp */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.85rem' }}>
              <span style={{ color: 'rgba(255,255,255,0.8)' }}>Pris vs Løn Spread (pp overstigning):</span>
              <strong style={{ color: '#ff6b6b' }}>+{wageSpread.toFixed(1)}pp</strong>
            </div>
            <input
              type="range"
              min="0"
              max="25"
              step="0.5"
              value={wageSpread}
              onChange={(e) => { setWageSpread(Number(e.target.value)); setActivePreset('custom'); }}
              style={{ width: '100%', accentColor: '#ff6b6b', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)' }}>
              <span>0pp (Balance)</span>
              <span>4pp (RED)</span>
              <span>25pp (Ekstrem Overophedning)</span>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Real-time Simulation Output Comparison */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h4 style={{ color: '#a78bfa', fontSize: '0.95rem', margin: '0 0 8px 0', textTransform: 'uppercase', letterSpacing: '1px' }}>
            📊 Simuleret Risikoudfald vs. Aktuelt Marked
          </h4>

          {/* Primary Result Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
            {/* Composite Score Card */}
            <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase' }}>Simuleret Risikoscore</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: simResults.alertColor, margin: '4px 0' }}>
                {simResults.compositeScore.toFixed(1)} <small style={{ fontSize: '0.8rem', fontWeight: 400, color: 'rgba(255,255,255,0.4)' }}>/ 27.0</small>
              </div>
              <div style={{ fontSize: '0.75rem', color: Math.abs(deltaScore) < 0.05 ? 'rgba(255,255,255,0.5)' : (deltaScore >= 0 ? '#ff6b6b' : '#00d4aa') }}>
                {Math.abs(deltaScore) < 0.05 ? `Matcher live-baseline (${liveComposite.toFixed(1)} / 27.0)` : (deltaScore >= 0 ? `+${deltaScore.toFixed(1)}pt i forhold til nu` : `${deltaScore.toFixed(1)}pt i forhold til nu`)}
              </div>
            </div>

            {/* Alert Level Card */}
            <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase' }}>Simuleret Varslingsniveau</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: simResults.alertColor, margin: '8px 0' }}>
                {simResults.alertLevel}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)' }}>
                Tærskel baseret på EWI matrix
              </div>
            </div>

            {/* ML Crash Probability Card */}
            <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(224, 64, 251, 0.05)', border: '1px solid rgba(224, 64, 251, 0.2)' }}>
              <div style={{ fontSize: '0.75rem', color: '#e040fb', textTransform: 'uppercase', fontWeight: 600 }}>ML Crash Sandsynlighed (&gt;10% fald)</div>
              {simResults.mlCrashProb === null ? (
                <>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'rgba(224, 64, 251, 0.55)', margin: '4px 0' }}>—</div>
                  <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Ikke publiceret: model ikke valideret</div>
                </>
              ) : (
                <>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#e040fb', margin: '4px 0' }}>
                    {(simResults.mlCrashProb * 100).toFixed(1)}%
                  </div>
                  <div style={{ fontSize: '0.75rem', color: Math.abs(deltaMl) < 0.001 ? 'rgba(255,255,255,0.5)' : (deltaMl >= 0 ? '#ff6b6b' : '#00d4aa') }}>
                    {Math.abs(deltaMl) < 0.001 ? `Matcher live-baseline (${(liveMlCrash * 100).toFixed(1)}%)` : (deltaMl >= 0 ? `+${(deltaMl * 100).toFixed(1)}% risiko` : `${(deltaMl * 100).toFixed(1)}% risiko`)}
                  </div>
                </>
              )}
            </div>

            {/* 12m Forecast Price Change Card */}
            <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
              <div style={{ fontSize: '0.75rem', color: '#3b82f6', textTransform: 'uppercase', fontWeight: 600 }}>Simuleret 12m Prisudvikling</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: simResults.sim12mChangePct >= 0 ? '#00d4aa' : '#ff6b6b', margin: '4px 0' }}>
                {simResults.sim12mChangePct >= 0 ? `+${simResults.sim12mChangePct.toFixed(1)}%` : `${simResults.sim12mChangePct.toFixed(1)}%`}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)' }}>
                12-måneders horisont
              </div>
            </div>
          </div>

          {/* Indicator Breakdown Table */}
          <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '10px', padding: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)', marginBottom: '8px', textTransform: 'uppercase', fontWeight: 600 }}>
              Indikator-reaktioner i din simulering:
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                <span>EWI-1 (Pris vs Løn):</span> {renderStatusBadge(simResults.ewi1Level)}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                <span>EWI-2 (Udbud vs Efterspørgsel):</span> {renderStatusBadge(simResults.ewi2Level)}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                <span>EWI-4 (Prisnedsættelser):</span> {renderStatusBadge(simResults.ewi4Level)}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                <span>EWI-5 (Liggetid / DOM):</span> {renderStatusBadge(simResults.ewi5Level)}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                <span>EWI-7 (Afdragsfri Andel):</span> {renderStatusBadge(simResults.ewi7Level)}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                <span>EWI-8 (Debt-Servicing Ratio):</span> {renderStatusBadge(simResults.ewi8Level)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
