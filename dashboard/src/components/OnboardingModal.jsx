export default function OnboardingModal({ isOpen, onClose }) {
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
      <div className="modal-card" style={{ maxWidth: '640px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🏢</span> Velkommen til Københavns Boligmarkedsmodel
          </h3>
          <button className="btn-close" aria-label="Close" onClick={onClose}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', lineHeight: '1.5' }}>
          <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.95rem' }}>
            Dette er et uafhængigt, kvantitativt <strong>Forecast & Early Warning System</strong> for ejerlejlighedsmarkedet i København. Dashboardet opdateres hver nat via automatiserede pipelines mod Danmarks Statistik (EJ56) og Boliga.
          </p>

          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <h4 style={{ color: '#00d4aa', margin: '0 0 8px 0', fontSize: '0.9rem' }}>🎯 Tre primære funktioner på siden:</h4>
            <ul style={{ margin: 0, paddingLeft: '20px', color: 'rgba(255,255,255,0.8)', fontSize: '0.88rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <li>
                <strong>12-måneders Forecast Ensemble:</strong> Kombinerer makroøkonomiske faktorer (renter, lønvækst, nybyggeri) i tre scenarier (<em>Baseline, Min Risk, Max Risk</em>).
              </li>
              <li>
                <strong>Tidlig Varsling (Early Warning 1–9):</strong> Overvåger udbudsmåneder, liggetid, prisafslag og gældsbelastning (DSR) for at opdage et vendepunkt før det ses i handelspriserne.
              </li>
              <li>
                <strong>🧪 Interaktiv Risikosimulator (Sandbox):</strong> Giver dig mulighed for selv at trække i markedsparametrene (liggetid, renter, udbud) og se effekten live på risikoscoren.
              </li>
            </ul>
          </div>

          <div style={{ background: 'rgba(255, 193, 7, 0.08)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255, 193, 7, 0.2)', fontSize: '0.82rem', color: '#ffc107' }}>
            ℹ️ <strong>Bemærk:</strong> Systemet måler operationel retningspræcision (56,2% historisk hit-rate) og tjener som et analytisk beslutningsværktøj. Det udgør ikke finansiel investeringsrådgivning.
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button
              onClick={onClose}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #00d4aa 0%, #00a887 100%)',
                color: '#060a14',
                fontWeight: 700,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.9rem',
              }}
            >
              Udforsk Dashboardet →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
