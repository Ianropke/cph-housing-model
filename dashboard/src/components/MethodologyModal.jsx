import React from 'react';

export default function MethodologyModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose();
      }}
    >
      <div className="modal-card" style={{ maxWidth: '720px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🔬</span> Model-Metodik & Historisk Backtest (v3.2 Spec)
          </h3>
          <button className="btn-close" aria-label="Close" onClick={onClose}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', lineHeight: '1.5', fontSize: '0.88rem' }}>
          <div>
            <h4 style={{ color: '#00d4aa', margin: '0 0 6px 0', fontSize: '0.95rem' }}>1. Arkitektur & Modelkomponenter</h4>
            <p style={{ color: 'rgba(255,255,255,0.8)' }}>
              Prognosesystemet benytter en 3-lags hybridmodel sammensat af stokastisk fundamental-modellering (Fundamental User Cost), 
              <strong>Bayesian Model Averaging (BMA)</strong> for makroøkonomiske vægte, og en <strong>Random Forest Classifier</strong> trænet på 
              Walk-Forward validation (<code>TimeSeriesSplit</code>) over perioden 2000–2024.
            </p>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <h4 style={{ color: '#3b82f6', margin: '0 0 8px 0', fontSize: '0.95rem' }}>2. Historiske Backtest-Resultater (2007–2024, 17 Årlige Punkter)</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px', textAlign: 'center' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Retningspræcision</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#00d4aa' }}>56,2%</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>MAPE (Procentfejl)</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#3b82f6' }}>7,58%</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>MAE (Middelfejl)</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#a78bfa' }}>6,79 pts</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Mean Bias Error</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ffc107' }}>+2,92 pts</div>
              </div>
            </div>
          </div>

          <div>
            <h4 style={{ color: '#a78bfa', margin: '0 0 6px 0', fontSize: '0.95rem' }}>3. Data Lineage & Pipeline Overvågning</h4>
            <p style={{ color: 'rgba(255,255,255,0.8)' }}>
              Realtidsdata hentes hver nat kl. 03:00 UTC fra <strong>Danmarks Statistik (EJ56, HUS1)</strong>, <strong>Boliga Web API</strong> (TLS impersonation) og <strong>Realkredit Danmark / Finans Danmark (RKR)</strong>. Data valideres via Pydantic skemaer før beregning af sammensatte Z-scores og publikation til Vercel Edge CDN.
            </p>
          </div>

          <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '12px', fontSize: '0.78rem', color: 'rgba(255,255,255,0.4)', fontStyle: 'italic' }}>
            ⚖️ <strong>Ansvarsfraskrivelse:</strong> Prospekter og kvantitative indikatorer er genereret til analytiske og videnskabelige formål. De udgør ikke juridisk eller finansiel investeringsrådgivning.
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
            <button
              onClick={onClose}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                background: 'rgba(255,255,255,0.1)',
                color: '#ffffff',
                border: '1px solid rgba(255,255,255,0.2)',
                cursor: 'pointer',
              }}
            >
              Luk Vindue
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
