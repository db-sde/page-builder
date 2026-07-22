import { useState, useEffect } from 'react';
import { saveToWorkspace, compileWorkspace, buildWebsite, getBuildStatus, downloadBuild, buildFileUrl } from '../api';

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

function apiErrorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  if (detail && typeof detail === 'object' && Array.isArray(detail.fields)) {
    return `${detail.message || 'Missing required fields'}: ${detail.fields.join(', ')}`;
  }
  return error.response?.data?.error || detail || error.message || fallback;
}

export default function Screen3Preview({ session, onBack }) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [previewWidth, setPreviewWidth] = useState('100%');
  const previewUrl = session.slug && session.page_type && session.university_slug
    ? `http://localhost:8000/preview-file?university_slug=${session.university_slug}&page_type=${session.page_type}&slug=${session.slug}`
    : null;


  // Workspace state
  const [workspaceSaving, setWorkspaceSaving] = useState(false);
  const [workspaceSaveResult, setWorkspaceSaveResult] = useState(null);
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

  const handleSaveAndCompile = async () => {
    setWorkspaceSaving(true);
    setWorkspaceError('');
    setWorkspaceSaveResult(null);
    try {
      const acf = buildAcf();
      const result = await saveToWorkspace(acf, session.images || {});
      if (result.status === 'saved') {
        setWorkspaceSaveResult(result);
        
        if (session.university_slug) {
          await compileWorkspace(session.university_slug);
        }
      } else {
        setWorkspaceError(result.error || 'Unknown error saving to workspace.');
      }
    } catch (e) {
      setWorkspaceError(apiErrorMessage(e, 'Failed to save to workspace.'));
    } finally {
      setWorkspaceSaving(false);
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
      setBuildError(apiErrorMessage(e, 'Website build failed.'));
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
        <h1 
          onDoubleClick={() => setShowAdvanced(!showAdvanced)} 
          style={{ fontSize: 26, fontWeight: 800, color: 'var(--navy)', marginTop: 6, cursor: 'default', userSelect: 'none' }}
        >
          Preview &amp; Publish
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: 15, marginTop: 6 }}>
          Review the live preview, save the page to your workspace, and build the website.
        </p>
      </div>

      {/* ── BUTTON ROW (NOW AT THE TOP) ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={onBack} style={{ background: '#fff', color: 'var(--navy)', fontWeight: 700, fontSize: 14, padding: '12px 22px', border: '1.5px solid var(--border)', borderRadius: 9, cursor: 'pointer' }}>
            ← Back
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
        </div>
      </div>

      {/* ── SAVE PAGE SECTION ── */}
      <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 24, marginBottom: 20 }}>
        <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--navy)', marginBottom: 8 }}>Save Page</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ flex: 1, minWidth: 280 }}>
            {workspaceSaving ? (
              <p style={{ color: 'var(--muted)', fontSize: 14, margin: 0 }}>Saving your changes...</p>
            ) : !workspaceSaveResult ? (
              <p style={{ color: 'var(--muted)', fontSize: 14, margin: 0 }}>This page has not yet been saved to your workspace.</p>
            ) : (
              <p style={{ color: 'var(--color-success)', fontSize: 14, fontWeight: 600, margin: 0 }}>✓ Saved To Workspace (Last saved successfully)</p>
            )}
          </div>
          <button
            onClick={handleSaveAndCompile}
            disabled={workspaceSaving}
            style={{
              background: workspaceSaving ? '#ccc' : 'var(--amber)',
              color: '#fff',
              border: 'none',
              padding: '10px 22px',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 700,
              cursor: workspaceSaving ? 'not-allowed' : 'pointer'
            }}
          >
            {workspaceSaving ? 'Saving…' : !workspaceSaveResult ? 'Save To Workspace' : 'Save Changes'}
          </button>
        </div>
        {workspaceError && (
          <div style={{ background: '#fff5f5', border: '1px solid #fed7d7', borderRadius: 8, padding: '12px 16px', color: '#c53030', fontSize: 13, marginTop: 12 }}>
            {workspaceError}
          </div>
        )}
      </div>

      {/* ── WEBSITE BUILD (Optional) ── */}
      <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ flex: 1, minWidth: 280 }}>
            <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--navy)', marginBottom: 4 }}>Website Export</div>
            {building ? (
              <p style={{ color: 'var(--muted)', fontSize: 14, margin: 0 }}>Building your website package...</p>
            ) : !buildResult ? (
              <p style={{ color: 'var(--muted)', fontSize: 14, margin: 0 }}>Build the entire website package using the latest workspace data.</p>
            ) : (
              <p style={{ color: 'var(--color-success)', fontSize: 14, fontWeight: 600, margin: 0 }}>✓ Website Built</p>
            )}
          </div>
          <button
            onClick={handleBuildWebsite}
            disabled={building || !session.university_slug}
            style={{
              background: building ? '#ccc' : 'var(--amber)',
              color: '#fff',
              border: 'none',
              padding: '10px 22px',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 700,
              cursor: building ? 'not-allowed' : 'pointer'
            }}
          >
            {building ? 'Building…' : buildResult ? 'Rebuild Website' : 'Build Website'}
          </button>
        </div>

        {buildError && (
          <div style={{ background: '#fff5f5', border: '1px solid #fed7d7', borderRadius: 8, padding: '12px 16px', color: '#c53030', fontSize: 13, marginTop: 12 }}>
            {buildError}
          </div>
        )}

        {buildResult && (
          <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Website Package</div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button
                onClick={() => window.open(buildFileUrl(session.university_slug, 'index.html'), '_blank')}
                style={{ background: 'var(--primary)', color: '#fff', fontWeight: 700, fontSize: 14, padding: '10px 20px', border: 'none', borderRadius: 8, cursor: 'pointer' }}
              >
                Preview Website ↗
              </button>
              <button
                onClick={() => downloadBuild(session.university_slug)}
                style={{ background: '#fff', color: 'var(--primary)', fontWeight: 700, fontSize: 14, padding: '10px 20px', border: '1.5px solid var(--primary)', borderRadius: 8, cursor: 'pointer' }}
              >
                Download ZIP
              </button>
            </div>
          </div>
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
