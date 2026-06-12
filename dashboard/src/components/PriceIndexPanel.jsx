import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { priceIndexData } from '../data/housingData';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload) return null;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} style={{ color: entry.color }}>
          {entry.name}: <strong>{entry.value?.toFixed(1) ?? '—'}</strong>
        </p>
      ))}
      <p className="tooltip-hint">Indeks 100 = prisniveauet i 2006</p>
    </div>
  );
};

export default function PriceIndexPanel() {
  return (
    <section className="glass-card panel-wide fade-in" style={{ animationDelay: '0.1s' }}>
      <div className="panel-header">
        <div>
          <h2>Prisindeks — København</h2>
          <span className="panel-explainer">
            Kvartalsvise prisindeks for boliger i Hovedstadsområdet fra Danmarks Statistik (tabel EJ56).
            Base 2006 = 100, så en værdi på 129 betyder at priserne er steget 29% siden 2006.
            Data opdateret 2026-05-29.
          </span>
        </div>
        <span className="panel-badge">2019Q1 → 2025Q4</span>
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
              dataKey="cphApartments"
              name="KBH Ejerlejligheder"
              stroke="url(#gradTeal)"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#00d4aa', stroke: '#0a0e1a', strokeWidth: 2 }}
            />
            <Line
              type="monotone"
              dataKey="cphHouses"
              name="KBH Omegn Huse"
              stroke="url(#gradAmber)"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#ffc107', stroke: '#0a0e1a', strokeWidth: 2 }}
            />
            <Line
              type="monotone"
              dataKey="fredApartments"
              name="KBH Omegn Lejl."
              stroke="url(#gradPurple)"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#a78bfa', stroke: '#0a0e1a', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
