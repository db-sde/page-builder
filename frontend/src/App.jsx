import { useState } from 'react';
import './styles.css';
import Screen0Workspace from './components/Screen0Workspace';
import Screen1Upload from './components/Screen1Upload';
import Screen2Review from './components/Screen2Review';
import Screen3Preview from './components/Screen3Preview';

export default function App() {
  const [step, setStep] = useState(1);
  const [session, setSession] = useState({
    workspace: null, // { slug: '', name: '', is_new: false }
    slug: '',
    page_type: '',
    university_slug: '',
    parent_slug: '',
    acf_data: {},
    raw_acf_data: {},
    images: {},
    context: null,
    htmlContent: null,
    htmlBlob: null,
    validation_warnings: [],
    table_warnings: [],
  });

  const updateSession = (patch) => setSession(s => ({ ...s, ...patch }));

  return (
    <div className="app-layout">
      {/* Sidebar step navigator */}
      <aside className="sidebar" id="sidebar" role="navigation" aria-label="Main navigation">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon" aria-hidden="true" style={{ background: 'var(--color-orange)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#fff', fontWeight: 800, fontSize: 18 }}>D</span>
          </div>
          <div className="sidebar-brand-text">
            <span className="sidebar-brand-name">Content Studio</span>
            <span className="sidebar-brand-sub">DegreeBaba</span>
          </div>
        </div>

        <div className="sidebar-section-label">Publishing workflow</div>
        <nav className="sidebar-nav">
          <button 
            onClick={() => step > 1 && setStep(1)}
            className={`sidebar-nav-item ${step === 1 ? 'active' : ''}`}
            style={{ cursor: step > 1 ? 'pointer' : 'default', border: 'none', background: 'none' }}
          >
            <span className="sidebar-nav-icon" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>1</span>
            <span>University</span>
          </button>

          <button 
            onClick={() => step > 2 && setStep(2)}
            className={`sidebar-nav-item ${step === 2 ? 'active' : ''}`}
            style={{ cursor: step > 2 ? 'pointer' : 'default', border: 'none', background: 'none' }}
            disabled={step < 2}
          >
            <span className="sidebar-nav-icon" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>2</span>
            <span>Import Content</span>
          </button>

          <button 
            onClick={() => step > 3 && setStep(3)}
            className={`sidebar-nav-item ${step === 3 ? 'active' : ''}`}
            style={{ cursor: step > 3 ? 'pointer' : 'default', border: 'none', background: 'none' }}
            disabled={step < 3}
          >
            <span className="sidebar-nav-icon" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>3</span>
            <span>Edit Page</span>
          </button>

          <button 
            className={`sidebar-nav-item ${step === 4 ? 'active' : ''}`}
            style={{ cursor: 'default', border: 'none', background: 'none' }}
            disabled={step < 4}
          >
            <span className="sidebar-nav-icon" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>4</span>
            <span>Preview & Publish</span>
          </button>
        </nav>

        {session.workspace && (
          <div style={{ margin: 'auto 16px 16px', padding: 12, background: 'rgba(255, 255, 255, 0.05)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ fontSize: 10, color: 'rgba(255, 255, 255, 0.4)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '.05em' }}>
              Active Workspace
            </div>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-orange)', marginTop: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              📁 {session.workspace.name}
            </div>
          </div>
        )}

        <div className="sidebar-footer">
          <span className="sidebar-footer-logo">
            Powered by <span>DegreeBaba</span>
          </span>
        </div>
      </aside>

      {/* Main workspace */}
      <main className="main-content">
        <div style={{ maxWidth: (step === 4 || step === 1) ? 1280 : 960, margin: '0 auto', transition: 'max-width 0.3s ease-in-out' }}>
          {step === 1 && <Screen0Workspace session={session} updateSession={updateSession} onNext={() => setStep(2)} setStep={setStep} />}
          {step === 2 && <Screen1Upload session={session} updateSession={updateSession} onNext={() => setStep(3)} />}
          {step === 3 && <Screen2Review session={session} updateSession={updateSession} onNext={() => setStep(4)} onBack={() => setStep(2)} />}
          {step === 4 && <Screen3Preview session={session} onBack={() => setStep(3)} />}
        </div>
      </main>
    </div>
  );
}
