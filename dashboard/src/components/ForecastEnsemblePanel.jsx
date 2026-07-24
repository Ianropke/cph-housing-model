import {
  Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Line, ComposedChart
} from 'recharts';
import { useCity } from '../context/CityContext';

const scenarioTooltips = {
  'Baseline': 'Hovedscenarie (55% vægt): Gradvis rentesænkning, stabil lønvækst og moderat prisstigning.',
  'Min Risk': 'Optimistisk scenarie (20% vægt): Rentesænkninger og høj efterspørgsel driver priserne stærkere op.',
  'Max Risk': 'Stress-test scenarie (25% vægt): Rentestigninger og konjunkturtilbagegang fører til beregnet prisfald.',
};

const CustomTooltip = ({ active, payload, label, ensembleConfidenceBounds }) => {
  if (!active || !payload) return null;
  const horizon = label;
  const bounds = ensembleConfidenceBounds ? ensembleConfidenceBounds[horizon] : null;
  
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">Horisont: {label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} style={{ color: entry.color || entry.fill }}>
          {entry.name}: <strong>{entry.value?.toFixed(1) ?? '—'}</strong>
        </p>
      ))}
      {bounds && (
        <p style={{ color: 'rgba(255,255,255,0.5)', borderTop: '1px solid rgba(255,255,255,0.1)', marginTop: '6px', paddingTop: '6px', fontSize: '11px' }}>
          Monte Carlo 90% konfidensinterval: <strong>[{bounds.p10.toFixed(1)} – {bounds.p90.toFixed(1)}]</strong>
        </p>
      )}
      <p className="tooltip-hint">Forventet indeksværdi (Base 2006 = 100)</p>
    </div>
  );
};

// We create a wrapper to pass down ensembleConfidenceBounds since CustomTooltip is instantiated by Recharts
const CustomTooltipWrapper = (props) => {
  return <CustomTooltip {...props} />;
};

export default function ForecastEnsemblePanel() {
  const { pipelineData, activeCity } = useCity();
  if (!pipelineData) return null;
  
  const segment = `${activeCity}_apartments`;
  const fc = pipelineData.forecasts[segment];
  if (!fc) return null;
  
  const forecastBarData = ['6m', '12m', '24m'].map(h => ({
    horizon: h,
    Baseline: fc.horizons[h].scenarios.baseline.forecast_index,
    'Min Risk': fc.horizons[h].scenarios.min_risk.forecast_index,
    'Max Risk': fc.horizons[h].scenarios.max_risk.forecast_index,
    Ensemble: fc.horizons[h].ensemble.probability_weighted_index,
  }));
  
  const forecastScenarios = [
    { scenario: 'Baseline', weight: fc.horizons['12m'].scenarios.baseline.probability_weight, color: '#00d4aa' },
    { scenario: 'Min Risk', weight: fc.horizons['12m'].scenarios.min_risk.probability_weight, color: '#3b82f6' },
    { scenario: 'Max Risk', weight: fc.horizons['12m'].scenarios.max_risk.probability_weight, color: '#ff6b6b' },
  ];

  const ensembleForecasts = {
    '6m': fc.horizons['6m'].ensemble.probability_weighted_index,
    '12m': fc.horizons['12m'].ensemble.probability_weighted_index,
    '24m': fc.horizons['24m'].ensemble.probability_weighted_index,
  };
  
  const ensembleConfidenceBounds = {
    '6m': fc.horizons['6m'].ensemble.confidence_bounds,
    '12m': fc.horizons['12m'].ensemble.confidence_bounds,
    '24m': fc.horizons['24m'].ensemble.confidence_bounds,
  };

  return (
    <section className="glass-card fade-in" style={{ animationDelay: '0.4s' }}>
      <div className="panel-header">
        <div>
          <h2>Prisprognose</h2>
          <span className="panel-explainer">
            Forventet prisudvikling over 6, 12 og 24 måneder. Hvert scenarie har en sandsynlighedsvægt.
            Den hvide linje viser det vægtede gennemsnit (ensemble). Konfidensintervallet (CI) viser 80% af Monte Carlo-simuleringerne.
          </span>
        </div>
        <div className="scenario-weights">
          {forecastScenarios.map((s) => (
            <span key={s.scenario}
              className="weight-badge tooltip"
              data-tooltip={scenarioTooltips[s.scenario]}
              style={{ color: s.color, borderColor: `${s.color}44` }}
            >
              {s.scenario} ({(s.weight * 100).toFixed(0)}%)
            </span>
          ))}
        </div>
      </div>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={forecastBarData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="horizon"
              stroke="rgba(255,255,255,0.4)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }}
            />
            <YAxis
              stroke="rgba(255,255,255,0.4)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              domain={['auto', 'auto']}
              label={{ value: 'Forventet indeks', angle: -90, position: 'insideLeft', style: { fill: 'rgba(255,255,255,0.4)', fontSize: 11 } }}
            />
            <Tooltip content={<CustomTooltipWrapper ensembleConfidenceBounds={ensembleConfidenceBounds} />} />
            <Legend
              wrapperStyle={{ paddingTop: 10 }}
              formatter={(value) => <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>{value}</span>}
            />
            <Bar dataKey="Baseline" fill="#00d4aa" radius={[4, 4, 0, 0]} barSize={28} fillOpacity={0.85} />
            <Bar dataKey="Min Risk" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={28} fillOpacity={0.85} />
            <Bar dataKey="Max Risk" fill="#ff6b6b" radius={[4, 4, 0, 0]} barSize={28} fillOpacity={0.85} />
            <Line
              type="monotone"
              dataKey="Ensemble"
              name="Ensemble (vægtet gns.)"
              stroke="#e2e8f0"
              strokeWidth={2.5}
              strokeDasharray="6 3"
              dot={{ r: 5, fill: '#e2e8f0', stroke: '#0a0e1a', strokeWidth: 2 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      {/* Ensemble summary row */}
      <div className="ensemble-summary">
        {Object.entries(ensembleForecasts).map(([h, v]) => {
          const bounds = ensembleConfidenceBounds ? ensembleConfidenceBounds[h] : null;
          return (
            <div key={h} className="ensemble-val tooltip"
              data-tooltip={`Sandsynlighedsvægtet prisindeks om ${h}. Beregnet som: Baseline×55% + Min Risk×20% + Max Risk×25%.`}
            >
              <span className="ensemble-label">{h} Ensemble</span>
              <span className="ensemble-number">{v.toFixed(1)}</span>
              {bounds && (
                <span className="ensemble-bounds" style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginTop: '4px' }}>
                  90% CI: [{bounds.p10.toFixed(1)} – {bounds.p90.toFixed(1)}]
                </span>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
