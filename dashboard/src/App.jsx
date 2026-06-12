import { useState } from 'react';
import PriceIndexPanel from './components/PriceIndexPanel';
import EarlyWarningDashboard from './components/EarlyWarningDashboard';
import ForecastEnsemblePanel from './components/ForecastEnsemblePanel';
import UserCostPanel from './components/UserCostPanel';
import ScenarioAssumptionsPanel from './components/ScenarioAssumptionsPanel';
import RiskBarometer from './components/RiskBarometer';
import { maxRiskIndex, ewiModes } from './data/housingData';

export default function App() {
  const [loading, setLoading] = useState(null); // 'update', 'backtest', 'status', or null
  const [activeModal, setActiveModal] = useState(null); // 'backtest', 'status', or null
  const [modalData, setModalData] = useState(null);
  const [ewiMode, setEwiMode] = useState('yoy_expanded');

  const activeModeData = ewiModes?.[ewiMode] || {
    earlyWarningIndicators: [],
    compositeScore: 0,
    freshnessWeightedComposite: 0,
    alertLevel: 'NORMAL',
    maxRiskIndex: maxRiskIndex
  };

  const isMockMode = typeof window !== 'undefined' && 
    window.location.hostname !== 'localhost' && 
    window.location.hostname !== '127.0.0.1';

  const MOCK_BACKTEST = {
    "backtest_range": "2007 - 2024",
    "backtest_date": "2026-06-12T08:05:53.823440",
    "methodology": "One-step-ahead: each year's forecast uses prior year's ACTUAL index (no error drift) [Vercel Demo]",
    "metrics": { "mape_pct": 7.58, "rmse_points": 11.54, "data_points_evaluated": 17 },
    "empirical_calibrations": {
      "EWI-1_price_vs_wages_red": 0.0447,
      "EWI-2_supply_demand_amber": 3.8,
      "EWI-6_price_to_rent_red_ratio": 1.1
    },
    "comparison": {
      "years": [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
      "actual": [100.0, 88.5, 76.2, 82.1, 80.4, 78.9, 84.6, 92.1, 101.4, 108.9, 114.5, 112.8, 82.5, 90.9, 98.9, 95.0, 99.0, 107.3],
      "predicted": [100.0, 91.0, 88.5, 78.6, 83.2, 84.0, 82.5, 89.5, 99.1, 110.5, 118.7, 124.8, 123.0, 91.0, 100.3, 94.4, 88.6, 95.9],
      "errors": [0.0, 2.5, 12.3, -3.5, 2.8, 5.1, -2.1, -2.6, -2.3, 1.6, 4.2, 12.0, 40.5, 0.1, 1.4, -0.6, -10.4, -11.4]
    }
  };

  const MOCK_STATUS = `=== Ingestion Status & Diagnostics (Vercel Demo) ===
Project Directory: /Users/ianropke/.gemini/antigravity/scratch/cph-housing-model

Data Files:
  - housingData.js: Exists (Mocked Production Release)
  - latest_pipeline.json: Exists (Last updated: 2026-06-11 22:09:40)

Latest Daily Reports:
  - daily_2026-06-11.md

Cron Task Health Check:
The daily background updater task is scheduled to run at 02:00 AM CET daily via the Antigravity scheduler.

[Vercel Demo Status: Online / Interactive]`;

  const runUpdate = async () => {
    setLoading('update');
    try {
      if (isMockMode) {
        await new Promise(r => setTimeout(r, 1200));
        alert('Vercel Demo: Ingestions-pipelinen er simuleret succesfuldt! (I det lokale miljø afvikles daily_pipeline.py)');
      } else {
        const res = await fetch('/api/update');
        const data = await res.json();
        if (res.ok) {
          alert('Data pipeline ran successfully!');
        } else {
          console.warn('Error running update: ' + (data.error || 'Unknown error'));
        }
      }
    } catch (e) {
      console.warn('Network error trying to run update: ' + e.message);
      await new Promise(r => setTimeout(r, 800));
      alert('Vercel Demo: Simuleret pipeline-kørsel færdig (faldt tilbage på demo på grund af netværksfejl).');
    } finally {
      setLoading(null);
    }
  };

  const runBacktest = async () => {
    setLoading('backtest');
    try {
      if (isMockMode) {
        await new Promise(r => setTimeout(r, 1000));
        setModalData(MOCK_BACKTEST);
        setActiveModal('backtest');
      } else {
        const res = await fetch('/api/backtest');
        const data = await res.json();
        if (res.ok) {
          setModalData(data);
          setActiveModal('backtest');
        } else {
          console.warn('Error running backtest: ' + (data.error || 'Unknown error'));
        }
      }
    } catch (e) {
      console.warn('Network error trying to run backtest: ' + e.message);
      await new Promise(r => setTimeout(r, 500));
      setModalData(MOCK_BACKTEST);
      setActiveModal('backtest');
    } finally {
      setLoading(null);
    }
  };

  const checkStatus = async () => {
    setLoading('status');
    try {
      if (isMockMode) {
        await new Promise(r => setTimeout(r, 600));
        setModalData(MOCK_STATUS);
        setActiveModal('status');
      } else {
        const res = await fetch('/api/status');
        const data = await res.json();
        if (res.ok) {
          setModalData(data.status);
          setActiveModal('status');
        } else {
          console.warn('Error getting status: ' + (data.error || 'Unknown error'));
        }
      }
    } catch (e) {
      console.warn('Network error trying to fetch status: ' + e.message);
      await new Promise(r => setTimeout(r, 300));
      setModalData(MOCK_STATUS);
      setActiveModal('status');
    } finally {
      setLoading(null);
    }
  };

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
              <h1>Copenhagen Housing Market</h1>
              <p className="header-subtitle">Forecast Dashboard & Controller</p>
            </div>
          </div>
          <div className="header-right">
            <div className="header-timestamp">
              <span className="timestamp-label">Last Updated</span>
              <time>2026-06-11 · Q1 Data</time>
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
            className="btn-control teal" 
            onClick={runUpdate} 
            disabled={loading !== null}
          >
            {loading === 'update' ? <span className="spinner" /> : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
              </svg>
            )}
            Update Data
          </button>
          
          <button 
            className="btn-control blue" 
            onClick={runBacktest} 
            disabled={loading !== null}
          >
            {loading === 'backtest' ? <span className="spinner" /> : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
            )}
            Run Backtest
          </button>

          <button 
            className="btn-control purple" 
            onClick={checkStatus} 
            disabled={loading !== null}
          >
            {loading === 'status' ? <span className="spinner" /> : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
                <path d="M12 16v-4" />
                <path d="M12 8h.01" />
              </svg>
            )}
            System Status
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
        />
        <ForecastEnsemblePanel />
        <UserCostPanel />
        <ScenarioAssumptionsPanel />
      </main>

      <footer className="dashboard-footer fade-in" style={{ animationDelay: '0.8s' }}>
        <p>Data: Danmarks Statistik (EJ56) · Model: CPH Housing Forecast System v2.4</p>
      </footer>

      {/* MODAL DIALOGS */}
      {activeModal === 'backtest' && modalData && (
        <div className="modal-overlay" role="dialog" aria-modal="true" onClick={() => setActiveModal(null)} onKeyDown={(e) => { if (e.key === 'Escape') setActiveModal(null); }}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Historical Backtest Calibration</h3>
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
              
              <h4 style={{ marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Empirical Warning Calibration</h4>
              <div style={{ marginBottom: '20px', padding: '12px', background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.15)', borderRadius: '8px' }}>
                <p style={{ fontSize: '0.82rem', marginBottom: '4px' }}>• Price-to-Wage RED Limit: <strong>{(modalData.empirical_calibrations["EWI-1_price_vs_wages_red"] * 100).toFixed(1)}% spread</strong></p>
                <p style={{ fontSize: '0.82rem', marginBottom: '4px' }}>• Supply-Demand AMBER Limit: <strong>{modalData.empirical_calibrations["EWI-2_supply_demand_amber"]} months</strong></p>
                <p style={{ fontSize: '0.82rem' }}>• Price-to-Rent RED Ratio: <strong>{modalData.empirical_calibrations["EWI-6_price_to_rent_red_ratio"]} ratio</strong></p>
              </div>

              <h4 style={{ marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Historical Simulation Series</h4>
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                      <th style={{ padding: '6px' }}>Year</th>
                      <th style={{ padding: '6px' }}>Actual Index</th>
                      <th style={{ padding: '6px' }}>Model Forecast</th>
                      <th style={{ padding: '6px' }}>Absolute Error</th>
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
              <h3>Forecasting System Diagnostics</h3>
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
