const STEPS = ['University Workspace', 'Upload & Configure', 'Review & Images', 'Preview & Download'];

export default function StepIndicator({ step }) {
  return (
    <div style={{ background: '#fff', borderBottom: '1px solid var(--border)' }}>
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 24px', display: 'flex' }}>
        {STEPS.map((label, i) => {
          const n = i + 1;
          const active = step === n;
          const done = step > n;
          return (
            <div key={n} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10, padding: '16px 0', borderBottom: active ? '3px solid var(--amber)' : '3px solid transparent' }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 800, fontSize: 13,
                background: done ? 'var(--amber)' : active ? 'var(--navy)' : 'var(--border)',
                color: done ? 'var(--navy)' : active ? '#fff' : 'var(--muted)'
              }}>
                {done ? '✓' : n}
              </div>
              <span style={{ fontSize: 13.5, fontWeight: active ? 700 : 500, color: active ? 'var(--navy)' : 'var(--muted)' }}>{label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
