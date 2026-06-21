import { useState, useEffect } from 'react';
import { renderHtml, saveToWorkspace, compileWorkspace, buildWebsite, getBuildStatus, downloadBuild, buildFileUrl } from '../api';

// Per-page-type transformer field descriptions for context comparison labels
const TRANSFORMER_DOCS = {
  course: {
    hero_image_url: 'Hero image — right column of the hero section (480×420px)',
    hero_image_alt: 'Alt text for the hero image (accessibility / SEO)',
    certificate_image_url: 'Certificate image — shown in Placement & Certificate section (320×240px)',
    og_image_url: 'Open Graph image — shown when page is shared on LinkedIn, WhatsApp, etc. (1200×630px)',
    hero: 'Hero block — title, description, pills, badge, CTAs, stat_card',
    breadcrumbs: 'Page breadcrumb trail',
    stats: 'Stats strip — duration, mode, fee, accreditation',
    rail: 'Sidebar navigation anchors (only sections with data)',
    about: 'About section HTML',
    highlights: 'Highlight cards array',
    accreditations: 'Accreditation badges derived from naac_grade + ugc_status',
    specializations: 'Child specialization cards fetched from DB',
    fees: 'Fee plans table + EMI note',
    eligibility: 'Eligibility HTML',
    admission: 'Admission steps HTML + fee note',
    syllabus: 'Syllabus HTML',
    placement: 'Placement content HTML',
    jobs: 'Job profile rows (title + salary)',
    reviews: 'Enriched reviews (initial, name, role, quote)',
    faqs: 'FAQ accordion items',
    sticky_bar: 'Sticky CTA bar fee + EMI',
  },
  specialization: {
    hero_image_url: 'Hero image — right column of the hero section (480×420px)',
    hero_image_alt: 'Alt text for the hero image (accessibility / SEO)',
    og_image_url: 'Open Graph image — shown when page is shared on LinkedIn, WhatsApp, etc. (1200×630px)',
    hero: 'Hero block — spec name, badge=Most Popular, stat_card=fee',
    breadcrumbs: 'Breadcrumbs including parent course',
    stats: 'Stats strip',
    rail: 'Sidebar navigation anchors',
    about: 'About HTML',
    highlights: 'Highlight cards',
    eligibility: 'Eligibility HTML',
    fees: 'Fee plans',
    other_specs: 'Sibling specialization cards from DB',
    syllabus: 'Syllabus HTML',
    exam: 'Exam process HTML',
    admission: 'Admission steps',
    placement: 'Placement HTML',
    certificate: 'Certificate description HTML',
    jobs: 'Job profiles',
    reviews: 'Enriched reviews',
    faqs: 'FAQs',
    sticky_bar: 'Sticky bar fee + EMI',
  },
  university: {
    hero_image_url: 'Hero image — right column of the hero section (480×420px)',
    hero_image_alt: 'Alt text for the hero image (accessibility / SEO)',
    og_image_url: 'Open Graph image — shown when page is shared on LinkedIn, WhatsApp, etc. (1200×630px)',
    hero: 'Hero — university name + full name, badge, pills',
    breadcrumbs: 'Page breadcrumbs',
    stats: 'Stats strip — est year, NAAC, UGC, fee, programs',
    rail: 'Sidebar rail',
    about: 'About HTML',
    why_choose: 'Why Choose HTML',
    facts: 'Quick facts cards',
    accreditations: 'Accreditation list',
    programs: 'Programs table + courses from DB',
    admission: 'Admission steps',
    emi: 'EMI/fees HTML',
    exam: 'Exam process HTML',
    placement: 'Placement HTML',
    reviews: 'Enriched reviews',
    faqs: 'FAQs',
  },
  blog: {
    hero: 'Blog hero title + description',
    categories: 'Category filter chips',
    featured_post: 'Featured post (first with featured:true) + image',
    posts: 'Remaining posts array + images',
    featured_image_url: 'Featured article banner image (580×320px)',
  },
};

function ComparisonPanel({ session }) {
  const [activeTab, setActiveTab] = useState('raw');
  const docs = TRANSFORMER_DOCS[session.page_type] || {};

  const tabStyle = (t) => ({
    padding: '8px 18px',
    fontWeight: 700,
    fontSize: 13,
    border: 'none',
    borderBottom: activeTab === t ? '2px solid var(--amber)' : '2px solid transparent',
    background: 'none',
    color: activeTab === t ? 'var(--navy)' : '#8a95a5',
    cursor: 'pointer',
  });

  return (
    <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)', marginBottom: 20, overflow: 'hidden' }}>
      <div style={{ borderBottom: '1px solid var(--border)', display: 'flex', padding: '0 20px', gap: 4, background: '#fafbfc' }}>
        <button style={tabStyle('raw')} onClick={() => setActiveTab('raw')}>📄 Raw JSON (Input)</button>
        <button style={tabStyle('context')} onClick={() => setActiveTab('context')}>⚙️ Transformer Context (Output)</button>
        <button style={tabStyle('diff')} onClick={() => setActiveTab('diff')}>🔍 Field Map</button>
      </div>

      {activeTab === 'raw' && (
        <div style={{ padding: 20 }}>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
            Original ACF JSON fields from your input — exactly as pasted/edited in Step 2.
          </div>
          <div style={{ background: '#f8fafc', border: '1px solid var(--border)', borderRadius: 8, padding: 16, maxHeight: 400, overflow: 'auto' }}>
            <pre style={{ fontFamily: 'ui-monospace, monospace', fontSize: 12, color: '#1a2533', whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0 }}>
              {JSON.stringify(session.raw_acf_data || session.acf_data, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {activeTab === 'context' && (
        <div style={{ padding: 20 }}>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
            Transformer output — structured context injected into the Jinja2 HTML template.
          </div>
          <div style={{ background: '#f0f8f0', border: '1px solid #c3e6cb', borderRadius: 8, padding: 16, maxHeight: 400, overflow: 'auto' }}>
            <pre style={{ fontFamily: 'ui-monospace, monospace', fontSize: 12, color: '#1a2533', whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0 }}>
              {JSON.stringify(session.context, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {activeTab === 'diff' && (
        <div style={{ padding: 20 }}>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
            How each transformer output key is used — what it maps to in the template for{' '}
            <strong style={{ color: 'var(--navy)' }}>{session.page_type}</strong> pages.
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {Object.entries(session.context || {})
              .filter(([k]) => k !== 'ctx_json' && k !== 'site')
              .map(([key, val]) => {
                const present = val !== null && val !== undefined && val !== '' && !(Array.isArray(val) && val.length === 0);
                return (
                  <div key={key} style={{
                    display: 'grid',
                    gridTemplateColumns: '180px 1fr',
                    gap: 12,
                    padding: '10px 14px',
                    borderRadius: 8,
                    background: present ? '#f0f9f4' : '#fdf4f4',
                    border: `1px solid ${present ? '#b7e4c7' : '#f5c6cb'}`,
                    alignItems: 'start',
                  }}>
                    <div>
                      <code style={{ fontFamily: 'ui-monospace, monospace', fontSize: 12, fontWeight: 700, color: present ? '#1a6b3c' : '#842029' }}>
                        {key}
                      </code>
                      <div style={{ fontSize: 10, marginTop: 3, color: present ? '#2d6a4f' : '#842029', fontWeight: 600 }}>
                        {present ? '✓ HAS DATA' : '✗ EMPTY / NULL'}
                      </div>
                    </div>
                    <div>
                      {docs[key] && (
                        <div style={{ fontSize: 11.5, color: '#5a6677', marginBottom: 4, fontStyle: 'italic' }}>{docs[key]}</div>
                      )}
                      <div style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11, color: '#4a5568', background: 'rgba(0,0,0,0.04)', padding: '4px 8px', borderRadius: 4, maxHeight: 60, overflow: 'hidden' }}>
                        {typeof val === 'object'
                          ? JSON.stringify(val).slice(0, 120) + (JSON.stringify(val).length > 120 ? '…' : '')
                          : String(val).slice(0, 120)}
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}

function ImagePreviewPanel({ session }) {
  const images = session.images || {};
  const hasImages = Object.values(images).some(Boolean);
  if (!hasImages) return null;

  const getImageUrl = (url) => {
    if (!url) return '';
    if (url.startsWith('/assets/images/')) {
      return `http://localhost:8000${url}`;
    }
    return url;
  };

  return (
    <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 24, marginBottom: 20 }}>
      <div style={{ fontSize: 15, fontWeight: 800, color: 'var(--navy)', marginBottom: 4 }}>Uploaded Images</div>
      <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 14 }}>
        These images are embedded in the preview and downloaded file below.
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
        {Object.entries(images).filter(([, v]) => v).map(([key, url]) => (
          <div key={key} style={{ flex: '0 0 auto', maxWidth: 240 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#8a95a5', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>{key}</div>
            <div style={{ borderRadius: 10, overflow: 'hidden', border: '2px solid var(--amber)', background: '#f4f7fb', height: 130 }}>
              <img
                src={getImageUrl(url)}
                alt={key}
                style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
              />
            </div>
            <div style={{ fontSize: 11, color: '#8a95a5', marginTop: 4 }}>
              {url.startsWith('data:') ? '📎 Local file (base64)' : `🔗 ${url.slice(0, 40)}${url.length > 40 ? '…' : ''}`}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Screen3Preview({ session, updateSession, onBack }) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [previewWidth, setPreviewWidth] = useState('100%');

  const previewUrl = session.slug && session.page_type && session.university_slug
    ? `http://localhost:8000/preview-file?university_slug=${session.university_slug}&page_type=${session.page_type}&slug=${session.slug}`
    : null;


  // Workspace state
  const [workspaceSaving, setWorkspaceSaving] = useState(false);
  const [workspaceSaveResult, setWorkspaceSaveResult] = useState(null);
  const [compiling, setCompiling] = useState(false);
  const [compileResult, setCompileResult] = useState(null);
  const [workspaceError, setWorkspaceError] = useState('');

  // Website build state (Pass 4)
  const [building, setBuilding] = useState(false);
  const [buildResult, setBuildResult] = useState(null);
  const [buildError, setBuildError] = useState('');

  // On mount, check if a build already exists for this workspace so the
  // "Build Complete" panel can render without forcing a rebuild.
  useEffect(() => {
    let cancelled = false;
    if (!session.university_slug) return undefined;
    getBuildStatus(session.university_slug)
      .then((status) => {
        if (cancelled) return;
        if (status && status.exists) {
          setBuildResult({
            university_slug: status.university_slug,
            build_path: status.build_path,
            build_url: status.build_url,
            pages_compiled: status.pages_compiled,
            images_copied: status.images_copied,
            routes_generated: status.routes_count,
            routes: Object.entries(status.routes || {}).map(([route, type]) => ({ route, type })),
            built_at: status.built_at,
            restored: true,
          });
        }
      })
      .catch(() => { /* non-fatal: build panel just stays idle */ });
    return () => { cancelled = true; };
  }, [session.university_slug]);

  // Helper: always merge session metadata into acf_data so the backend uses the
  // correct transformer and never falls back to auto-detection.
  const buildAcf = () => ({
    ...(session.raw_acf_data || session.acf_data),
    page_type:       session.page_type,
    slug:            session.slug,
    university_slug: session.university_slug,
    parent_slug:     session.parent_slug,
  });



  const handleDownload = async () => {
    setDownloading(true);
    setError('');
    try {
      // re-render to get the downloadable blob (also re-saves to generated/)
      // Include metadata so the backend uses the correct template.
      const acf = buildAcf();
      const blob = await renderHtml({
        acf_data: { ...acf, ...(session.images || {}) },
        images: session.images || {},
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${session.slug}.html`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally {
      setDownloading(false);
    }
  };

  const handleSaveAndCompile = async () => {
    setWorkspaceSaving(true);
    setWorkspaceError('');
    setWorkspaceSaveResult(null);
    setCompileResult(null);
    try {
      const acf = buildAcf();
      const result = await saveToWorkspace(acf, session.images || {});
      if (result.status === 'saved') {
        setWorkspaceSaveResult(result);
        
        if (session.university_slug) {
          setCompiling(true);
          const compRes = await compileWorkspace(session.university_slug);
          setCompileResult(compRes);
        }
      } else {
        setWorkspaceError(result.error || 'Unknown error saving to workspace.');
      }
    } catch (e) {
      setWorkspaceError(e.response?.data?.error || e.message || String(e));
    } finally {
      setWorkspaceSaving(false);
      setCompiling(false);
    }
  };

  const handleBuildWebsite = async () => {
    setBuilding(true);
    setBuildError('');
    setBuildResult(null);
    try {
      const result = await buildWebsite(session.university_slug);
      if (result.errors && result.errors.length === 0 && result.pages_failed === 0) {
        setBuildResult(result);
      } else if (result.build_path) {
        // Build still produced output even if there were non-fatal warnings.
        setBuildResult(result);
      } else {
        setBuildError(result.error || 'Build failed with no output.');
      }
    } catch (e) {
      setBuildError(e.response?.data?.error || e.message || String(e));
    } finally {
      setBuilding(false);
    }
  };

  const card = { background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 28, marginBottom: 20 };
  const imageCount = Object.values(session.images || {}).filter(Boolean).length;
  const totalSlots = Object.keys(session.images || {}).length;

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 12.5, fontWeight: 700, letterSpacing: '.14em', color: 'var(--amber)', textTransform: 'uppercase' }}>Step 4</div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: 'var(--navy)', marginTop: 6 }}>Preview & Download</h1>
        <p style={{ color: 'var(--muted)', fontSize: 15, marginTop: 6 }}>
          Your page is generated and saved directly to the workspace below. Review the live iframe mockup or download the file.
        </p>
      </div>

      {/* ── BUTTON ROW (NOW AT THE TOP) ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={onBack} style={{ background: '#fff', color: 'var(--navy)', fontWeight: 700, fontSize: 14, padding: '12px 22px', border: '1.5px solid var(--border)', borderRadius: 9, cursor: 'pointer' }}>
            ← Back
          </button>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            style={{ background: showAdvanced ? '#e2e8f0' : '#fff', color: 'var(--navy)', fontWeight: 700, fontSize: 14, padding: '12px 22px', border: '1.5px solid var(--border)', borderRadius: 9, cursor: 'pointer', display: 'inline-flex', alignItems: 'center' }}
          >
            {showAdvanced ? '⚙️ Hide Advanced Info' : '⚙️ Show Advanced Info'}
          </button>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={() => {
              if (previewUrl) {
                window.open(previewUrl, '_blank');
              }
            }}
            style={{ background: 'var(--navy)', color: '#fff', fontWeight: 700, fontSize: 14, padding: '12px 22px', border: 'none', borderRadius: 9, cursor: 'pointer', display: 'inline-flex', alignItems: 'center' }}
          >
            Open Full Page ↗
          </button>
          <button
            onClick={handleDownload}
            disabled={downloading}
            style={{ background: downloading ? '#ccc' : 'var(--amber)', color: '#fff', fontWeight: 800, fontSize: 15, padding: '13px 28px', border: 'none', borderRadius: 9, cursor: 'pointer' }}
          >
            {downloading ? 'Preparing…' : `⬇ Download ${session.slug}.html`}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: '#fff5f5', border: '1px solid #fed7d7', borderRadius: 8, padding: '12px 16px', color: '#c53030', fontSize: 14, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* ── WORKSPACE STATUS SECTION ── */}
      <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 800, color: 'var(--navy)' }}>University Workspace Status</div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>
              {!workspaceSaveResult ? 'This page is in preview and has not been saved to your workspace on disk yet.' : 'This page is saved and compiled within your selected university workspace.'}
            </div>
          </div>
          <button
            onClick={handleSaveAndCompile}
            disabled={workspaceSaving || compiling}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              background: !workspaceSaveResult ? 'var(--amber)' : '#f8fafc',
              color: !workspaceSaveResult ? '#fff' : 'var(--navy)',
              border: !workspaceSaveResult ? '1px solid var(--amber)' : '1px solid var(--border)',
              padding: '8px 16px',
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            {!workspaceSaveResult ? '💾 Add to Workspace & Compile' : '🔄 Sync & Compile Workspace'}
          </button>
        </div>

        {/* Status indicator banner */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: 16,
          borderRadius: 8,
          background: workspaceSaving || compiling ? '#f8fafc' : workspaceError ? '#fef2f2' : (!workspaceSaveResult ? '#fffbeb' : '#f0f9f4'),
          border: `1px solid ${workspaceSaving || compiling ? 'var(--border)' : workspaceError ? '#fca5a5' : (!workspaceSaveResult ? '#fde68a' : '#b7e4c7')}`,
        }}>
          <div style={{ fontSize: 24 }}>
            {workspaceSaving ? '💾' : compiling ? '⚡' : workspaceError ? '⚠️' : (!workspaceSaveResult ? '📝' : '✓')}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: workspaceError ? '#c53030' : 'var(--navy)' }}>
              {workspaceSaving ? 'Saving to workspace folder...' : compiling ? 'Compiling and updating workspace site context...' : workspaceError ? 'Workspace Error' : (!workspaceSaveResult ? 'Page not yet added to workspace folder' : 'All changes saved & compiled successfully')}
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>
              {workspaceSaving ? 'Writing source.json and template HTML...' : compiling ? 'Running the two-pass builder compiler...' : workspaceError ? workspaceError : (!workspaceSaveResult ? 'Review the preview mockup below, then click "Add to Workspace & Compile" to save this page and build all relationships.' : `Saved under workspaces/${session.university_slug || 'unknown'}`)}
            </div>
          </div>
        </div>

        {workspaceSaveResult && (
          <div style={{ marginTop: 16, background: '#f8fafc', border: '1px solid var(--border)', borderRadius: 8, padding: '14px 18px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { label: 'University Workspace', value: workspaceSaveResult.university_slug },
                { label: 'Page Directory', value: workspaceSaveResult.page_type },
                { label: 'Slug ID', value: workspaceSaveResult.slug },
                { label: 'Parent Link Slug', value: workspaceSaveResult.parent_slug || '—' },
              ].map(item => (
                <div key={item.label} style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 6, padding: '8px 12px' }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: '#8a95a5', textTransform: 'uppercase', letterSpacing: '.05em' }}>{item.label}</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)', marginTop: 2 }}>{item.value}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 12, fontSize: 12, color: '#8a95a5', fontFamily: 'monospace', wordBreak: 'break-all' }}>
              📁 Path on server disk: {workspaceSaveResult.workspace_dir}
            </div>
          </div>
        )}

        {compileResult && (
          <div style={{ marginTop: 12, background: compileResult.pages_failed > 0 ? '#fffbeb' : '#f0f9f4', border: `1px solid ${compileResult.pages_failed > 0 ? '#fde68a' : '#b7e4c7'}`, borderRadius: 8, padding: '14px 18px' }}>
            <div style={{ fontWeight: 700, color: compileResult.pages_failed > 0 ? '#92400e' : '#1a6b3c', fontSize: 13, marginBottom: 8 }}>
              {compileResult.pages_failed > 0 ? '⚠️ Compiled with errors' : '⚡ Workspace Site Compilation Summary'}
            </div>
            <div style={{ display: 'flex', gap: 16 }}>
              <div style={{ background: '#fff', border: '1px solid #b7e4c7', borderRadius: 6, padding: '8px 14px', textAlign: 'center' }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: '#1a6b3c' }}>{compileResult.pages_compiled}</div>
                <div style={{ fontSize: 11, color: '#2d6a4f', marginTop: 2 }}>Pages compiled</div>
              </div>
              <div style={{ background: '#fff', border: `1px solid ${compileResult.pages_failed > 0 ? '#fca5a5' : '#b7e4c7'}`, borderRadius: 6, padding: '8px 14px', textAlign: 'center' }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: compileResult.pages_failed > 0 ? '#c53030' : '#1a6b3c' }}>{compileResult.pages_failed}</div>
                <div style={{ fontSize: 11, color: compileResult.pages_failed > 0 ? '#c53030' : '#2d6a4f', marginTop: 2 }}>Errors</div>
              </div>
            </div>
            {compileResult.errors && compileResult.errors.length > 0 && (
              <div style={{ marginTop: 10 }}>
                {compileResult.errors.map((e, i) => (
                  <div key={i} style={{ fontSize: 12, color: '#c53030', fontFamily: 'monospace', marginTop: 4 }}>
                    [{e.page_type}] {e.slug}: {e.error}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── WEBSITE BUILD (Pass 4 — deployable export) ── */}
      <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 800, color: 'var(--navy)' }}>Website Build</div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>
              {!buildResult
                ? 'Export the entire workspace into a deployable static website package.'
                : buildResult.restored
                  ? 'A previous build exists on disk. Rebuild to refresh, or download / preview it below.'
                  : 'Build complete — your deployable website is ready.'}
            </div>
          </div>
          <button
            onClick={handleBuildWebsite}
            disabled={building || !session.university_slug}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: building ? '#ccc' : 'var(--amber)',
              color: '#fff', border: 'none',
              padding: '8px 16px', borderRadius: 6,
              fontSize: 13, fontWeight: 700, cursor: building ? 'not-allowed' : 'pointer',
            }}
          >
            {building ? '⏳ Building Website…' : buildResult ? '🔄 Rebuild Website' : '🚀 Build Website'}
          </button>
        </div>

        {/* Status / progress banner */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12, padding: 16, borderRadius: 8,
          background: building ? '#f8fafc' : buildError ? '#fef2f2' : (!buildResult ? '#fff7ed' : '#f0f9f4'),
          border: `1px solid ${building ? 'var(--border)' : buildError ? '#fca5a5' : (!buildResult ? '#fed7aa' : '#b7e4c7')}`,
        }}>
          <div style={{ fontSize: 24 }}>
            {building ? '🏗️' : buildError ? '⚠️' : (!buildResult ? '📦' : '✓')}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: buildError ? '#c53030' : 'var(--navy)' }}>
              {building
                ? 'Building website package...'
                : buildError
                  ? 'Build Error'
                  : (!buildResult
                      ? 'No build yet'
                      : buildResult.restored
                        ? 'Existing build found on disk'
                        : 'Build Complete')}
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>
              {building
                ? 'Compiling pages, rewriting routes, copying assets, generating sitemap...'
                : buildError
                  ? buildError
                  : (!buildResult
                      ? 'Click "Build Website" to export all pages into a single deployable folder.'
                      : `Deployable site at workspaces/${session.university_slug}/build/`)}
            </div>
          </div>
        </div>

        {buildError && (
          <div style={{ marginTop: 12, fontSize: 12, color: '#c53030', fontFamily: 'monospace' }}>
            {buildError}
          </div>
        )}

        {buildResult && (
          <>
            {/* Build stats */}
            <div style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {[
                { label: 'Pages', value: buildResult.pages_compiled ?? 0 },
                { label: 'Images', value: buildResult.images_copied ?? 0 },
                { label: 'Downloads', value: buildResult.downloads_copied ?? 0 },
                { label: 'Routes', value: buildResult.routes_generated ?? 0 },
              ].map((s) => (
                <div key={s.label} style={{ background: '#fff', border: '1px solid #b7e4c7', borderRadius: 6, padding: '8px 14px', textAlign: 'center', minWidth: 84 }}>
                  <div style={{ fontSize: 20, fontWeight: 800, color: '#1a6b3c' }}>{s.value}</div>
                  <div style={{ fontSize: 11, color: '#2d6a4f', marginTop: 2 }}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Action buttons */}
            <div style={{ marginTop: 16, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button
                onClick={() => window.open(buildFileUrl(session.university_slug, 'index.html'), '_blank')}
                style={{ background: 'var(--navy)', color: '#fff', fontWeight: 700, fontSize: 13, padding: '10px 18px', border: 'none', borderRadius: 7, cursor: 'pointer' }}
              >
                📂 Preview Built Site ↗
              </button>
              <button
                onClick={() => downloadBuild(session.university_slug)}
                style={{ background: '#fff', color: 'var(--navy)', fontWeight: 700, fontSize: 13, padding: '10px 18px', border: '1.5px solid var(--border)', borderRadius: 7, cursor: 'pointer' }}
              >
                ⬇ Download Website (ZIP)
              </button>
            </div>

            {/* Build location */}
            <div style={{ marginTop: 14, fontSize: 12, color: '#8a95a5', fontFamily: 'monospace', wordBreak: 'break-all' }}>
              📁 Build folder: {buildResult.build_path}
            </div>

            {/* Non-fatal build warnings (e.g. dangling parent_slug, missing image) */}
            {buildResult.errors && buildResult.errors.length > 0 && (
              <div style={{ marginTop: 12, background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 8, padding: '12px 14px' }}>
                <div style={{ fontWeight: 700, color: '#92400e', fontSize: 12.5, marginBottom: 6 }}>
                  ⚠️ {buildResult.errors.length} warning(s) — build completed but these should be fixed
                </div>
                {buildResult.errors.slice(0, 8).map((e, i) => (
                  <div key={i} style={{ fontSize: 11.5, color: '#92400e', fontFamily: 'monospace', marginTop: 3 }}>
                    [{e.page_type}]{e.slug ? ` ${e.slug}:` : ''} {e.error}
                  </div>
                ))}
                {buildResult.errors.length > 8 && (
                  <div style={{ fontSize: 11, color: '#92400e', marginTop: 4 }}>…and {buildResult.errors.length - 8} more</div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* ── PAGE SUMMARY (CONDITIONAL) ── */}
      {showAdvanced && (
        <div style={card}>
          <div style={{ fontSize: 15, fontWeight: 800, color: 'var(--navy)', marginBottom: 14 }}>Page Summary</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
            {[
              { label: 'Slug', value: session.slug },
              { label: 'Page Type', value: session.page_type },
              { label: 'University', value: session.university_slug || '—' },
              { label: 'Fields Extracted', value: Object.keys(session.raw_acf_data || session.acf_data).length + ' fields' },
              { label: 'Images Embedded', value: imageCount > 0 ? `${imageCount} of ${totalSlots}` : 'none' },
              { label: 'Parent Slug', value: session.parent_slug || '—' },
            ].map(item => (
              <div key={item.label} style={{ background: '#f4f7fb', border: '1px solid var(--border)', borderRadius: 10, padding: 14 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#8a95a5', textTransform: 'uppercase', letterSpacing: '.05em' }}>{item.label}</div>
                <div style={{ fontSize: 14.5, fontWeight: 700, color: 'var(--navy)', marginTop: 4 }}>{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── UPLOADED IMAGES (CONDITIONAL) ── */}
      {showAdvanced && <ImagePreviewPanel session={session} />}

      {/* ── RAW vs CONTEXT COMPARISON (CONDITIONAL) ── */}
      {showAdvanced && <ComparisonPanel session={session} />}

      {/* ── LIVE IFRAME PREVIEW WITH DEVICE CONTROLS ── */}
      <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)', marginBottom: 20, overflow: 'hidden', boxShadow: 'var(--shadow)' }}>
        {/* Browser Mockup Header */}
        <div style={{ borderBottom: '1px solid var(--border)', background: '#fafbfc', padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ display: 'flex', gap: 6 }}>
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff5f57' }} />
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#febc2e' }} />
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#28c840' }} />
            </div>
            <div style={{ background: '#f1f5f9', borderRadius: 6, padding: '4px 16px', fontSize: 12, color: '#475569', fontFamily: 'var(--font-code)', border: '1px solid var(--border)', width: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {session.slug || 'untitled'}.html
            </div>
          </div>

          {/* Device Toggles */}
          <div style={{ display: 'flex', background: '#f1f5f9', padding: 3, borderRadius: 8, border: '1px solid var(--border)' }}>
            {[
              { id: '100%', label: '🖥️ Desktop', width: '100%' },
              { id: '768px', label: '📁 Tablet', width: '768px' },
              { id: '375px', label: '📱 Mobile', width: '375px' },
            ].map((device) => {
              const active = previewWidth === device.width;
              return (
                <button
                  key={device.id}
                  onClick={() => setPreviewWidth(device.width)}
                  style={{
                    padding: '6px 12px',
                    fontSize: 12,
                    fontWeight: 600,
                    fontFamily: 'var(--font-ui)',
                    background: active ? '#fff' : 'transparent',
                    color: active ? 'var(--color-navy)' : 'var(--color-text-secondary)',
                    border: 'none',
                    borderRadius: 6,
                    cursor: 'pointer',
                    boxShadow: active ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {device.label}
                </button>
              );
            })}
          </div>

          <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 500, fontFamily: 'var(--font-ui)' }}>
            {imageCount > 0 ? `${imageCount} image${imageCount > 1 ? 's' : ''} embedded` : 'no images'}
          </div>
        </div>

        {/* Workspace Canvas (Contrasting Slate Gray) */}
        <div style={{ 
          background: '#0f172a', 
          padding: '32px 24px', 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          overflow: 'auto',
          minHeight: 560
        }}>
          {previewUrl ? (
            <div style={{
              width: previewWidth,
              maxWidth: '100%',
              background: '#fff',
              borderRadius: 8,
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
              border: '1px solid #334155',
              transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              overflow: 'hidden'
            }}>
              <iframe
                src={previewUrl}
                title="Page Preview"
                style={{ width: '100%', height: 600, border: 'none', display: 'block' }}
                sandbox="allow-scripts allow-same-origin"
              />
            </div>
          ) : (
            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 14, fontFamily: 'var(--font-ui)' }}>
              No preview available — go back and click Generate Preview.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
