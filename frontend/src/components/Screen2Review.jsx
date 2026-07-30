import { useState, useEffect } from 'react';
import { ingestAcf, previewHtml, detectParent, remapParent, generateSpecializationStub, getWorkspaceTree, getPageBlueprint } from '../api';
import SectionContentEditor from './SectionContentEditor';
import { FIELD_SCHEMA, isPlaceholder } from '../fieldSchema';
import BlogEditor from './BlogEditor';

// Legacy pages without a Blueprint retain their explicit image-slot fallback.
// Blog now uses the same Blueprint contract as the other page types.
const LEGACY_IMAGE_SLOTS = {
  blog: [
    { key: 'hero_image_url', label: 'Article Hero Image', hint: 'Main article header banner image displayed on the right of the title', dims: '460 × 340px', required: true },
  ],
};

function formatApiError(error) {
  let payload = error.response?.data;
  // Preview responses are HTML on success, so Axios returns error bodies as
  // text too. Decode FastAPI's JSON error before falling back to its message.
  if (typeof payload === 'string') {
    try {
      payload = JSON.parse(payload);
    } catch {
      // Keep the raw response as the final fallback below.
    }
  }
  const detail = payload?.detail;
  if (detail && typeof detail === 'object') {
    const labels = (detail.missing_fields || []).map(field => field.label).filter(Boolean);
    return labels.length ? `${detail.message} Missing: ${labels.join(', ')}.` : detail.message;
  }
  return detail || payload?.error || (typeof payload === 'string' ? payload : null) || error.message || String(error);
}

// ── helpers ──────────────────────────────────────────────────────────────────

/** Convert the fields state (all strings) to a proper acf_data dict. */
function fieldsToAcf(fields) {
  const out = {};
  for (const [k, v] of Object.entries(fields)) {
    // Attempt to parse anything that looks like JSON
    if (typeof v === 'string' && (v.startsWith('[') || v.startsWith('{'))) {
      try {
        out[k] = JSON.parse(v);
        continue;
      } catch {
        // Keep the original string when a user is still editing JSON.
      }
    }
    out[k] = v;
  }
  return out;
}

/** Initialise the editable fields state from session.acf_data, excluding metadata keys and structured (object/array) fields. */
function initFields(acf_data, page_type) {
  const excludedKeys = [
    'slug', 'page_type', 'university_slug', 'parent_slug',
    'hero_image_url', 'certificate_image_url', 'og_image_url', 'featured_image_url',
    'hero_image_alt'
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

function initStructuredFields(acfData) {
  const output = {};
  for (const [name, value] of Object.entries(acfData || {})) {
    if (name === '_meta') continue;
    if (Array.isArray(value)) output[name] = value;
  }
  return output;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function Screen2Review({ session, updateSession, onNext, onBack }) {
  const [fields, setFields]       = useState(() => initFields(session.acf_data, session.page_type));
  const [structuredFields, setStructuredFields] = useState(() => initStructuredFields(session.acf_data));
  const [imageUrls, setImageUrls] = useState(() => {
    const initImages = { ...session.images };
    const neededKeys = ['hero_image_url', 'certificate_image_url', 'og_image_url', 'featured_image_url'];
    for (const key of neededKeys) {
      if (session.acf_data && session.acf_data[key]) {
        initImages[key] = session.acf_data[key];
      }
    }
    return initImages;
  });
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');
  const [blueprint, setBlueprint] = useState(null);
  const [blueprintLoading, setBlueprintLoading] = useState(false);
  const [heroImageAlt, setHeroImageAlt] = useState(() => {
    return session.acf_data?.hero_image_alt || '';
  });

  // ── Parent Mapping state (specialization only) ────────────────────────────
  const [parentInfo, setParentInfo]     = useState(null);   // { detected_parent_slug, confidence, available_courses }
  const [parentLoading, setParentLoading] = useState(false);
  const [showParentDropdown, setShowParentDropdown] = useState(false);
  const [parentRemapping, setParentRemapping] = useState(false);
  const [parentError, setParentError] = useState('');

  // ── Detected Specializations state (course only) ─────────────────────────
  const [workspaceSpecs, setWorkspaceSpecs] = useState([]);
  const [specStates, setSpecStates] = useState({});

  useEffect(() => {
    if (!['university', 'course', 'specialization', 'blog'].includes(session.page_type)) return;
    setBlueprintLoading(true);
    getPageBlueprint(session.page_type)
      .then(setBlueprint)
      .catch(err => {
        console.warn('Failed to load page blueprint:', err);
        setError('The page editing contract could not be loaded. Please try again.');
      })
      .finally(() => setBlueprintLoading(false));
  }, [session.page_type]);

  useEffect(() => {
    if (session.page_type !== 'course' || !session.university_slug) return;
    getWorkspaceTree(session.university_slug)
      .then(tree => {
        if (tree && tree.specializations) {
          setWorkspaceSpecs(tree.specializations);
        }
      })
      .catch(err => console.warn('Failed to load workspace specializations:', err));
  }, [session.page_type, session.university_slug]);

  const handleExecuteSpecAction = async (specName) => {
    const currentState = specStates[specName] || { action: 'skip' };
    
    setSpecStates(prev => ({
      ...prev,
      [specName]: { ...currentState, loading: true, error: '' }
    }));

    try {
      if (currentState.action === 'generate') {
        const result = await generateSpecializationStub(
          session.university_slug,
          specName,
          session.slug
        );
        setSpecStates(prev => ({
          ...prev,
          [specName]: {
            ...currentState,
            loading: false,
            completed: true,
            slug: result.slug
          }
        }));
      } else if (currentState.action === 'link') {
        if (!currentState.selectedSlug) {
          throw new Error('Please select an existing specialization page to link');
        }
        await remapParent(
          session.university_slug,
          currentState.selectedSlug,
          session.slug
        );
        setSpecStates(prev => ({
          ...prev,
          [specName]: {
            ...currentState,
            loading: false,
            completed: true
          }
        }));
      }
      
      // Refresh specs listing
      const tree = await getWorkspaceTree(session.university_slug);
      if (tree && tree.specializations) {
        setWorkspaceSpecs(tree.specializations);
      }
    } catch (err) {
      setSpecStates(prev => ({
        ...prev,
        [specName]: {
          ...currentState,
          loading: false,
          error: err.response?.data?.detail || err.message || 'Operation failed'
        }
      }));
    }
  };

  useEffect(() => {
    if (session.page_type !== 'specialization') return;
    if (!session.slug || !session.university_slug) return;
    setParentLoading(true);
    detectParent(session.slug, session.university_slug, session.parent_slug)
      .then(info => setParentInfo(info))
      .catch(err => console.warn('Parent detection failed:', err))
      .finally(() => setParentLoading(false));
  }, [session.page_type, session.slug, session.university_slug, session.parent_slug]);

  const handleParentChange = async (newParentSlug) => {
    setParentError('');
    setParentRemapping(true);
    try {
      // Update in session immediately (affects the preview + save flow)
      updateSession({ parent_slug: newParentSlug });
      // If this spec is already saved in workspace, persist the remap on disk too
      if (session.workspace && session.slug) {
        await remapParent(session.university_slug, session.slug, newParentSlug);
      }
      setParentInfo(prev => ({ ...prev, detected_parent_slug: newParentSlug, confidence: 'manual' }));
      setShowParentDropdown(false);
    } catch {
      setParentError('Failed to update parent assignment. You can still proceed.');
    } finally {
      setParentRemapping(false);
    }
  };

  const slots = blueprint
    ? (blueprint.image_fields || []).map(name => ({ key: name, ...blueprint.fields[name] }))
    : (LEGACY_IMAGE_SLOTS[session.page_type] || []);

  // ── Generate preview ──────────────────────────────────────────────────────
  const generatePreview = async (rebuilt, uploadedImages, slugOverride = session.slug) => {
    setError('');
    setLoading(true);
    try {
      const metadata = {
        page_type:       session.page_type,
        slug:            slugOverride,
        university_slug: session.university_slug,
        parent_slug:     session.parent_slug,
      };

      const merged = { ...rebuilt, ...metadata, ...uploadedImages };
      const rawWithMeta = { ...rebuilt, ...metadata };

      updateSession({ acf_data: rebuilt, images: uploadedImages, raw_acf_data: rawWithMeta });

      // Step A: transformer context
      const result = await ingestAcf({ acf_data: merged });
      if (result.status !== 'ok') {
        setError(result.error || 'Failed to process ACF data');
        setLoading(false);
        return;
      }

      // Step B: render HTML
      const htmlText = await previewHtml({ acf_data: merged, images: uploadedImages });

      updateSession({
        context:         result.context,
        slug:            result.slug     || session.slug,
        page_type:       result.page_type || session.page_type,
        university_slug: result.university_slug || session.university_slug,
        parent_slug:     result.parent_slug,
        acf_data:        result.acf_data,
        field_state:     result.field_state || {},
        editing_state:   result.editing_state || {},
        images:          uploadedImages,
        raw_acf_data:    rawWithMeta,
        htmlContent:     htmlText,
      });
      onNext();
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    const rebuilt = { ...session.acf_data, ...fieldsToAcf(fields), ...structuredFields, hero_image_alt: heroImageAlt };
    try {
      await generatePreview(rebuilt, imageUrls);
    } catch (e) {
      setError(formatApiError(e));
    }
  };

  const editorValues = {
    ...session.acf_data,
    ...fieldsToAcf(fields),
    ...structuredFields,
    ...imageUrls,
    hero_image_alt: heroImageAlt,
  };

  const isListingPage = ['programs_listing', 'specializations_listing', 'blog_listing'].includes(session.page_type);

  const getImageUrl = (url) => {
    if (!url) return '';
    if (url.startsWith('/assets/images/')) {
      return `http://localhost:8000${url}`;
    }
    return url;
  };

  if (session.page_type === 'blog') {
    return <BlogEditor
      key={`${session.university_slug}-${session.slug}`}
      session={session}
      blueprint={blueprint}
      loading={loading || blueprintLoading}
      onBack={onBack}
      onPreview={generatePreview}
    />;
  }

  return (
    <div>
      <div className="topbar">
        <div className="topbar-left">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h1 className="topbar-title">Page Content</h1>
            {session.workspace && (
              <span className="badge badge--published" style={{ fontSize: 12, padding: '4px 10px', height: 'fit-content' }}>
                📁 Workspace: {session.workspace.name}
              </span>
            )}
          </div>
          <p className="topbar-subtitle">Review each page section, complete missing content, and add images before previewing.</p>
        </div>
      </div>

      {/* ── Table Ingestion Warnings ── */}
      {session.table_warnings && session.table_warnings.length > 0 && (
        <div className="card" style={{ marginBottom: 20, borderLeft: '4px solid var(--color-warning)', background: 'var(--color-warning-light)' }}>
          <div className="card-body" style={{ padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
              <span style={{ fontSize: 18 }}>⚠</span>
              <div style={{ fontSize: 15, fontWeight: 800, color: 'var(--color-warning)' }}>
                Table Ingestion Warning
              </div>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {session.table_warnings.map((w, idx) => (
                <div key={idx} style={{ background: '#fff', border: '1px solid var(--color-border)', borderRadius: 8, padding: 16 }}>
                  <div style={{ fontWeight: 700, color: 'var(--color-text-primary)', fontSize: 13, marginBottom: 8 }}>
                    Table Title:
                  </div>
                  <div style={{ fontStyle: 'italic', fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
                    {w.table_title || '(Untitled Table)'}
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                    <div>
                      <div style={{ fontWeight: 700, color: '#c53030', fontSize: 12, marginBottom: 6 }}>
                        Detected Headers:
                      </div>
                      <div style={{ fontSize: 12, fontFamily: 'var(--font-code)', color: '#c53030', whiteSpace: 'pre-wrap' }}>
                        {(w.detected_headers || []).join('\n')}
                      </div>
                    </div>
                    
                    <div>
                      <div style={{ fontWeight: 700, color: '#166534', fontSize: 12, marginBottom: 6 }}>
                        Suggested Headers:
                      </div>
                      <div style={{ fontSize: 12, fontFamily: 'var(--font-code)', color: '#166534', whiteSpace: 'pre-wrap' }}>
                        {(w.suggested_headers || []).join('\n')}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}


      {/* ── Detected Academic Specializations Panel (course only) ── */}
      {session.page_type === 'course' && session.acf_data?.detected_specializations?.length > 0 && (
        <div className="card" style={{ marginBottom: 20, borderLeft: '4px solid #4f46e5' }}>
          <div className="card-body" style={{ padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)' }}>
                🔍 Detected Academic Specializations
              </div>
              <span className="badge" style={{ background: '#e0e7ff', color: '#4338ca', fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 99, height: 'fit-content' }}>
                {session.acf_data.detected_specializations.length} found
              </span>
            </div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 20 }}>
              The parser detected these academic specializations from the document tables. Generate new pages, link them to existing pages, or skip them.
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {session.acf_data.detected_specializations.map((spec) => {
                const state = specStates[spec] || { action: 'skip' };
                const isCompleted = state.completed;
                
                return (
                  <div key={spec} style={{
                    display: 'grid',
                    gridTemplateColumns: '1.2fr 1.8fr 1fr',
                    gap: 16,
                    alignItems: 'center',
                    padding: '12px 16px',
                    border: '1px solid var(--color-border)',
                    borderRadius: 8,
                    background: isCompleted ? '#f0fdf4' : '#f8fafc',
                    borderColor: isCompleted ? '#bbf7d0' : undefined,
                    transition: 'all 0.2s ease',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: 14 }}>
                        {spec}
                      </div>
                      {isCompleted && (
                        <div style={{ fontSize: 11, color: '#166534', fontWeight: 700, marginTop: 2, display: 'flex', alignItems: 'center', gap: 4 }}>
                          <span>✓</span> {state.action === 'generate' ? 'Page Generated' : 'Linked Successfully'}
                        </div>
                      )}
                      {state.error && (
                        <div style={{ fontSize: 11, color: '#991b1b', fontWeight: 600, marginTop: 2 }}>
                          ⚠ {state.error}
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      {!isCompleted ? (
                        <>
                          <select
                            className="input"
                            value={state.action}
                            onChange={(e) => setSpecStates(prev => ({
                              ...prev,
                              [spec]: { ...prev[spec], action: e.target.value }
                            }))}
                            style={{ maxWidth: 150, fontSize: 12.5, padding: '4px 8px' }}
                          >
                            <option value="skip">Skip / Ignore</option>
                            <option value="generate">Generate Page</option>
                            <option value="link">Link Existing</option>
                          </select>

                          {state.action === 'link' && (
                            <select
                              className="input"
                              value={state.selectedSlug || ''}
                              onChange={(e) => setSpecStates(prev => ({
                                ...prev,
                                [spec]: { ...prev[spec], selectedSlug: e.target.value }
                              }))}
                              style={{ flex: 1, fontSize: 12.5, padding: '4px 8px', fontFamily: 'var(--font-code)' }}
                            >
                              <option value="">— select spec —</option>
                              {workspaceSpecs.map(wsSpec => (
                                <option key={wsSpec.slug} value={wsSpec.slug}>
                                  {wsSpec.slug.replace(`${session.university_slug}-`, '').replace(/-/g, ' ').toUpperCase()} ({wsSpec.slug})
                                </option>
                              ))}
                            </select>
                          )}
                        </>
                      ) : (
                        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', fontFamily: 'var(--font-code)' }}>
                          slug: {state.slug || state.selectedSlug}
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      {!isCompleted && state.action !== 'skip' && (
                        <button
                          className="btn btn-primary"
                          disabled={state.loading || (state.action === 'link' && !state.selectedSlug)}
                          onClick={() => handleExecuteSpecAction(spec)}
                          style={{ padding: '6px 14px', fontSize: 12, borderRadius: 6 }}
                        >
                          {state.loading ? 'Processing…' : state.action === 'generate' ? 'Generate' : 'Link'}
                        </button>
                      )}
                      {isCompleted && (
                        <span style={{ fontSize: 12.5, color: '#166534', fontWeight: 600 }}>
                          Done
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── Parent Course Mapping Panel (specialization only) ── */}
      {session.page_type === 'specialization' && (
        <div className="card" style={{ marginBottom: 20, borderLeft: '4px solid #4f46e5' }}>
          <div className="card-body" style={{ padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)' }}>
                🔗 Parent Course Assignment
              </div>
              {parentInfo && (
                <span style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '2px 9px',
                  borderRadius: 99,
                  background: parentInfo.confidence === 'auto' ? '#dcfce7' :
                              parentInfo.confidence === 'manual' ? '#dbeafe' :
                              parentInfo.confidence === 'heuristic' ? '#fef9c3' : '#fee2e2',
                  color: parentInfo.confidence === 'auto' ? '#166534' :
                         parentInfo.confidence === 'manual' ? '#1d4ed8' :
                         parentInfo.confidence === 'heuristic' ? '#92400e' : '#991b1b',
                }}>
                  {parentInfo.confidence === 'auto' ? '✓ Confirmed' :
                   parentInfo.confidence === 'manual' ? '✎ Manual' :
                   parentInfo.confidence === 'heuristic' ? '~ Auto-detected' : '⚠ Not assigned'}
                </span>
              )}
            </div>

            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 14 }}>
              This specialization will only appear under its assigned parent course. Verify the assignment is correct before generating.
            </div>

            {parentLoading && (
              <div style={{ fontSize: 13, color: 'var(--color-text-muted)', fontStyle: 'italic' }}>Detecting parent course…</div>
            )}

            {!parentLoading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <div style={{
                  background: '#f1f5f9',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  padding: '8px 14px',
                  fontFamily: 'var(--font-code)',
                  fontSize: 13,
                  color: parentInfo?.detected_parent_slug ? 'var(--color-text-primary)' : '#9ca3af',
                  fontWeight: 600,
                  minWidth: 200,
                }}>
                  {parentInfo?.detected_parent_slug || '(none — please assign)'}
                </div>

                {!showParentDropdown && (
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '8px 16px', fontSize: 13 }}
                    onClick={() => setShowParentDropdown(true)}
                  >
                    ✎ Change
                  </button>
                )}
              </div>
            )}

            {showParentDropdown && !parentLoading && (
              <div style={{ marginTop: 14 }}>
                <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>
                  Select Parent Course
                </label>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <select
                    className="input"
                    defaultValue={parentInfo?.detected_parent_slug || ''}
                    onChange={e => e.target.value && handleParentChange(e.target.value)}
                    style={{ flex: 1, fontFamily: 'var(--font-code)', fontSize: 13 }}
                    disabled={parentRemapping}
                  >
                    <option value="">— select a course —</option>
                    {(parentInfo?.available_courses || []).map(c => (
                      <option key={c.slug} value={c.slug}>
                        {c.name} ({c.slug})
                      </option>
                    ))}
                  </select>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '8px 14px', fontSize: 13 }}
                    onClick={() => setShowParentDropdown(false)}
                    disabled={parentRemapping}
                  >
                    Cancel
                  </button>
                </div>
                {parentRemapping && (
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 6 }}>Saving assignment…</div>
                )}
              </div>
            )}

            {parentError && (
              <div style={{ marginTop: 10, fontSize: 13, color: 'var(--color-error)', fontWeight: 600 }}>⚠ {parentError}</div>
            )}
          </div>
        </div>
      )}

      {blueprintLoading && (
        <div className="card author-loading">Loading page sections…</div>
      )}

      {!blueprintLoading && blueprint && (
        <SectionContentEditor
          blueprint={blueprint}
          editingState={session.editing_state}
          values={editorValues}
          onChange={(name, value) => {
            if (Array.isArray(value)) {
              setStructuredFields(current => ({ ...current, [name]: value }));
              setFields(current => {
                const next = { ...current };
                delete next[name];
                return next;
              });
            } else {
              setFields(current => ({ ...current, [name]: value }));
              setStructuredFields(current => {
                const next = { ...current };
                delete next[name];
                return next;
              });
            }
          }}
          slots={slots}
          imageUrls={imageUrls}
          heroImageAlt={heroImageAlt}
          onImageChange={(name, value) => setImageUrls(current => ({ ...current, [name]: value }))}
          onAltChange={setHeroImageAlt}
          getImageUrl={getImageUrl}
        />
      )}

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

    </div>
  );
}
