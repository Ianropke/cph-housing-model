import { useState, useMemo } from 'react';
import PriceIndexPanel from './components/PriceIndexPanel';
import EarlyWarningDashboard from './components/EarlyWarningDashboard';
import ForecastEnsemblePanel from './components/ForecastEnsemblePanel';
import UserCostPanel from './components/UserCostPanel';
import ScenarioAssumptionsPanel from './components/ScenarioAssumptionsPanel';
import RiskBarometer from './components/RiskBarometer';
import ScenarioSandboxPanel from './components/ScenarioSandboxPanel';
import SkeletonLoader from './components/SkeletonLoader';
import OnboardingModal from './components/OnboardingModal';
import MethodologyModal from './components/MethodologyModal';
import { useCity } from './context/CityContext';

export default function App() {
  const {
    pipelineData,
    activeCity,
    setActiveCity,
    loading: dataLoading,
    dataStatus,
    dataErrors,
  } = useCity();
  const [activeModal, setActiveModal] = useState(null);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showMethodology, setShowMethodology] = useState(false);
  const [modalData, setModalData] = useState(null);
  const [ewiMode, setEwiMode] = useState('yoy_expanded');
  const displayTimestamp = useMemo(() => {
    if (!pipelineData?.generated_at) return '—';
    const date = new Date(pipelineData.generated_at);
    return Number.isNaN(date.getTime())
      ? pipelineData.generated_at.slice(0, 10)
      : date.toLocaleDateString('da-DK', { day: 'numeric', month: 'long', year: 'numeric' });
  }, [pipelineData]);

  const activeSegment = `${activeCity}_apartments`;
  const ewiModes = pipelineData?.early_warnings?.[activeSegment]?.modes || {};
  const activeModeData = ewiModes[ewiMode];
  const mlCrashProbability = activeModeData?.mlCrashProbability ?? null;

  const checkStatus = async () => {
    const status = pipelineData?.market_data_status;
    const sourceNames = Object.keys(status?.sources || {}).join(', ') || 'Ingen verificerede kilder';
    setModalData([
      '=== Systemdiagnostik ===',
      `Payload: ${dataStatus === 'live' ? 'LIVE' : dataStatus.toUpperCase()}`,
      `Genereret: ${pipelineData?.generated_at || 'Ukendt'}`,
      `Markedsdata: ${status?.status || 'Ukendt'}`,
      `Datakilder: ${sourceNames}`,
    ].join('\n'));
    setActiveModal('status');
  };

  if (dataLoading) return <div className="dashboard"><SkeletonLoader /></div>;

  if (!dataLoading && !pipelineData) {
    const isStale = dataStatus === 'stale';
    return (
      <div className="dashboard" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <div className="glass-card" style={{ textAlign: 'center', padding: '3rem', maxWidth: '500px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
          <h2 style={{ color: '#ff6b6b', marginBottom: '0.5rem' }}>
            {isStale ? 'Data er forældet' : 'Data Midlertidigt Utilgængelig'}
          </h2>
          <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            {isStale
              ? 'Dashboardet viser ikke modeltal, før pipeline-payloaden er opdateret og valideret.'
              : 'Dashboardet viser ikke modeltal, fordi den seneste pipeline-payload ikke kan verificeres.'}
          </p>
          {dataErrors.length > 0 && (
            <ul style={{ textAlign: 'left', color: 'rgba(255,255,255,0.55)', fontSize: '0.8rem', marginBottom: '1.5rem' }}>
              {dataErrors.slice(0, 4).map((error) => <li key={error}>{error}</li>)}
            </ul>
          )}
          <button 
            onClick={() => window.location.reload()} 
            style={{ padding: '10px 24px', borderRadius: '8px', background: '#3b82f6', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 600 }}
          >
            🔄 Genindlæs Data
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header fade-in">
        <div className="header-content">
          <div className="header-left">
            <div className="header-icon">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <rect x="2" y="2" width="28" height="28" rx="8" fill="rgba(0,212,170,0.12)" stroke="#00d4aa" strokeWidth="1.5" />
                <path d="M8 22L12 14L16 18L20 10L24 16" stroke="#00d4aa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div>
              <h1>Det Københavnske Boligmarked</h1>
              <p className="header-subtitle">Prognose- & Risikodashboard</p>
            <div className="city-selector" style={{ marginTop: '8px' }}>
              <select 
                value={activeCity} 
                onChange={(e) => setActiveCity(e.target.value)}
                style={{
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: 'white',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '0.9rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="copenhagen">København & Frederiksberg</option>
                <option value="aarhus" disabled>Aarhus (Kommer snart)</option>
                <option value="odense" disabled>Odense (Kommer snart)</option>
                <option value="aalborg" disabled>Aalborg (Kommer snart)</option>
              </select>
            </div>

            </div>
          </div>
          <div className="header-right">
            <div className="header-timestamp">
              <span className="timestamp-label">Sidst opdateret</span>
              <time>{displayTimestamp}</time>
            </div>
            <div className="header-status">
              <span className="status-dot" />
              Live
            </div>
          </div>
        </div>

        {/* Dynamic Action Control Bar */}
        <div className="control-bar fade-in" style={{ animationDelay: '0.1s', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button 
            className="btn-control purple" 
            onClick={() => setShowOnboarding(true)}
            title="Åbn onboarding intro og guide"
          >
            <span>❓</span> Guide & Intro
          </button>
          
          <button 
            className="btn-control purple" 
            onClick={() => setShowMethodology(true)}
            title="Åbn model-metodik, backtest-resultater og datadokumentation"
          >
            <span>🔬</span> Model-Metodik & Backtest
          </button>

          <button 
            className="btn-control purple" 
            onClick={checkStatus} 
            title="Vis systemstatus, datakilde-helbredscheck og pipeline-log"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>
            Systemstatus
          </button>
        </div>
      </header>

      <main className="dashboard-grid">
        <RiskBarometer maxRiskIndex={activeModeData.maxRiskIndex} />
        <PriceIndexPanel />
        <EarlyWarningDashboard 
          ewiMode={ewiMode} 
          setEwiMode={setEwiMode}
          indicators={activeModeData.earlyWarningIndicators}
          compositeScore={activeModeData.compositeScore}
          freshnessWeightedComposite={activeModeData.freshnessWeightedComposite}
          alertLevel={activeModeData.alertLevel}
          mlCrashProbability={mlCrashProbability}
          mlModelStatus={activeModeData.mlModelStatus}
          mlProbabilityHistory={activeModeData.mlProbabilityHistory}
          dataFreshness={activeModeData.dataFreshness}
        />
        <ScenarioSandboxPanel />
        <ForecastEnsemblePanel />
        <UserCostPanel />
        <ScenarioAssumptionsPanel />
      </main>

      <footer className="dashboard-footer fade-in" style={{ animationDelay: '0.8s', display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center', textAlign: 'center', padding: '30px 20px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'center', fontSize: '0.85rem' }}>
          <button onClick={() => setShowOnboarding(true)} style={{ background: 'none', border: 'none', color: '#00d4aa', cursor: 'pointer', textDecoration: 'underline' }}>
            ❓ Guide & Intro
          </button>
          <span>·</span>
          <button onClick={() => setShowMethodology(true)} style={{ background: 'none', border: 'none', color: '#a78bfa', cursor: 'pointer', textDecoration: 'underline' }}>
            🔬 Model-Metodik & Backtest
          </button>
          <span>·</span>
          <a href="https://github.com/Ianropke/cph-housing-model" target="_blank" rel="noopener noreferrer" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'underline' }}>
            💻 GitHub Repository & Kildekode
          </a>
        </div>
        <p style={{ margin: 0, fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)' }}>
          Data: Danmarks Statistik (EJ56, HUS1), Boliga Web API & Finans Danmark (RKR) · CPH Housing Forecast System v3.2
        </p>
        <p style={{ margin: 0, fontSize: '0.74rem', color: 'rgba(255,255,255,0.3)', maxWidth: '800px' }}>
          ⚖️ <em>Ansvarsfraskrivelse: Dette dashboard er et uafhængigt kvantitativt analyseværktøj udarbejdet til videnskabelig og analytisk brug. Indholdet udgør ikke finansiel investeringsrådgivning eller opfordring til køb/salg af ejendomme.</em>
        </p>
      </footer>

      {/* ONBOARDING & METHODOLOGY MODALS */}
      <OnboardingModal isOpen={showOnboarding} onClose={() => setShowOnboarding(false)} />
      <MethodologyModal isOpen={showMethodology} onClose={() => setShowMethodology(false)} />

      {/* MODAL DIALOGS */}
      {activeModal === 'backtest' && modalData && (
        <div className="modal-overlay" role="dialog" aria-modal="true" onClick={() => setActiveModal(null)} onKeyDown={(e) => { if (e.key === 'Escape') setActiveModal(null); }}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Historisk Backtest-kalibrering</h3>
              <button className="btn-close" aria-label="Close" onClick={() => setActiveModal(null)}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="modal-content">
              <div className="backtest-grid">
                <div className="backtest-metric-card">
                  <div className="backtest-metric-label">Mean Absolute Pct Error (MAPE)</div>
                  <div className="backtest-metric-value">{modalData.metrics.mape_pct}%</div>
                </div>
                <div className="backtest-metric-card">
                  <div className="backtest-metric-label">Root Mean Squared Error (RMSE)</div>
                  <div className="backtest-metric-value">{modalData.metrics.rmse_points} pts</div>
                </div>
              </div>
              
              <h4 style={{ marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Empirisk varslingskalibrering</h4>
              <div style={{ marginBottom: '20px', padding: '12px', background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.15)', borderRadius: '8px' }}>
                <p style={{ fontSize: '0.82rem', marginBottom: '4px' }}>• Pris-vs-Løn RØD-grænse: <strong>{(modalData.empirical_calibrations["EWI-1_price_vs_wages_red"] * 100).toFixed(1)}% spread</strong></p>
                <p style={{ fontSize: '0.82rem', marginBottom: '4px' }}>• Udbud-Efterspørgsel GUL-grænse: <strong>{modalData.empirical_calibrations["EWI-2_supply_demand_amber"]} måneder</strong></p>
                <p style={{ fontSize: '0.82rem' }}>• Pris-til-Leje RØD-ratio: <strong>{modalData.empirical_calibrations["EWI-6_price_to_rent_red_ratio"]} ratio</strong></p>
              </div>

              <h4 style={{ marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Historisk simulering</h4>
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                      <th style={{ padding: '6px' }}>År</th>
                      <th style={{ padding: '6px' }}>Faktisk indeks</th>
                      <th style={{ padding: '6px' }}>Model-prognose</th>
                      <th style={{ padding: '6px' }}>Absolut fejl</th>
                    </tr>
                  </thead>
                  <tbody>
                    {modalData.comparison.years.map((year, idx) => (
                      <tr key={year} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '6px' }}>{year}</td>
                        <td style={{ padding: '6px' }}>{modalData.comparison.actual[idx].toFixed(1)}</td>
                        <td style={{ padding: '6px' }}>{modalData.comparison.predicted[idx].toFixed(1)}</td>
                        <td style={{ padding: '6px', color: modalData.comparison.errors[idx] > 0 ? 'var(--coral)' : 'var(--teal)' }}>
                          {modalData.comparison.errors[idx] > 0 ? '+' : ''}{modalData.comparison.errors[idx].toFixed(1)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeModal === 'status' && modalData && (
        <div className="modal-overlay" role="dialog" aria-modal="true" onClick={() => setActiveModal(null)} onKeyDown={(e) => { if (e.key === 'Escape') setActiveModal(null); }}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '720px' }}>
            <div className="modal-header">
              <h3>Systemdiagnostik</h3>
              <button className="btn-close" aria-label="Close" onClick={() => setActiveModal(null)}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="modal-content">
              <pre className="pre-wrap">{modalData}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
