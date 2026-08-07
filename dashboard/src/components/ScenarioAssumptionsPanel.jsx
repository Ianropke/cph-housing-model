import { useState } from 'react';
import { useCity } from '../context/CityContext';

const tooltipDescriptions = {
  'Realkreditrente (30Y)': 'Den gennemsnitlige 30-årige fastforrentede realkreditrente i Danmark. Aktuelt ca. 3,5-4%. Påvirker direkte den månedlige ydelse og dermed købernes råderum.',
  'ECB Styringsrente': 'ECB\'s depositumrente styrer de korte danske renter via kronens fastkurspolitik. Når ECB sænker renten, falder de variable realkreditrenter typisk med 6-12 måneders forsinkelse.',
  'Lønvækst (YoY)': 'Forventet årlig lønstigning i Hovedstadsområdet. Lønvækst øger købekraften og understøtter boligpriserne — medmindre priserne stiger endnu hurtigere.',
  'Forventet Prisændring': 'Forventet årlig prisstigning/fald på boliger. Indgår i user cost-beregningen som en "rabat" — jo højere forventet stigning, jo billigere føles det at eje.',
  'Nettotilflytning (CPH)': 'Nettotilflytning til København. Flere tilflyttere øger efterspørgslen efter boliger og presser priserne op, alt andet lige.',
  'Nybyggeri Pipeline': 'Nye boliger der forventes færdigbygget de næste 12 måneder. Mere nybyggeri øger udbuddet og kan dæmpe prisstigningerne.',
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
            Sandsynlighedsvægt: {scenario.weight}
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
      scenario: 'Baseline (Hovedscenarie)', weight: `${(fc?.horizons['12m']?.scenarios?.baseline?.probability_weight || 0.55)*100}%`, color: '#00d4aa',
      assumptions: {
        'Realkreditrente (30Y)': '3.7% → 3.5%',
        'ECB Styringsrente': '2.75% → 2.0%',
        'Lønvækst (YoY)': '3.5%',
        'Forventet Prisændring': '+2.0% → +6.0%',
        'Nettotilflytning (CPH)': '+8.500 pers/år',
        'Nybyggeri Pipeline': '3.500 boliger'
      }
    },
    {
      scenario: 'Min Risk (Højkonjunktur / Lavrente)', weight: `${(fc?.horizons['12m']?.scenarios?.min_risk?.probability_weight || 0.20)*100}%`, color: '#3b82f6',
      assumptions: {
        'Realkreditrente (30Y)': '3.5% → 2.8%',
        'ECB Styringsrente': '2.75% → 1.0%',
        'Lønvækst (YoY)': '4.5%',
        'Forventet Prisændring': '+4.5% → +15.0%',
        'Nettotilflytning (CPH)': '+11.000 pers/år',
        'Nybyggeri Pipeline': '2.800 boliger'
      }
    },
    {
      scenario: 'Max Risk (Makrochok / Rentestød)', weight: `${(fc?.horizons['12m']?.scenarios?.max_risk?.probability_weight || 0.25)*100}%`, color: '#ff6b6b',
      assumptions: {
        'Realkreditrente (30Y)': '5.0% → 6.0%',
        'ECB Styringsrente': '2.75% → 4.25%',
        'Lønvækst (YoY)': '2.5%',
        'Forventet Prisændring': '-5.5% → -14.0%',
        'Nettotilflytning (CPH)': '+4.000 pers/år',
        'Nybyggeri Pipeline': '5.500 boliger'
      }
    }
  ];

  const [openIndex, setOpenIndex] = useState(0);

  return (
    <section className="glass-card panel-wide fade-in" style={{ animationDelay: '0.7s' }}>
      <div className="panel-header">
        <div>
          <h2>Scenarie-Antagelser & Vægtningsforudsætninger</h2>
          <span className="panel-explainer">
            Modelantagelser for hver af de tre markedsstier (Baseline, Min Risk, Max Risk) kalibreret mod historiske makrochok (2008 og 2022).
          </span>
        </div>
        <span className="panel-badge">Model-Parametre</span>
      </div>

      <div className="scenarios-list">
        {scenarioAssumptions.map((sc, i) => (
          <ScenarioRow
            key={sc.scenario}
            scenario={sc}
            isOpen={openIndex === i}
            onToggle={() => setOpenIndex(openIndex === i ? -1 : i)}
            index={i}
          />
        ))}
      </div>
    </section>
  );
}
