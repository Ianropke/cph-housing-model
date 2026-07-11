import { useState } from 'react';
import { useCity } from '../context/CityContext';

const tooltipDescriptions = {
  'Mortgage Rate (30Y Fixed)': 'Den gennemsnitlige 30-årige fastforrentede realkreditrente i Danmark. Aktuelt ca. 3,5-4%. Påvirker direkte den månedlige ydelse og dermed købernes råderum.',
  'ECB Deposit Rate Path': 'ECB\'s styringsrente styrer de korte danske renter via kronens fastkurspolitik. Når ECB sænker renten, falder de variable realkreditrenter typisk med 6-12 måneders forsinkelse.',
  'Wage Growth (Nominal YoY)': 'Forventet årlig lønstigning i Hovedstadsområdet. Lønvækst øger købekraften og understøtter boligpriserne — medmindre priserne stiger endnu hurtigere.',
  'Expected Appreciation': 'Forventet årlig prisstigning på boliger. Indgår i user cost-beregningen som en "rabat" — jo højere forventet stigning, jo billigere føles det at eje.',
  'Net Migration (CPH)': 'Nettotilflytning til København. Flere tilflyttere øger efterspørgslen efter boliger og presser priserne op, alt andet lige.',
  'Completions Pipeline (12m)': 'Nye boliger der forventes færdigbygget de næste 12 måneder. Mere nybyggeri øger udbuddet og kan dæmpe prisstigningerne.',
  'Rentefradrag': 'Skattefradraget for renteudgifter. I Danmark er det 33% af de første 50.000 kr. (100.000 kr. for par) og 25% derover. Reducerer den effektive rente.',
};

function ScenarioRow({ scenario, isOpen, onToggle, index }) {
  return (
    <div
      className="scenario-row fade-in"
      style={{
        animationDelay: `${0.7 + index * 0.08}s`,
        borderColor: `${scenario.color}22`,
      }}
    >
      <button className="scenario-toggle" onClick={onToggle} aria-expanded={isOpen}>
        <div className="scenario-toggle-left">
          <span className="scenario-dot" style={{ background: scenario.color }} />
          <span className="scenario-name">{scenario.scenario}</span>
          <span className="scenario-weight" style={{ color: scenario.color }}>
            {scenario.weight}
          </span>
        </div>
        <span className={`scenario-chevron ${isOpen ? 'open' : ''}`}>▾</span>
      </button>
      <div className={`scenario-details ${isOpen ? 'expanded' : ''}`}>
        <div className="assumptions-grid">
          {Object.entries(scenario.assumptions).map(([key, val]) => {
            const tooltip = tooltipDescriptions[key] || '';
            return (
              <div 
                key={key} 
                className={`assumption-item ${tooltip ? 'tooltip' : ''}`}
                data-tooltip={tooltip}
              >
                <span className="assumption-key">{key}</span>
                <span className="assumption-val" style={{ color: scenario.color }}>{val}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default function ScenarioAssumptionsPanel() {
  const { pipelineData, activeCity } = useCity();
  if (!pipelineData) return null;
  const fc = pipelineData.forecasts[`${activeCity}_apartments`];
  
  const scenarioAssumptions = [
    {
      scenario: 'Baseline', weight: `${(fc?.horizons['12m']?.scenarios?.baseline?.probability_weight || 0.55)*100}%`, color: '#00d4aa',
      assumptions: {
        'Mortgage Rate': '3.7% → 3.5%',
        'ECB Deposit': '2.75% → 2.0%',
        'Wage Growth': '3.5%',
        'Appreciation': '+2.0% → +6.0%',
        'Net Migration': '+8,500/yr',
        'Completions': '3,500 units'
      }
    },
    {
      scenario: 'Min Risk', weight: `${(fc?.horizons['12m']?.scenarios?.min_risk?.probability_weight || 0.20)*100}%`, color: '#3b82f6',
      assumptions: {
        'Mortgage Rate': '3.5% → 2.8%',
        'ECB Deposit': '2.75% → 1.0%',
        'Wage Growth': '4.5%',
        'Appreciation': '+4.5% → +15.0%',
        'Net Migration': '+11,000/yr',
        'Completions': '2,800 units'
      }
    },
    {
      scenario: 'Max Risk', weight: `${(fc?.horizons['12m']?.scenarios?.max_risk?.probability_weight || 0.25)*100}%`, color: '#ff6b6b',
      assumptions: {
        'Mortgage Rate': '5.0% → 6.0%',
        'ECB Deposit': '2.75% → 4.25%',
        'Wage Growth': '2.5%',
        'Appreciation': '-5.5% → -14.0%',
        'Net Migration': '+4,000/yr',
        'Completions': '5,500 units'
      }
    }
  ];

  const [openIndex, setOpenIndex] = useState(0);

  return (
    <section className="glass-card panel-wide fade-in" style={{ animationDelay: '0.7s' }}>
      <div className="panel-header">
        <div>
          <h2>Scenarie-antagelser</h2>
          <span className="panel-explainer">
            Hvert scenarie bygger på et sæt makroøkonomiske antagelser om renter, lønvækst, migration og nybyggeri.
            Klik for at se detaljerne. Hold musen over en parameter for at forstå dens betydning.
          </span>
        </div>
        <span className="panel-badge">Nøgleinput</span>
      </div>
      <div className="scenarios-list">
        {scenarioAssumptions.map((s, i) => (
          <ScenarioRow
            key={s.scenario}
            scenario={s}
            index={i}
            isOpen={openIndex === i}
            onToggle={() => setOpenIndex(openIndex === i ? -1 : i)}
          />
        ))}
      </div>
    </section>
  );
}
