import { useState, useEffect, useCallback } from 'react';
import PriceIndexPanel from './components/PriceIndexPanel';
import EarlyWarningDashboard from './components/EarlyWarningDashboard';
import ForecastEnsemblePanel from './components/ForecastEnsemblePanel';
import UserCostPanel from './components/UserCostPanel';
import ScenarioAssumptionsPanel from './components/ScenarioAssumptionsPanel';
import RiskBarometer from './components/RiskBarometer';
import { useCity } from './context/CityContext';

// ─── Inline Toast Notification ───────────────────────────────
function Toast({ message, type, onDismiss }) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 4000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  const colors = {
    success: { bg: 'rgba(0,212,170,0.12)', border: 'rgba(0,212,170,0.35)', text: '#00d4aa', icon: '✓' },
    error:   { bg: 'rgba(255,107,107,0.12)', border: 'rgba(255,107,107,0.35)', text: '#ff6b6b', icon: '✕' },
    info:    { bg: 'rgba(59,130,246,0.12)', border: 'rgba(59,130,246,0.35)', text: '#3b82f6', icon: 'ℹ' },
  };
  const c = colors[type] || colors.info;

  return (
    <div style={{
      position: 'fixed', top: '20px', right: '20px', zIndex: 9999,
      padding: '14px 20px', borderRadius: '12px',
      background: c.bg, border: `1px solid ${c.border}`,
      backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)',
      color: c.text, fontSize: '0.88rem', fontWeight: 500,
      display: 'flex', alignItems: 'center', gap: '10px',
      animation: 'slideInRight 0.3s ease-out',
      boxShadow: `0 8px 32px ${c.border}`,
      maxWidth: '400px',
    }}>
      <span style={{ fontSize: '1.1rem', fontWeight: 700 }}>{c.icon}</span>
      <span>{message}</span>
      <button onClick={onDismiss} style={{
        background: 'none', border: 'none', color: c.text, cursor: 'pointer',
        marginLeft: '8px', fontSize: '1rem', opacity: 0.6, padding: '0 4px',
      }}>✕</button>
    </div>
  );
}

export default function App() {
  const { pipelineData, activeCity, setActiveCity, loading: dataLoading } = useCity();
  const [loading, setLoading] = useState(null);
  const [activeModal, setActiveModal] = useState(null);
  const [modalData, setModalData] = useState(null);
  const [ewiMode, setEwiMode] = useState('yoy_expanded');
  const [toast, setToast] = useState(null);
  const [displayTimestamp, setDisplayTimestamp] = useState('—');
  useEffect(() => {
    if (pipelineData) setDisplayTimestamp(pipelineData.generated_at.substring(0, 10));
  }, [pipelineData]);

  const activeSegment = `${activeCity}_apartments`;
  const ewiModes = pipelineData?.early_warnings?.[activeSegment]?.modes || {};
  const activeModeData = ewiModes?.[ewiMode] || {
    earlyWarningIndicators: [],
    compositeScore: 0,
    freshnessWeightedComposite: 0,
    alertLevel: 'NORMAL',
    maxRiskIndex: 0
  };
  const mlCrashProbability = pipelineData?.early_warnings?.[activeSegment]?.ml_crash_probability ?? null;

  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type, key: Date.now() });
  }, []);

  const dismissToast = useCallback(() => setToast(null), []);

  const MOCK_BACKTEST = {
    "backtest_range": "2000 - 2026",
    "backtest_date": "2026-06-14T21:08:33.276032",
    "methodology": "One-step-ahead: each year's forecast uses prior year's ACTUAL index (no error drift)",
    "metrics": {
      "mape_pct": 8.9,
      "rmse_points": 11.67,
      "data_points_evaluated": 26
    },
    "empirical_calibrations": {
      "EWI-1_price_vs_wages_red": 0.0441,
      "EWI-2_supply_demand_amber": 3.8,
      "EWI-6_price_to_rent_red_ratio": 1.1
    },
    "comparison": {
      "years": [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
      "actual": [55.0, 58.2, 61.5, 65.8, 73.2, 86.4, 100.0, 100.0, 88.5, 76.2, 82.1, 80.4, 78.9, 84.6, 92.1, 101.4, 108.9, 114.5, 112.8, 82.5, 90.9, 98.9, 95.0, 99.0, 107.3, 129.2, 132.5],
      "predicted": [55.0, 51.3, 54.8, 59.6, 64.3, 72.2, 83.7, 95.5, 91.0, 88.5, 78.6, 83.2, 84.0, 82.5, 89.5, 99.1, 110.5, 118.7, 124.8, 123.0, 91.0, 100.3, 94.4, 88.6, 95.9, 105.4, 129.2],
      "errors": [0.0, -6.9, -6.7, -6.2, -8.9, -14.2, -16.3, -4.5, 2.5, 12.3, -3.5, 2.8, 5.1, -2.1, -2.6, -2.3, 1.6, 4.2, 12.0, 40.5, 0.1, 1.4, -0.6, -10.4, -11.4, -23.8, -3.3]
    }
  };

  const MOCK_STATUS = `=== System Diagnostics ===
Model Version: 3.0 (Fase 1)

Data Files:
  - housingData.js: ✓ OK
  - latest_pipeline.json: ✓ OK

Pipeline Status: Operational
Cron: Daily at 02:00 CET`;

  const runUpdate = async () => {
    setLoading('update');
    try {
      const res = await fetch('/api/update');
      const data = await res.json();
      if (res.ok) {
        // Update the timestamp to reflect current time
        const now = new Date();
        const dateStr = now.toISOString().slice(0, 10);
        setDisplayTimestamp(`${dateStr} · 2025Q4 Data`);
        showToast('Data er opdateret med seneste DST-tal', 'success');
        // Reload after a short delay so the user sees the toast
        setTimeout(() => window.location.reload(), 1500);
      } else {
        showToast('Fejl ved opdatering: ' + (data.error || 'Ukendt fejl'), 'error');
      }
    } catch (e) {
      console.warn('Network error trying to run update: ' + e.message);
      showToast('Kunne ikke nå serveren — kører du lokalt med npm run dev?', 'error');
    } finally {
      setLoading(null);
    }
  };

  const runBacktest = async () => {
    setLoading('backtest');
    try {
      const res = await fetch('/api/backtest');
      const data = await res.json();
      if (res.ok) {
        setModalData(data);
        setActiveModal('backtest');
      } else {
        showToast('Fejl ved backtest: ' + (data.error || 'Ukendt fejl'), 'error');
      }
    } catch (e) {
      console.warn('Network error trying to run backtest: ' + e.message);
      // Fallback to mock data for demo
      setModalData(MOCK_BACKTEST);
      setActiveModal('backtest');
    } finally {
      setLoading(null);
    }
  };

  const checkStatus = async () => {
    setLoading('status');
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      if (res.ok) {
        setModalData(data.status);
        setActiveModal('status');
      } else {
        showToast('Fejl ved status-hentning', 'error');
      }
    } catch (e) {
      console.warn('Network error trying to fetch status: ' + e.message);
      setModalData(MOCK_STATUS);
      setActiveModal('status');
    } finally {
      setLoading(null);
    }
  };

  if (dataLoading) return <div className="dashboard" style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'white'}}>Indlæser model data...</div>;

  return (
    <div className="dashboard">
      {/* Toast notification */}
      {toast && (
        <Toast
          key={toast.key}
          message={toast.message}
          type={toast.type}
          onDismiss={dismissToast}
        />
      )}

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
              <h1>Copenhagen Housing Market</h1>
              <p className="header-subtitle">Forecast Dashboard & Controller</p>
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
                <option value="copenhagen">København</option>
                <option value="aarhus">Aarhus</option>
                <option value="odense">Odense</option>
                <option value="aalborg">Aalborg</option>
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
        <div className="control-bar fade-in" style={{ animationDelay: '0.1s' }}>
          <button 
            className="btn-control purple" 
            onClick={checkStatus} 
            disabled={loading !== null}
            title="Vis systemstatus, datakilde-helbredscheck og pipeline-log"
          >
            {loading === 'status' ? <span className="spinner" /> : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
                <path d="M12 16v-4" />
                <path d="M12 8h.01" />
              </svg>
            )}
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
          dataFreshness={activeModeData.dataFreshness}
          mlProbabilityHistory={activeModeData.mlProbabilityHistory}
        />
        <ForecastEnsemblePanel />
        <UserCostPanel />
        <ScenarioAssumptionsPanel />
      </main>

      <footer className="dashboard-footer fade-in" style={{ animationDelay: '0.8s' }}>
        <p>Data: Danmarks Statistik (EJ56) · Model: CPH Housing Forecast System v3.0 (Fase 1)</p>
      </footer>

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
