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
      <div className="modal-card" style={{ maxWidth: '760px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🔬</span> Model-Metodik & Statistisk Event-Validering (v3.4 Spec)
          </h3>
          <button className="btn-close" aria-label="Close" onClick={onClose}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', lineHeight: '1.5', fontSize: '0.88rem' }}>
          <div>
            <h4 style={{ color: '#00d4aa', margin: '0 0 6px 0', fontSize: '0.95rem' }}>1. Eksplicit Todelt Modelarkitektur (Model A vs. Model B)</h4>
            <p style={{ color: 'rgba(255,255,255,0.8)' }}>
              Prognosesystemet anvender en todelt todelt modelarkitektur for at adskille uafhængige ekspert-heuristikker fra statistisk kalibrerede maskinlærings-sandsynligheder:
            </p>
            <ul style={{ margin: '6px 0 0 16px', color: 'rgba(255,255,255,0.8)' }}>
              <li><strong>Model A — Ekspert EWI Risikoscore (0–27 pts):</strong> Heuristisk vægtet composite score baseret på 9 Early Warning indikatorer og 4 risikoregimer (NORMAL, FORHØJET, HØJ, KRITISK).</li>
              <li><strong>Model B — Statistisk ML Event Model (Random Forest & Isotonic Calibration):</strong> Estimerer den konkrete statistiske sandsynlighed for et reelt prisfald på <strong>&ge;10% over de næste 12 måneder</strong> (Crash_12m).</li>
            </ul>
          </div>

          {/* Event Prediction Metric Cards */}
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <h4 style={{ color: '#e040fb', margin: '0 0 8px 0', fontSize: '0.95rem' }}>2. Event Prediction & Crash-Detektering (2000–2024, 76 Kvartaler)</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px', textAlign: 'center' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Crash Recall (Sensitivity)</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#00d4aa' }}>77,8%</div>
                <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.4)' }}>Opdagede 7 af 9 crash-kvartaler</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Advarsels Lead Time</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#3b82f6' }}>7,5 mdr</div>
                <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.4)' }}>Gennemsnitligt varsel før fald</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Brier Score (Kalibrering)</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#a78bfa' }}>0,1558</div>
                <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.4)' }}>Lav sandsynlighedsfejl (0=perfekt)</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Directional Accuracy</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ffc107' }}>56,2%</div>
                <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.4)' }}>Retningspræcision 1-step ahead</div>
              </div>
            </div>
          </div>

          <div>
            <h4 style={{ color: '#a78bfa', margin: '0 0 6px 0', fontSize: '0.95rem' }}>3. Data Lineage & Gennemsigtighed</h4>
            <p style={{ color: 'rgba(255,255,255,0.8)' }}>
              Data pipelines kører automatisk via GitHub Actions hver nat kl. 02:00 CET. Pipelinen skelner eksplicit mellem observationstidspunkt (f.eks. Q4 2025 fra Danmarks Statistik) og indhentelsestidspunkt.
            </p>
          </div>

          <div style={{ padding: '10px', background: 'rgba(255, 51, 102, 0.1)', borderRadius: '8px', border: '1px solid rgba(255, 51, 102, 0.2)', fontSize: '0.8rem', color: 'rgba(255,255,255,0.7)' }}>
            <strong>⚖️ Juridisk Ansvarsfraskrivelse:</strong> Dette dashboard er et uafhængigt kvantitativt forskningsværktøj til akademisk og analytisk brug. Modellerne udgør ikke finansiel rådgivning eller investeringsanbefaling.
          </div>
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
          <button className="btn-secondary" onClick={onClose}>
            Luk Metodenotat
          </button>
        </div>
      </div>
    </div>
  );
}
