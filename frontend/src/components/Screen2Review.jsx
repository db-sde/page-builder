import { useState } from 'react';
import { ingestAcf, previewHtml } from '../api';
import FieldHealthPanel from './FieldHealthPanel';
import AddFieldModal from './AddFieldModal';
import { FIELD_SCHEMA, isPlaceholder } from '../fieldSchema';

// Image slots required per page type
const IMAGE_SLOTS = {
  university: [
    { key: 'hero_image_url', label: 'Hero Image', hint: 'Homepage Hero / Campus Banner', dims: '480 × 420px' },
  ],
  course: [
    { key: 'hero_image_url', label: 'Hero Image', hint: 'Right column of hero section — the main visual', dims: '480 × 420px' },
    { key: 'certificate_image_url', label: 'Degree Certificate Image', hint: 'Sample degree certificate visual shown in Placement section', dims: '320 × 240px' },
  ],
  specialization: [
    { key: 'hero_image_url', label: 'Hero Image', hint: 'Right column of hero section — the main visual', dims: '480 × 420px' },
  ],
  blog: [
    { key: 'hero_image_url', label: 'Article Hero Image', hint: 'Main article header banner image displayed on the right of the title', dims: '460 × 340px' },
  ],
};

// ── helpers ──────────────────────────────────────────────────────────────────

/** Convert the fields state (all strings) to a proper acf_data dict. */
function fieldsToAcf(fields) {
  const out = {};
  for (const [k, v] of Object.entries(fields)) {
    // Attempt to parse anything that looks like JSON
    if (typeof v === 'string' && (v.startsWith('[') || v.startsWith('{'))) {
      try { out[k] = JSON.parse(v); continue; } catch {}
    }
    out[k] = v;
  }
  return out;
}

/** Initialise the editable fields state from session.acf_data, excluding metadata keys and structured (object/array) fields. */
function initFields(acf_data, page_type) {
  const excludedKeys = [
    'slug', 'page_type', 'university_slug', 'parent_slug',
    'hero_image_url', 'certificate_image_url', 'og_image_url', 'featured_image_url'
  ];
  const out = {};
  const schema = FIELD_SCHEMA[page_type] || [];
  const schemaKeys = schema.map(f => f.key);

  // 1. Pre-populate all schema fields, converting placeholders to ''
  for (const field of schema) {
    if (excludedKeys.includes(field.key)) continue;
    const v = acf_data[field.key];
    out[field.key] = isPlaceholder(v) ? '' : String(v);
  }

  // 2. Add other fields present in acf_data not in schema
  for (const [k, v] of Object.entries(acf_data)) {
    if (excludedKeys.includes(k)) continue;
    if (schemaKeys.includes(k)) continue;
    if (typeof v === 'object' && v !== null) continue; // exclude structured fields
    out[k] = isPlaceholder(v) ? '' : String(v);
  }

  return out;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function Screen2Review({ session, updateSession, onNext, onBack }) {
  const [fields, setFields]       = useState(() => initFields(session.acf_data, session.page_type));
  const [imageUrls, setImageUrls] = useState(() => {
    const initImages = { ...session.images };
    const neededKeys = (IMAGE_SLOTS[session.page_type] || []).map(slot => slot.key);
    for (const key of neededKeys) {
      if (session.acf_data && session.acf_data[key]) {
        initImages[key] = session.acf_data[key];
      }
    }
    return initImages;
  });
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');
  const [modalField, setModalField] = useState(null);   // field object or null

  const slots = IMAGE_SLOTS[session.page_type] || [];

  // ── Field modal handlers ──────────────────────────────────────────────────
  const handleAddField = (field) => {
    setModalField(field);
  };

  const JSON_ARRAY_FIELDS = [
    'highlights', 'fee_plans', 'job_profiles', 'faqs', 'reviews',
    'accreditations', 'facts', 'programs_table', 'posts', 'categories',
    'programs_list', 'other_specs'
  ];

  const handleSaveField = (key, rawValue) => {
    if (JSON_ARRAY_FIELDS.includes(key)) {
      // Parse and store directly in session.acf_data as a real array
      try {
        const parsed = JSON.parse(rawValue);
        updateSession({
          acf_data: { ...session.acf_data, [key]: parsed }
        });
      } catch {
        // If invalid JSON, store as string in fields and let backend handle it
        setFields(f => ({ ...f, [key]: rawValue }));
      }
    } else {
      // Simple fields go into the editable fields state as strings
      setFields(f => ({ ...f, [key]: rawValue }));
    }
    setModalField(null);
  };

  // ── Generate preview ──────────────────────────────────────────────────────
  const handleGenerate = async () => {
    setError('');
    
    // Check validation of required images before proceeding
    const requiredImages = {
      university: ['hero_image_url'],
      course: ['hero_image_url', 'certificate_image_url'],
      specialization: ['hero_image_url'],
      blog: ['hero_image_url'],
    };
    const needed = requiredImages[session.page_type] || [];
    const missingImgs = needed.filter(key => !imageUrls[key]);
    if (missingImgs.length > 0) {
      const labels = {
        hero_image_url: 'Hero Image',
        certificate_image_url: 'Degree Certificate Image',
      };
      const formatted = missingImgs.map(k => labels[k] || k).join(', ');
      setError(`Missing required image assets: ${formatted}`);
      return;
    }

    setLoading(true);
    try {
      const rebuilt = { ...session.acf_data, ...fieldsToAcf(fields) };

      // IMPORTANT: Always include metadata keys so the backend uses the correct
      // transformer. Without these, the backend auto-detects and can wrongly
      // classify a blog as a course (because blog content has no `posts` key).
      const metadata = {
        page_type:       session.page_type,
        slug:            session.slug,
        university_slug: session.university_slug,
        parent_slug:     session.parent_slug,
      };

      const merged = { ...rebuilt, ...metadata, ...imageUrls };
      const rawWithMeta = { ...rebuilt, ...metadata };

      updateSession({ acf_data: rebuilt, images: imageUrls, raw_acf_data: rawWithMeta });

      // Step A: transformer context
      const result = await ingestAcf({ acf_data: merged });
      if (result.status !== 'ok') {
        setError(result.error || 'Failed to process ACF data');
        setLoading(false);
        return;
      }

      // Step B: render HTML
      const htmlText = await previewHtml({ acf_data: merged, images: imageUrls });

      updateSession({
        context:         result.context,
        slug:            result.slug     || session.slug,
        page_type:       result.page_type || session.page_type,
        university_slug: result.university_slug || session.university_slug,
        parent_slug:     result.parent_slug,
        acf_data:        result.acf_data,
        images:          imageUrls,
        raw_acf_data:    rawWithMeta,
        htmlContent:     htmlText,
      });
      onNext();
    } catch (e) {
      setError(e.response?.data?.error || e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  // ── Styles ────────────────────────────────────────────────────────────────
  const card  = { background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 28, marginBottom: 20 };
  const label = { display: 'block', fontSize: 12.5, fontWeight: 700, color: '#33363f', marginBottom: 6 };

  // Split editable fields into simple vs complex
  const simpleFields  = Object.entries(fields);

  // Live acf_data for health panel (parsed)
  const liveAcf = { ...session.acf_data, ...fieldsToAcf(fields), ...imageUrls };

  const isListingPage = ['programs_listing', 'specializations_listing', 'blog_listing'].includes(session.page_type);

  const getImageUrl = (url) => {
    if (!url) return '';
    if (url.startsWith('/assets/images/')) {
      return `http://localhost:8000${url}`;
    }
    return url;
  };

  return (
    <div>
      <div className="topbar">
        <div className="topbar-left">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h1 className="topbar-title">Review &amp; Images</h1>
            {session.workspace && (
              <span className="badge badge--published" style={{ fontSize: 12, padding: '4px 10px', height: 'fit-content' }}>
                📁 Workspace: {session.workspace.name}
              </span>
            )}
          </div>
          <p className="topbar-subtitle">Check field health, edit extracted fields, and upload images before generating the page.</p>
        </div>
      </div>

      {/* ── Field Health Panel ── */}
      <FieldHealthPanel
        acf_data={liveAcf}
        page_type={session.page_type}
        onAddField={handleAddField}
      />

      {/* ── Simple text fields ── */}
      {simpleFields.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-body" style={{ padding: 28 }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>Page Fields</div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 20 }}>Edit any field before generating the page.</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {simpleFields.map(([key, val]) => {
                const schema = FIELD_SCHEMA[session.page_type] || [];
                const schemaField = schema.find(f => f.key === key);
                const isRequired = schemaField ? schemaField.required : false;
                const isFieldEmpty = val === '';
                
                return (
                  <div key={key}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: 'var(--color-text-primary)', margin: 0 }}>{key}</label>
                      {isRequired && <span style={{ fontSize: 11, color: '#c53030', fontWeight: 800 }}>Required</span>}
                    </div>
                    <input
                      className="input"
                      value={val}
                      onChange={e => setFields(f => ({ ...f, [key]: e.target.value }))}
                      style={{ 
                        width: '100%',
                        borderColor: isFieldEmpty && isRequired ? '#feb2b2' : isFieldEmpty ? '#fde68a' : undefined,
                        background: isFieldEmpty ? (isRequired ? '#fff8f8' : '#fffff4') : undefined,
                      }}
                    />
                    {isFieldEmpty && (
                      <div style={{ 
                        color: isRequired ? '#c53030' : '#b45309', 
                        fontSize: 11.5, 
                        marginTop: 4, 
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4
                      }}>
                        <span>⚠</span> {isRequired ? 'Missing from uploaded document' : 'Not detected from source file'}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── Image upload slots ── */}
      {isListingPage && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-body" style={{ padding: 28, textAlign: 'center' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: 4 }}>No Image Uploads Required</div>
            <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
              Listing pages are generated automatically from workspace data and do not require image assets.
            </div>
          </div>
        </div>
      )}

      {!isListingPage && slots.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-body" style={{ padding: 28 }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>Image Slots</div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 20 }}>
              Upload images for this <strong>{session.page_type}</strong> page. All slots are optional — placeholders show if left empty.
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {slots.map(slot => (
                <div
                  key={slot.key}
                  style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: 20, display: 'grid', gridTemplateColumns: '1fr 200px', gap: 20, alignItems: 'center' }}
                >
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--color-text-primary)', fontSize: 14.5 }}>{slot.label}</div>
                    <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>{slot.hint}</div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 3 }}>Recommended: {slot.dims}</div>

                    <div style={{ marginTop: 12 }}>
                      <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>Image URL</label>
                      <input
                        className="input"
                        placeholder="https://..."
                        value={imageUrls[slot.key] || ''}
                        onChange={e => setImageUrls(u => ({ ...u, [slot.key]: e.target.value }))}
                        style={{ width: '100%' }}
                      />
                    </div>

                    <div style={{ marginTop: 12 }}>
                      <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>Or Upload Local Image</label>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={e => {
                          const file = e.target.files[0];
                          if (!file) return;
                          const reader = new FileReader();
                          reader.onloadend = () => setImageUrls(u => ({ ...u, [slot.key]: reader.result }));
                          reader.readAsDataURL(file);
                        }}
                        className="input"
                        style={{ display: 'block', width: '100%', cursor: 'pointer' }}
                      />
                    </div>
                  </div>

                  {/* Preview thumbnail */}
                  <div style={{
                    height: 120, borderRadius: 8, overflow: 'hidden', border: '1px solid var(--color-border)',
                    background: 'repeating-linear-gradient(135deg,#eef2f8,#eef2f8 10px,#e4ebf5 10px,#e4ebf5 20px)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {imageUrls[slot.key] ? (
                      <img src={getImageUrl(imageUrls[slot.key])} alt={slot.label} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                      <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'var(--font-code)', textAlign: 'center', padding: 8 }}>No image yet</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div style={{ background: 'var(--color-error-light)', border: '1px solid var(--color-error)', borderRadius: 'var(--radius-md)', padding: '12px 16px', color: 'var(--color-error)', fontSize: 14, fontWeight: 500, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* ── Navigation ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button
          onClick={onBack}
          className="btn btn-secondary"
          style={{ padding: '12px 24px' }}
        >← Back</button>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="btn btn-primary"
          style={{ padding: '12px 28px' }}
        >{loading ? 'Generating…' : 'Generate Preview →'}</button>
      </div>

      {/* ── Add Field Modal ── */}
      {modalField && (
        <AddFieldModal
          field={modalField}
          onSave={handleSaveField}
          onClose={() => setModalField(null)}
        />
      )}
    </div>
  );
}
