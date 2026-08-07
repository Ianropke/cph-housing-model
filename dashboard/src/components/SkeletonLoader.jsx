import React from 'react';

export default function SkeletonLoader() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '20px 0' }}>
      <div className="skeleton-pulse" style={{ height: '80px', borderRadius: '16px', background: 'rgba(255,255,255,0.03)' }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        <div className="skeleton-pulse" style={{ height: '320px', borderRadius: '16px', background: 'rgba(255,255,255,0.03)' }} />
        <div className="skeleton-pulse" style={{ height: '320px', borderRadius: '16px', background: 'rgba(255,255,255,0.03)' }} />
      </div>
    </div>
  );
}
