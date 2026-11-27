import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';

const SEGMENT_LABELS = {
  copenhagen_apartments: 'København — Ejerlejligheder',
  copenhagen_houses: 'København — Huse',
  frederiksberg_apartments: 'Frederiksberg — Ejerlejligheder',
};

const DIRECTION_CONFIG = {
  OP: { label: 'OPADGÅENDE', color: '#00d4aa', bg: 'rgba(0, 212, 170, 0.14)', arrow: '↗' },
  FLADT: { label: 'AFDÆMPET / FLADT', color: '#ffc107', bg: 'rgba(255, 193, 7, 0.14)', arrow: '→' },
  NED: { label: 'NEDADGÅENDE', color: '#ff6b6b', bg: 'rgba(255, 107, 107, 0.14)', arrow: '↘' },
};

const formatPct = (val) => {
  if (typeof val !== 'number' || !Number.isFinite(val)) return '—';
  const sign = val > 0 ? '+' : '';
  return `${sign}${val.toFixed(1).replace('.', ',')}%`;
};

const formatPp = (val) => {
  if (typeof val !== 'number' || !Number.isFinite(val)) return '—';
  const sign = val > 0 ? '+' : '';
  return `${sign}${val.toFixed(1).replace('.', ',')} pp`;
};

const formatDkkSqm = (val) => (
  typeof val === 'number' && Number.isFinite(val)
    ? `${Math.round(val).toLocaleString('da-DK')} kr./m²`
    : '—'
);

const formatPeriodDa = (period) => {
  if (typeof period !== 'string') return '—';
  const match = period.match(/^(\d{4})M(\d{2})$/);
  if (!match) return period;
  const months = ['jan.', 'feb.', 'mar.', 'apr.', 'maj', 'jun.', 'jul.', 'aug.', 'sep.', 'okt.', 'nov.', 'dec.'];
  return months[Number(match[2]) - 1] ? `${months[Number(match[2]) - 1]} ${match[1]}` : period;
};

const ForecastTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  if (!row) return null;

  return (
    <div className="chart-tooltip">
      <div className="tooltip-label">
        {label} {row.horizon_label ? `(${row.horizon_label} prognose)` : '(DST EJ56)'}
      </div>
      {row.actual != null && (
        <p style={{ color: '#00d4aa' }}>
          Realiseret indeks: <strong>{row.actual.toFixed(1)}</strong>
        </p>
      )}
      {row.is_forecast && row.forecast != null && (
        <>
          <p style={{ color: '#3b82f6' }}>
            Samlet prognose: <strong>{row.forecast.toFixed(1)}</strong>
          </p>
          {row.econometric != null && (
            <p style={{ color: 'rgba(255,255,255,0.65)' }}>
              Ren DST-tidsseriemodel: <strong>{row.econometric.toFixed(1)}</strong>
            </p>
          )}
          {row.p10 != null && row.p90 != null && (
            <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: '0.75rem', marginTop: '4px' }}>
              Empirisk P10–P90 bånd: <strong>[{row.p10.toFixed(1)} – {row.p90.toFixed(1)}]</strong>
            </p>
          )}
        </>
      )}
      <p className="tooltip-hint">Prisindeks (Base 2006 = 100). Bånd fra walk-forward OOS-fejl.</p>
    </div>
  );
};

export default function ForecastHeroPanel({
  pipelineData,
  activeSegment,
  setActiveSegment,
  onOpenTab,
}) {
  const fe = pipelineData?.forecast_engine?.[activeSegment];
  const nowcast = pipelineData?.asking_price_nowcast?.[activeSegment];
  const ewi = pipelineData?.early_warnings?.[activeSegment];

  if (!fe) {
    return (
      <section className="glass-card panel-wide fade-in">
        <h2>Datadrevet boligprisprognose</h2>
        <p className="panel-explainer">
          Prognosemotorens output er midlertidigt utilgængeligt for det valgte segment.
        </p>
      </section>
    );
  }

  const h6 = fe.horizons['6m'];
  const h12 = fe.horizons['12m'];
  const h24 = fe.horizons['24m'];
  const dir = DIRECTION_CONFIG[fe.direction_12m] || DIRECTION_CONFIG.FLADT;
  const wf12 = h12.walk_forward_validation;
  const wf6 = h6.walk_forward_validation;

  const udb = nowcast?.rkr_udb020;
  const boliga = nowcast?.boliga_realtime;
  const ewiScore = ewi?.composite_score;
  const ewiAlert = ewi?.alert_level;

  const horizonCards = [
    { key: '6m', label: '6 måneder', data: h6 },
    { key: '12m', label: '12 måneder', data: h12, primary: true },
    { key: '24m', label: '24 måneder', data: h24 },
  ];

  // Combine 12m drivers (both econometric and live post-quarter market signals)
  const ecoDrivers = h12.drivers?.econometric || [];
  const liveDrivers = h12.drivers?.live_market || [];

  // Tight Y-axis domain around actuals + forecast P10-P90 fan so the curve uses full chart height
  const yValues = fe.trajectory.flatMap((pt) => [pt.actual, pt.forecast, pt.econometric, pt.p10, pt.p90].filter((v) => typeof v === 'number' && Number.isFinite(v)));
  const yMin = yValues.length ? Math.floor((Math.min(...yValues) - 6) / 5) * 5 : 80;
  const yMax = yValues.length ? Math.ceil((Math.max(...yValues) + 6) / 5) * 5 : 180;

  return (
    <div className="forecast-hero-stack">
      {/* 1. HERO FORECAST VERDICT & HORIZON CARDS */}
      <section className="glass-card panel-wide fade-in forecast-hero-card">
        <div className="forecast-hero-top">
          <div>
            <div className="forecast-eyebrow">
              <span>Datadrevet prognosemotor</span>
              <span>·</span>
              <span>Trænet på DST {fe.training_range} ({fe.training_quarters} kvt.)</span>
            </div>
            <h2 className="forecast-hero-heading">
              Hvor bevæger markedet sig hen? — {SEGMENT_LABELS[activeSegment] || activeSegment}
            </h2>
            <p className="panel-explainer" style={{ maxWidth: '780px' }}>
              Kombinerer en regulariseret økonometrisk tidsseriemodel (DST EJ56 + renter 2007–2026) med live markedsjustering
              efter {fe.current_period} fra udbudspriser (UDB020), liggetid, handelsvolumen og Boliga-prisafslag.
            </p>
          </div>

          <div className="forecast-hero-controls">
            <div className="segment-pills" role="tablist" aria-label="Vælg boligsegment">
              {Object.entries(SEGMENT_LABELS).map(([segKey, segLabel]) => (
                <button
                  key={segKey}
                  type="button"
                  role="tab"
                  aria-selected={activeSegment === segKey}
                  className={`segment-pill ${activeSegment === segKey ? 'active' : ''}`}
                  onClick={() => setActiveSegment(segKey)}
                >
                  {segLabel.replace('København — ', 'Kbh. ').replace('Frederiksberg — ', 'Frb. ')}
                </button>
              ))}
            </div>
            <div className="direction-pill" style={{ color: dir.color, background: dir.bg, borderColor: `${dir.color}44` }}>
              <span className="direction-arrow">{dir.arrow}</span>
              <span>12 mdr. retning: <strong>{dir.label}</strong></span>
            </div>
          </div>
        </div>

        {/* 3 Horizon Forecast Cards */}
        <div className="horizon-cards-grid">
          {horizonCards.map(({ key, label, data, primary }) => {
            const c = data.combined;
            const valColor = c.change_pct >= 1.5 ? '#00d4aa' : c.change_pct <= -1.5 ? '#ff6b6b' : '#ffc107';
            return (
              <div key={key} className={`horizon-card ${primary ? 'horizon-card-primary' : ''}`}>
                <div className="horizon-card-header">
                  <span className="horizon-card-title">{label}</span>
                  <span className="horizon-card-target">Mål: {data.target_period}</span>
                </div>
                <div className="horizon-card-pct" style={{ color: valColor }}>
                  {formatPct(c.change_pct)}
                </div>
                <div className="horizon-card-sub">
                  Indeks <strong>{c.forecast_index.toFixed(1)}</strong> (fra {fe.current_index.toFixed(1)})
                </div>
                <div className="horizon-card-band">
                  Empirisk P10–P90: <strong>{formatPct(c.p10_change_pct)}</strong> til <strong>{formatPct(c.p90_change_pct)}</strong>
                </div>
                <div className="horizon-card-split">
                  <span>DST-model: {formatPct(data.econometric_ridge.change_pct)}</span>
                  <span style={{ color: data.live_adjustment_pp < 0 ? '#ff6b6b' : '#00d4aa' }}>
                    Live-bro: {formatPp(data.live_adjustment_pp)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* UNIFIED MAIN CHART: Historical EJ56 + Forecast Fan */}
        <div className="unified-chart-box">
          <div className="unified-chart-header">
            <div>
              <h3 className="unified-chart-title">Samlet prisbane: Historik ({fe.current_period}) → Prognosevifte (24 mdr.)</h3>
              <span className="unified-chart-sub">
                Grøn linje = realiseret DST EJ56 · Blå linje = samlet prognose (inkl. live-bro) · Blåt bånd = empirisk P10–P90 ud fra walk-forward fejl · Stiplet grå = ren DST-model
              </span>
            </div>
            <div className="wf-badge-group">
              <span className="panel-badge" title="Gennemsnitlig absolut fejl i ud-af-stikprøve walk-forward test uden look-ahead">
                6m OOS-fejl: <strong>{wf6.mae_pct.toFixed(1).replace('.', ',')}%</strong> (Hit {wf6.hit_rate_pct.toFixed(0)}%)
              </span>
              <span className="panel-badge" title="12-måneders walk-forward out-of-sample validering på DST-historik">
                12m OOS-fejl: <strong>{wf12.mae_pct.toFixed(1).replace('.', ',')}%</strong> (n={wf12.oos_quarters} kvt.)
              </span>
            </div>
          </div>

          <div className="chart-container">
            <ResponsiveContainer width="100%" height={330}>
              <ComposedChart data={fe.trajectory} margin={{ top: 16, right: 24, left: 6, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis
                  dataKey="period"
                  stroke="rgba(255,255,255,0.4)"
                  tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }}
                  minTickGap={22}
                />
                <YAxis
                  stroke="rgba(255,255,255,0.4)"
                  tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }}
                  domain={[yMin, yMax]}
                  width={48}
                />
                <Tooltip content={<ForecastTooltip />} />
                <ReferenceLine
                  x={fe.current_period}
                  stroke="rgba(167,139,250,0.65)"
                  strokeDasharray="4 4"
                  label={{
                    value: `Seneste DST (${fe.current_period})`,
                    position: 'insideTopLeft',
                    fill: '#a78bfa',
                    fontSize: 10,
                  }}
                />
                {/* Stacked Area trick for P10-P90 fan band */}
                <Area
                  type="monotone"
                  dataKey="band_base"
                  stackId="fan"
                  stroke="none"
                  fill="transparent"
                  isAnimationActive={false}
                />
                <Area
                  type="monotone"
                  dataKey="band_width"
                  stackId="fan"
                  stroke="none"
                  fill="rgba(59, 130, 246, 0.18)"
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  name="Realiseret (DST EJ56)"
                  stroke="#00d4aa"
                  strokeWidth={2.6}
                  dot={{ r: 2.5, fill: '#00d4aa', strokeWidth: 0 }}
                  activeDot={{ r: 5, fill: '#00d4aa', stroke: '#0a0e1a', strokeWidth: 2 }}
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="econometric"
                  name="Ren DST-model"
                  stroke="rgba(255,255,255,0.38)"
                  strokeWidth={1.6}
                  strokeDasharray="5 4"
                  dot={false}
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  name="Samlet prognose"
                  stroke="#3b82f6"
                  strokeWidth={2.8}
                  dot={{ r: 4, fill: '#3b82f6', stroke: '#0a0e1a', strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: '#60a5fa', stroke: '#0a0e1a', strokeWidth: 2 }}
                  connectNulls={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* 2. DRIVERS & LIVE NOWCAST PULSE (2 balanced columns on desktop) */}
      <div className="forecast-secondary-grid">
        {/* Left: What drives the 12m forecast up and down */}
        <section className="glass-card fade-in" style={{ animationDelay: '0.12s' }}>
          <div className="panel-header" style={{ marginBottom: '14px' }}>
            <div>
              <h2>Hvad driver 12-måneders prognosen?</h2>
              <span className="panel-explainer">
                Eksakt opdeling i procentpoint mellem den historiske DST-tidsseriemodel og de nyeste live-signaler efter {fe.current_period}.
              </span>
            </div>
          </div>

          <div className="drivers-group">
            <div className="drivers-group-title">Historisk økonometrisk model (DST 2007–2026)</div>
            {ecoDrivers.map((d) => (
              <div className="driver-row" key={d.key}>
                <div className="driver-row-left">
                  <span className="driver-label">{d.label}</span>
                  <span className="driver-meta">{d.value_display} · {d.source}</span>
                </div>
                <span className="driver-impact" style={{ color: d.impact_pp >= 0 ? '#00d4aa' : '#ff6b6b' }}>
                  {formatPp(d.impact_pp)}
                </span>
              </div>
            ))}
          </div>

          <div className="drivers-group" style={{ marginTop: '14px' }}>
            <div className="drivers-group-title">Live markedsjustering efter {fe.current_period} (6m basis, ×1,15 på 12m)</div>
            {liveDrivers.map((d) => (
              <div className="driver-row" key={d.key}>
                <div className="driver-row-left">
                  <span className="driver-label">{d.label}</span>
                  <span className="driver-meta">{d.value_display} · {d.source}</span>
                </div>
                <span className="driver-impact" style={{ color: d.impact_pp >= 0 ? '#00d4aa' : '#ff6b6b' }}>
                  {formatPp(d.impact_pp)}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Right: Live Market Pulse (Nowcast + EWI Summary + Quick Navigation) */}
        <section className="glass-card fade-in" style={{ animationDelay: '0.18s' }}>
          <div className="panel-header" style={{ marginBottom: '14px' }}>
            <div>
              <h2>Live markedspuls (efter {fe.current_period})</h2>
              <span className="panel-explainer">
                Nyeste månedlige udbudspriser (Finans Danmark UDB020) og dagsaktuelle annoncer (Boliga API), strengt adskilt fra DST EJ56.
              </span>
            </div>
          </div>

          <div className="pulse-metrics-list">
            <div className="pulse-metric-card">
              <div className="pulse-metric-top">
                <span>Officiel udbudspris (UDB020)</span>
                <span className="nowcast-period-pill">{formatPeriodDa(udb?.latest_period)}</span>
              </div>
              <div className="pulse-metric-main">
                <strong style={{ color: '#00d4aa' }}>{formatDkkSqm(udb?.latest_value)}</strong>
                <span
                  className="nowcast-delta-pill"
                  style={{
                    color: (udb?.since_dst_quarter_change_pct ?? 0) >= 0 ? '#00d4aa' : '#ff6b6b',
                    background: (udb?.since_dst_quarter_change_pct ?? 0) >= 0 ? 'rgba(0,212,170,0.12)' : 'rgba(255,107,107,0.12)',
                  }}
                >
                  {formatPct(udb?.since_dst_quarter_change_pct)} siden {fe.current_period}
                </span>
              </div>
              <div className="pulse-metric-meta">År/år: {formatPct(udb?.yoy_change_pct)} · Finans Danmark Statistikbank</div>
            </div>

            <div className="pulse-metric-card">
              <div className="pulse-metric-top">
                <span>Realtids aktive annoncer (Boliga)</span>
                <span className="nowcast-period-pill nowcast-period-live">Realtid</span>
              </div>
              <div className="pulse-metric-main">
                <strong style={{ color: '#a78bfa' }}>{formatDkkSqm(boliga?.median_dkk_sqm)}</strong>
                <span className="nowcast-yoy-text">Gns. {formatDkkSqm(boliga?.mean_dkk_sqm)}</span>
              </div>
              <div className="pulse-metric-meta">
                {boliga?.sample_size ? `${boliga.sample_size.toLocaleString('da-DK')} aktive boliger` : 'Ingen stikprøve'} · Hentet {boliga?.retrieved_at?.slice(0, 10) || '—'}
              </div>
            </div>

            <div className="pulse-metric-card">
              <div className="pulse-metric-top">
                <span>Samlet sårbarhedsindeks (EWI)</span>
                <span className="nowcast-period-pill" style={{ color: ewiAlert === 'NORMAL' ? '#00d4aa' : '#ff6b6b' }}>
                  {ewiAlert === 'HIGH' ? 'Høj' : ewiAlert === 'CRITICAL' ? 'Kritisk' : ewiAlert === 'ELEVATED' ? 'Forhøjet' : 'Normal'}
                </span>
              </div>
              <div className="pulse-metric-main">
                <strong style={{ color: ewiScore >= 9 ? '#ff6b6b' : '#ffc107' }}>
                  {typeof ewiScore === 'number' ? `${ewiScore.toFixed(1)} / 27` : '—'}
                </strong>
                <span className="nowcast-yoy-text">Indeks (ikke en procentchance)</span>
              </div>
              <div className="pulse-metric-meta">
                Baseret på 9 tidlige varslingsindikatorer (liggetid, prisafslag, DSR m.fl.)
              </div>
            </div>
          </div>

          <div className="pulse-actions">
            <button type="button" className="btn-control purple" onClick={() => onOpenTab('risk')}>
              🛡️ Se alle 9 indikatorer &amp; datakilder →
            </button>
            <button type="button" className="btn-control teal" onClick={() => onOpenTab('sandbox')}>
              🧪 Stresstest i Hvad-nu-hvis →
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
