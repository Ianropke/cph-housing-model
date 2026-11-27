import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { useCity } from '../context/CityContext';

const formatDkkSqm = (val) => (
  typeof val === 'number' && Number.isFinite(val)
    ? `${Math.round(val).toLocaleString('da-DK')} kr./m²`
    : '—'
);

const formatSignedPct = (val) => {
  if (typeof val !== 'number' || !Number.isFinite(val)) return '—';
  const sign = val > 0 ? '+' : '';
  return `${sign}${val.toFixed(1).replace('.', ',')}%`;
};

const formatPeriodDa = (period) => {
  if (typeof period !== 'string') return 'Ukendt';
  const match = period.match(/^(\d{4})M(\d{2})$/);
  if (!match) return period;
  const months = ['jan.', 'feb.', 'mar.', 'apr.', 'maj', 'jun.', 'jul.', 'aug.', 'sep.', 'okt.', 'nov.', 'dec.'];
  const idx = Number(match[2]) - 1;
  return months[idx] ? `${months[idx]} ${match[1]}` : period;
};

const NowcastTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="tooltip-title">{formatPeriodDa(label)} ({label})</div>
      <div className="tooltip-divider" />
      {payload.map((entry) => (
        <div className="tooltip-row" key={entry.name}>
          <span className="tooltip-dot" style={{ background: entry.color }} />
          <span className="tooltip-label">{entry.name}:</span>
          <span className="tooltip-value">{formatDkkSqm(entry.value)}</span>
        </div>
      ))}
      <div className="tooltip-hint">Officiel udbudspris (Finans Danmark UDB020) — ikke tinglyst handelspris.</div>
    </div>
  );
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload) return null;
  return (
    <div className="chart-tooltip">
      <div className="tooltip-title">{label}</div>
      <div className="tooltip-divider" />
      {payload.map((entry) => (
        <div className="tooltip-row" key={entry.name}>
          <span className="tooltip-dot" style={{ background: entry.color }} />
          <span className="tooltip-label">{entry.name}:</span>
          <span className="tooltip-value">{entry.value?.toFixed(1) ?? '—'}</span>
        </div>
      ))}
      <div className="tooltip-hint">Indeks (2006 = 100). Basisår 2006 = 100.</div>
    </div>
  );
};

const CITY_LABELS = {
  copenhagen: 'København',
  aarhus: 'Aarhus',
  odense: 'Odense',
  aalborg: 'Aalborg',
};

export default function PriceIndexPanel() {
  const { pipelineData, activeCity } = useCity();
  
  if (!pipelineData) return null;
    
  const aptSeg = `${activeCity}_apartments`;
  const houseSeg = `${activeCity}_houses`;
  
  const aptData = pipelineData.dst_data.segments[aptSeg]?.series || {};
  const houseData = pipelineData.dst_data.segments[houseSeg]?.series || {};
  
  const quarters = Object.keys(aptData).sort();
  const priceIndexData = quarters.map(q => ({
    quarter: q,
    apartments: aptData[q],
    houses: houseData[q]
  }));

  const dstLastUpdated = pipelineData.dst_data.last_updated || '2026-05-29';
  const startQuarter = priceIndexData[0]?.quarter || '2019Q1';
  const endQuarter = priceIndexData[priceIndexData.length - 1]?.quarter || '2025Q4';
  const cityLabel = CITY_LABELS[activeCity] || (activeCity.charAt(0).toUpperCase() + activeCity.slice(1));

  // Separate Asking-Price Nowcast layer (strictly distinct from official DST EJ56 index)
  const aptNowcast = pipelineData.asking_price_nowcast?.[aptSeg] || null;
  const houseNowcast = pipelineData.asking_price_nowcast?.[houseSeg] || null;
  const aptUdb = aptNowcast?.rkr_udb020 || null;
  const houseUdb = houseNowcast?.rkr_udb020 || null;
  const boligaRt = aptNowcast?.boliga_realtime || null;
  const hasNowcast = Boolean(aptUdb?.series && Object.keys(aptUdb.series).length > 0);

  const nowcastPeriods = hasNowcast ? Object.keys(aptUdb.series).sort() : [];
  const nowcastChartData = nowcastPeriods.map((p) => ({
    period: p,
    apartments: aptUdb.series[p],
    houses: houseUdb?.series?.[p] ?? null,
  }));
  const anchorPeriod = aptUdb?.anchor_period || null;
  const boligaDate = boligaRt?.retrieved_at ? boligaRt.retrieved_at.slice(0, 10) : null;

  return (
    <section className="glass-card panel-wide fade-in" style={{ animationDelay: '0.1s' }}>
      <div className="panel-header">
        <div>
          <h2>Prisindeks — {cityLabel}</h2>
          <span className="panel-explainer">
            Kvartalsvise prisindeks for boliger i Hovedstadsområdet fra Danmarks Statistik (tabel EJ56).
            Base 2006 = 100, så en værdi på 140 betyder at priserne er steget 40% siden 2006.
            Data opdateret {dstLastUpdated}.
          </span>
        </div>
        <span className="panel-badge">{startQuarter} → {endQuarter}</span>
      </div>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={340}>
          <LineChart data={priceIndexData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <defs>
              <linearGradient id="gradTeal" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#00d4aa" stopOpacity={0.8} />
                <stop offset="100%" stopColor="#00d4aa" stopOpacity={1} />
              </linearGradient>
              <linearGradient id="gradAmber" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#ffc107" stopOpacity={0.8} />
                <stop offset="100%" stopColor="#ffc107" stopOpacity={1} />
              </linearGradient>
              <linearGradient id="gradPurple" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#a78bfa" stopOpacity={0.8} />
                <stop offset="100%" stopColor="#a78bfa" stopOpacity={1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="quarter"
              stroke="rgba(255,255,255,0.4)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              interval={3}
            />
            <YAxis
              stroke="rgba(255,255,255,0.4)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              domain={['dataMin - 5', 'dataMax + 5']}
              label={{ value: 'Indeks (2006=100)', angle: -90, position: 'insideLeft', style: { fill: 'rgba(255,255,255,0.4)', fontSize: 11 } }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: 10 }}
              iconType="circle"
              formatter={(value) => <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>{value}</span>}
            />
            <Line
              type="monotone"
              dataKey="apartments"
              name="Ejerlejligheder"
              stroke="url(#gradTeal)"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#00d4aa', stroke: '#0a0e1a', strokeWidth: 2 }}
            />
            <Line
              type="monotone"
              dataKey="houses"
              name="Huse"
              stroke="url(#gradAmber)"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#ffc107', stroke: '#0a0e1a', strokeWidth: 2 }}
            />
            
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* SEPARATE ASKING-PRICE NOWCAST LAYER (BETWEEN DST QUARTERS) */}
      <div className="nowcast-section">
        <div className="nowcast-header">
          <div>
            <h3 className="nowcast-title">Udbudspris-nowcast efter {endQuarter}</h3>
            <p className="nowcast-explainer">
              Separat udbudspris-signal (kr./m²) til at følge prisretningen mellem Danmarks Statistiks kvartalsudgivelser.
              Udbudspriser er ikke tinglyste handelspriser og blandes ikke ind i EJ56-indekset ovenfor.
            </p>
          </div>
          <span className="panel-badge nowcast-badge">
            {hasNowcast ? `RKR UDB020 (${aptUdb.latest_period}) + Boliga realtid` : 'Utilgængelig'}
          </span>
        </div>

        {!hasNowcast ? (
          <div className="nowcast-unavailable">
            Månedligt udbudspris-nowcast er midlertidigt utilgængeligt for dette segment.
          </div>
        ) : (
          <>
            <div className="nowcast-cards-grid">
              {/* Card 1: Apartments RKR UDB020 */}
              <div className="nowcast-card">
                <div className="nowcast-card-top">
                  <span className="nowcast-card-label">Ejerlejligheder · UDB020</span>
                  <span className="nowcast-period-pill">{formatPeriodDa(aptUdb.latest_period)}</span>
                </div>
                <div className="nowcast-card-value" style={{ color: '#00d4aa' }}>
                  {formatDkkSqm(aptUdb.latest_value)}
                </div>
                <div className="nowcast-card-deltas">
                  <span
                    className="nowcast-delta-pill"
                    style={{
                      color: (aptUdb.since_dst_quarter_change_pct ?? 0) >= 0 ? '#00d4aa' : '#ff6b6b',
                      background: (aptUdb.since_dst_quarter_change_pct ?? 0) >= 0 ? 'rgba(0,212,170,0.12)' : 'rgba(255,107,107,0.12)',
                    }}
                  >
                    {formatSignedPct(aptUdb.since_dst_quarter_change_pct)} siden {endQuarter}
                  </span>
                  <span className="nowcast-yoy-text">
                    {formatSignedPct(aptUdb.yoy_change_pct)} år/år
                  </span>
                </div>
                <span className="nowcast-source-meta">
                  Kilde: Finans Danmark Statistikbank ({aptUdb.table}, obs. {aptUdb.latest_period})
                </span>
              </div>

              {/* Card 2: Houses RKR UDB020 */}
              <div className="nowcast-card">
                <div className="nowcast-card-top">
                  <span className="nowcast-card-label">Huse · UDB020</span>
                  <span className="nowcast-period-pill">{formatPeriodDa(houseUdb?.latest_period)}</span>
                </div>
                <div className="nowcast-card-value" style={{ color: '#ffc107' }}>
                  {formatDkkSqm(houseUdb?.latest_value)}
                </div>
                <div className="nowcast-card-deltas">
                  <span
                    className="nowcast-delta-pill"
                    style={{
                      color: (houseUdb?.since_dst_quarter_change_pct ?? 0) >= 0 ? '#00d4aa' : '#ff6b6b',
                      background: (houseUdb?.since_dst_quarter_change_pct ?? 0) >= 0 ? 'rgba(0,212,170,0.12)' : 'rgba(255,107,107,0.12)',
                    }}
                  >
                    {formatSignedPct(houseUdb?.since_dst_quarter_change_pct)} siden {endQuarter}
                  </span>
                  <span className="nowcast-yoy-text">
                    {formatSignedPct(houseUdb?.yoy_change_pct)} år/år
                  </span>
                </div>
                <span className="nowcast-source-meta">
                  Kilde: Finans Danmark Statistikbank ({houseUdb?.table || 'UDB020'}, obs. {houseUdb?.latest_period || '—'})
                </span>
              </div>

              {/* Card 3: Boliga real-time active listings */}
              <div className="nowcast-card">
                <div className="nowcast-card-top">
                  <span className="nowcast-card-label">Aktive annoncer · Boliga</span>
                  <span className="nowcast-period-pill nowcast-period-live">Realtid</span>
                </div>
                <div className="nowcast-card-value" style={{ color: '#a78bfa' }}>
                  {formatDkkSqm(boligaRt?.median_dkk_sqm)}
                </div>
                <div className="nowcast-card-deltas">
                  <span className="nowcast-yoy-text">
                    Median · Gns. {formatDkkSqm(boligaRt?.mean_dkk_sqm)}
                  </span>
                </div>
                <span className="nowcast-source-meta">
                  København Kommune · {boligaRt?.sample_size ? `${boligaRt.sample_size.toLocaleString('da-DK')} aktive lejl.` : 'Ingen stikprøve'} · Hentet {boligaDate || '—'}
                </span>
              </div>
            </div>

            <div className="nowcast-chart-wrap">
              <div className="nowcast-chart-caption">
                Månedlig udbudspris (kr./m²) — seneste 13 måneder ({nowcastPeriods[0]} → {nowcastPeriods[nowcastPeriods.length - 1]})
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={nowcastChartData} margin={{ top: 16, right: 18, left: 4, bottom: 6 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    dataKey="period"
                    tickFormatter={formatPeriodDa}
                    stroke="rgba(255,255,255,0.35)"
                    tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
                    minTickGap={30}
                  />
                  <YAxis
                    stroke="rgba(255,255,255,0.35)"
                    tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
                    domain={['dataMin - 1500', 'dataMax + 1500']}
                    tickFormatter={(v) => `${Math.round(v / 1000)}k`}
                    width={46}
                  />
                  <Tooltip content={<NowcastTooltip />} />
                  <Legend
                    wrapperStyle={{ paddingTop: 6 }}
                    iconType="circle"
                    formatter={(value) => <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 11 }}>{value}</span>}
                  />
                  {anchorPeriod && (
                    <ReferenceLine
                      x={anchorPeriod}
                      stroke="rgba(167,139,250,0.65)"
                      strokeDasharray="4 4"
                      label={{
                        value: `DST ${endQuarter} slut`,
                        position: 'insideTopRight',
                        fill: '#a78bfa',
                        fontSize: 10,
                      }}
                    />
                  )}
                  <Line
                    type="monotone"
                    dataKey="apartments"
                    name="Ejerlejligheder (UDB020)"
                    stroke="#00d4aa"
                    strokeWidth={2.2}
                    dot={{ r: 3, fill: '#00d4aa', strokeWidth: 0 }}
                    activeDot={{ r: 5, fill: '#00d4aa', stroke: '#0a0e1a', strokeWidth: 2 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="houses"
                    name="Huse (UDB020)"
                    stroke="#ffc107"
                    strokeWidth={2.2}
                    dot={{ r: 3, fill: '#ffc107', strokeWidth: 0 }}
                    activeDot={{ r: 5, fill: '#ffc107', stroke: '#0a0e1a', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
