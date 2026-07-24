import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, LabelList
} from 'recharts';
import { useCity } from '../context/CityContext';

const ucExplainer = `Fundamental User Cost (brugeromkostning) er den løbende ejeromkostning ved at besidde en ejerbolig — inklusive renter efter skat, ejendomsskatter, vedligeholdelse og risikopræmie. Beregnet for en bolig til 3,0 mio. DKK med 80% belåning.`;

const scenarioTips = {
  'Baseline': 'Hovedscenarie: Moderat renteniveau. De fundamentale ejeromkostninger inkluderer rentefradrag (vægtet skattesats), ejendomsskatter, vedligeholdelse og risikopræmie.',
  'Min Risk': 'Optimistisk scenarie: Lavere renter reducerer de fundamentale ejeromkostninger betydeligt.',
  'Max Risk': 'Stress-test scenarie: Stigende renter og øget risikopræmie fører til væsentligt højere løbende finansieringsomkostninger.',
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{d.scenario}</p>
      <p style={{ color: d.color }}>
        Årlig UC-rate: <strong>{d?.ucRate > 0 ? '+' : ''}{d?.ucRate}%</strong> af boligværdien
      </p>
      <p style={{ color: d.color }}>
        Månedlig omkostning: <strong>{d?.monthly?.toLocaleString('da-DK') ?? '—'} DKK</strong>
      </p>
      <p className="tooltip-hint">Jo højere User Cost, jo større er den løbende ejerbyrde</p>
    </div>
  );
};

function CostCard({ data, index }) {
  const isNegative = data.monthly < 0;
  const isSevere = data.ucRate > 10;
  const tip = scenarioTips[data.scenario] || '';

  return (
    <div
      className={`cost-card fade-in tooltip`}
      data-tooltip={tip}
      style={{
        animationDelay: `${0.5 + index * 0.1}s`,
        borderColor: `${data.color}33`,
      }}
    >
      <div className="cost-card-header">
        <span className="cost-scenario" style={{ color: data.color }}>{data.scenario}</span>
        <span
          className="cost-icon"
          style={{
            color: data.color,
            background: `${data.color}18`,
          }}
        >
          {data.icon}
        </span>
      </div>
      <div className="cost-rate">
        <span className="cost-rate-value" style={{ color: data.color }}>
          {data.ucRate > 0 ? '+' : ''}{data.ucRate}%
        </span>
        <span className="cost-rate-label">Årlig UC-rate</span>
      </div>
      <div className="cost-monthly">
        <span className="cost-monthly-value">
          {data.monthly.toLocaleString('da-DK')} <small>DKK/md</small>
        </span>
      </div>
      <span
        className="cost-status-label"
        style={{
          color: isNegative ? '#3b82f6' : isSevere ? '#ff6b6b' : '#00d4aa',
          background: isNegative ? 'rgba(59,130,246,0.12)' : isSevere ? 'rgba(255,107,107,0.12)' : 'rgba(0,212,170,0.12)',
        }}
      >
        {data.label}
      </span>
    </div>
  );
}

export default function UserCostPanel() {
  const { pipelineData, activeCity } = useCity();
  if (!pipelineData) return null;
  
  const uc = pipelineData.user_costs;
  const userCostData = [
    { scenario: 'Baseline', ucRate: Math.round(uc.baseline['12m'].user_cost_breakdown.user_cost_rate * 10000)/100, monthly: uc.baseline['12m'].user_cost_breakdown.user_cost_monthly_dkk, label: uc.baseline['12m'].interpretation.assessment, color: '#00d4aa', icon: '✓' },
    { scenario: 'Min Risk', ucRate: Math.round(uc.min_risk['12m'].user_cost_breakdown.user_cost_rate * 10000)/100, monthly: uc.min_risk['12m'].user_cost_breakdown.user_cost_monthly_dkk, label: uc.min_risk['12m'].interpretation.assessment, color: '#3b82f6', icon: '✓' },
    { scenario: 'Max Risk', ucRate: Math.round(uc.max_risk['12m'].user_cost_breakdown.user_cost_rate * 10000)/100, monthly: uc.max_risk['12m'].user_cost_breakdown.user_cost_monthly_dkk, label: uc.max_risk['12m'].interpretation.assessment, color: '#ff6b6b', icon: '✗' },
  ];

  const chartData = userCostData;

  return (
    <section className="glass-card fade-in" style={{ animationDelay: '0.55s' }}>
      <div className="panel-header">
        <div>
          <h2>Brugeromkostning (User Cost)</h2>
          <span className="panel-explainer">{ucExplainer}</span>
        </div>
        <span className="panel-badge tooltip" data-tooltip="UC_fund beregnes med Nationalbankens/OECD formel: UC_fund = P × [r(1-τ_r) + τ_p + δ + rp]">12-måneders horisont</span>
      </div>
      <div className="cost-layout">
        <div className="cost-cards-row">
          {userCostData.map((d, i) => (
            <CostCard key={d.scenario} data={d} index={i} />
          ))}
        </div>
        <div className="cost-chart">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} margin={{ top: 20, right: 20, left: 20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis
                dataKey="scenario"
                stroke="rgba(255,255,255,0.4)"
                tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }}
              />
              <YAxis
                stroke="rgba(255,255,255,0.4)"
                tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                label={{ value: 'DKK/måned', angle: -90, position: 'insideLeft', style: { fill: 'rgba(255,255,255,0.4)', fontSize: 11 } }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="monthly" radius={6} barSize={48}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} fillOpacity={0.8} />
                ))}
                <LabelList
                  dataKey="monthly"
                  position="top"
                  formatter={(v) => `${v > 0 ? '+' : ''}${(v / 1000).toFixed(1)}k`}
                  style={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
