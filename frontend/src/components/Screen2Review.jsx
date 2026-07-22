import { useState, useEffect } from 'react';
import { ingestAcf, previewHtml, saveDraft, detectParent, remapParent, generateSpecializationStub, getWorkspaceTree } from '../api';
import FieldHealthPanel from './FieldHealthPanel';
import AddFieldModal from './AddFieldModal';
import RepeaterEditor from './RepeaterEditor';
import StepListEditor from './StepListEditor';
import { FIELD_SCHEMA, SYSTEM_FIELDS, REPEATER_FIELDS, getFieldCategory, getFieldPlaceholder, isPlaceholder } from '../fieldSchema';

// Image slots required per page type
const IMAGE_SLOTS = {
  university: [
    { key: 'hero_image_url', label: 'Hero Image', hint: 'Homepage hero or campus banner', dims: '480 × 420px', required: true },
  ],
  course: [
    { key: 'hero_image_url', label: 'Hero Image', hint: 'The main visual at the top of the page', dims: '480 × 420px', required: true },
    { key: 'certificate_image_url', label: 'Degree Certificate Image', hint: 'Sample degree certificate visual shown in Placement section', dims: '320 × 240px' },
  ],
  specialization: [
    { key: 'hero_image_url', label: 'Hero Image', hint: 'The main visual at the top of the page', dims: '480 × 420px', required: true },
  ],
  blog: [
    { key: 'hero_image_url', label: 'Article Hero Image', hint: 'The main visual at the top of the article', dims: '460 × 340px', required: true },
  ],
};

const LONG_TEXT_FIELDS = new Set([
  'about_content', 'why_choose_content', 'eligibility_content', 'admission_steps',
  'syllabus_content', 'placement_content', 'emi_content', 'exam_content',
  'certificate_description', 'content_html',
]);

const REPEATER_PRIMARY_FIELDS = {
  highlights: 'highlight_title',
  facts: 'fact_title',
  accreditations: 'body_name',
  reviews: 'review_text',
  faculty_members: 'member_name',
  faqs: 'question',
  fee_plans: 'plan_name',
  job_profiles: 'job_title',
  other_specs: 'other_spec_name',
};

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

function buildDraftAcf(session, fields, heroImageAlt) {
  const contentData = { ...session.acf_data, ...fieldsToAcf(fields), hero_image_alt: heroImageAlt };
  const documentTitle = contentData.title || contentData.spec_name || contentData.program_name ||
    contentData.university_full_name || contentData.university_name || contentData.hero_title ||
    contentData._meta?.document_title || 'Untitled page';
  return {
    ...contentData,
    _meta: {
      ...(contentData._meta && typeof contentData._meta === 'object' ? contentData._meta : {}),
      document_title: documentTitle,
      page_type: session.page_type,
      generated_by: 'DegreeBaba Content Publisher',
    },
  };
}

/** Initialise the editable fields state from session.acf_data, excluding metadata keys and structured (object/array) fields. */
function initFields(acf_data, page_type) {
  const excludedKeys = [
    'slug', 'page_type', 'university_slug', 'parent_slug',
    'hero_image_url', 'certificate_image_url', 'og_image_url', 'featured_image_url',
    'hero_image_alt', '_meta'
  ];
  const out = {};
  const schema = FIELD_SCHEMA[page_type] || [];
  const schemaKeys = schema.map(f => f.key);

  // 1. Pre-populate all schema fields, converting placeholders to ''
  for (const field of schema) {
    if (excludedKeys.includes(field.key) || SYSTEM_FIELDS.has(field.key)) continue;
    const v = acf_data[field.key];
    if (isPlaceholder(v)) {
      out[field.key] = '';
    } else if (REPEATER_FIELDS.has(field.key) && Array.isArray(v)) {
      // One-time import filter: drop items that don't have the expected primary key
      // (catches wrong-keyed data e.g. label/value instead of fact_title/fact_description,
      // and backend-seeded empty rows). Runs only here so add/remove buttons work freely.
      const primaryField = REPEATER_PRIMARY_FIELDS[field.key];
      const meaningful = primaryField
        ? v.filter(item => item && typeof item === 'object' &&
            item[primaryField] !== '' && item[primaryField] !== null && item[primaryField] !== undefined)
        : v.filter(item => item && typeof item === 'object' &&
            Object.values(item).some(val => val !== '' && val !== null && val !== undefined));
      out[field.key] = JSON.stringify(meaningful, null, 2);
    } else if (typeof v === 'object' && v !== null) {
      out[field.key] = JSON.stringify(v, null, 2);
    } else {
      out[field.key] = String(v);
    }
  }

  // 2. Add other fields present in acf_data not in schema
  for (const [k, v] of Object.entries(acf_data)) {
    if (excludedKeys.includes(k) || SYSTEM_FIELDS.has(k)) continue;
    if (schemaKeys.includes(k)) continue;
    out[k] = isPlaceholder(v)
      ? ''
      : (typeof v === 'object' && v !== null ? JSON.stringify(v, null, 2) : String(v));
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
  const [draftSaveState, setDraftSaveState] = useState('saved');
  const [modalField, setModalField] = useState(null);   // field object or null
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

  const slots = IMAGE_SLOTS[session.page_type] || [];

  useEffect(() => {
    if (!session.slug || !session.page_type || !session.university_slug) return undefined;
    let cancelled = false;
    const timer = setTimeout(async () => {
      setDraftSaveState('saving');
      const draftData = buildDraftAcf(session, fields, heroImageAlt);
      try {
        await saveDraft({
          ...draftData,
          slug: session.slug,
          page_type: session.page_type,
          university_slug: session.university_slug,
          parent_slug: session.parent_slug,
        }, imageUrls);
        if (!cancelled) setDraftSaveState('saved');
      } catch {
        if (!cancelled) setDraftSaveState('error');
      }
    }, 800);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [fields, heroImageAlt, imageUrls, session]);

  // ── Field modal handlers ──────────────────────────────────────────────────
  const handleAddField = (field) => {
    setModalField(field);
  };

  const handleSaveField = (key, rawValue) => {
    setFields(f => ({ ...f, [key]: rawValue }));
    setModalField(null);
  };

  const handleRepeaterChange = (key, items) => {
    setFields(current => ({ ...current, [key]: JSON.stringify(items) }));
  };

  // ── Generate preview ──────────────────────────────────────────────────────
  const handleGenerate = async () => {
    setError('');
    
    // Image Slots is the only authoring source for image fields.
    const needed = slots.filter(slot => slot.required).map(slot => slot.key);
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
      const rebuilt = buildDraftAcf(session, fields, heroImageAlt);

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

  const schema = FIELD_SCHEMA[session.page_type] || [];
  const schemaByKey = Object.fromEntries(schema.map(field => [field.key, field]));
  const contentFields = Object.entries(fields)
    .filter(([key, value]) => key !== 'admission_steps' && schemaByKey[key] &&
      ['required', 'optional'].includes(getFieldCategory(schemaByKey[key])) &&
      (schemaByKey[key].required || value !== ''))
    .map(([key, value]) => ({ ...schemaByKey[key], value }));
  const contentGroups = contentFields.reduce((groups, field) => {
    groups[field.section] = [...(groups[field.section] || []), field];
    return groups;
  }, {});
  const repeaterFields = schema.filter(field => getFieldCategory(field) === 'repeater');
  const templateFields = schema.filter(field => getFieldCategory(field) === 'template-default');
  const admissionField = schema.find(field => field.key === 'admission_steps');

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
            <h1 className="topbar-title">Edit Page</h1>
            {session.workspace && (
              <span className="badge badge--published" style={{ fontSize: 12, padding: '4px 10px', height: 'fit-content' }}>
                📁 Workspace: {session.workspace.name}
              </span>
            )}
          </div>
          <p className="topbar-subtitle">Review the imported content, add structured sections, and choose the page images.</p>
        </div>
        <div style={{ fontSize: 12.5, fontWeight: 700, color: draftSaveState === 'error' ? 'var(--color-error)' : 'var(--color-text-secondary)' }}>
          {draftSaveState === 'saving' ? 'Saving draft…' : draftSaveState === 'error' ? 'Draft save failed' : '✓ Draft saved'}
        </div>
      </div>

      {/* ── Field Health Panel ── */}
      <FieldHealthPanel
        acf_data={liveAcf}
        page_type={session.page_type}
        onAddField={handleAddField}
        imageReady={slots.filter(slot => slot.required).every(slot => Boolean(imageUrls[slot.key]))}
        imageLabel={slots.find(slot => slot.required)?.label || 'Hero image'}
      />

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

      {/* ── Writer content ── */}
      {contentFields.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-body" style={{ padding: 20 }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>Page content</div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 14 }}>Review the extracted content. Open only the sections you need to change.</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {Object.entries(contentGroups).map(([section, sectionFields], sectionIndex) => (
                <details key={section} defaultOpen={sectionIndex === 0} style={{ border: '1px solid var(--color-border)', borderRadius: 8, background: '#fff' }}>
                  <summary style={{ padding: '10px 12px', cursor: 'pointer', fontSize: 13, fontWeight: 800, color: 'var(--color-text-primary)' }}>{section}</summary>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12, padding: '4px 12px 12px', borderTop: '1px solid var(--color-border)' }}>
                    {sectionFields.map(field => {
                      const isFieldEmpty = field.value === '';
                      return (
                        <div key={field.key} style={{ gridColumn: LONG_TEXT_FIELDS.has(field.key) ? '1 / -1' : undefined }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                            <label style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--color-text-primary)' }}>{field.label}</label>
                            {field.required && <span style={{ fontSize: 11, color: '#c53030', fontWeight: 800 }}>Required</span>}
                          </div>
                          {LONG_TEXT_FIELDS.has(field.key) ? (
                            <textarea className="input" rows={4} value={field.value} placeholder={getFieldPlaceholder(field)} onChange={event => setFields(current => ({ ...current, [field.key]: event.target.value }))} style={{ width: '100%', resize: 'vertical', borderColor: isFieldEmpty && field.required ? '#feb2b2' : undefined }} />
                          ) : (
                            <input className="input" value={field.value} placeholder={getFieldPlaceholder(field)} onChange={event => setFields(current => ({ ...current, [field.key]: event.target.value }))} style={{ width: '100%', borderColor: isFieldEmpty && field.required ? '#feb2b2' : undefined }} />
                          )}
                          {isFieldEmpty && field.required && <div style={{ color: '#c53030', fontSize: 11.5, marginTop: 4, fontWeight: 600 }}>Required content was not found in the document</div>}
                        </div>
                      );
                    })}
                  </div>
                </details>
              ))}
            </div>
          </div>
        </div>
      )}

      {admissionField && (
        <details className="card" style={{ marginBottom: 12 }}>
          <summary style={{ padding: '12px 16px', cursor: 'pointer', fontSize: 14, fontWeight: 800, color: 'var(--color-text-primary)' }}>Admission Steps</summary>
          <div style={{ padding: '2px 16px 16px', borderTop: '1px solid var(--color-border)' }}>
            <p style={{ fontSize: 12.5, margin: '10px 0' }}>Review the application journey in the order a student should follow it.</p>
            <StepListEditor value={fields.admission_steps || ''} onChange={value => setFields(current => ({ ...current, admission_steps: value }))} />
          </div>
        </details>
      )}

      {repeaterFields.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-body" style={{ padding: 20 }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>Structured content</div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 14 }}>Items stay collapsed so you can scan the page quickly.</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 10, alignItems: 'start' }}>
              {repeaterFields.map(field => {
                // Filtering only happens once in initFields at import time.
                // The render just parses whatever is in fields state — no re-filtering —
                // so add/remove buttons work without items disappearing.
                let items;
                try {
                  const parsed = fields[field.key] ? JSON.parse(fields[field.key]) : [];
                  items = Array.isArray(parsed) ? parsed : [];
                } catch {
                  items = [];
                }
                if (items.length === 0) items = [{}];
                return <RepeaterEditor key={field.key} fieldKey={field.key} label={field.label} items={items} onChange={itemsValue => handleRepeaterChange(field.key, itemsValue)} />;
              })}
            </div>
          </div>
        </div>
      )}

      {templateFields.length > 0 && (
        <details className="card" style={{ marginBottom: 20 }}>
          <summary style={{ padding: '18px 24px', cursor: 'pointer', fontWeight: 800, color: 'var(--color-text-primary)' }}>
            Advanced Customization · Section headings
          </summary>
          <div style={{ padding: '0 24px 24px' }}>
            <p style={{ fontSize: 13, marginBottom: 16 }}>The page uses clear default headings. Only add an override when the wording needs to be different.</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 16 }}>
              {templateFields.map(field => (
                <div key={field.key}>
                  <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>{field.label}</label>
                  <input className="input" value={fields[field.key] || ''} placeholder="Use template default" onChange={event => setFields(current => ({ ...current, [field.key]: event.target.value }))} style={{ width: '100%' }} />
                </div>
              ))}
            </div>
          </div>
        </details>
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
          <div className="card-body" style={{ padding: 20 }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>Image Slots</div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 20 }}>
              Add the page visuals here. The image you choose is applied to the page automatically.
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {slots.map(slot => (
                <div
                  key={slot.key}
                  style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: 14, display: 'grid', gridTemplateColumns: '1fr 160px', gap: 14, alignItems: 'center' }}
                >
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--color-text-primary)', fontSize: 14.5 }}>
                      {slot.label}{slot.required && <span style={{ color: 'var(--color-error)', marginLeft: 5 }}>*</span>}
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>{slot.hint}</div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 3 }}>Recommended: {slot.dims}</div>

                    <div style={{ marginTop: 12 }}>
                      <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>Image URL</label>
                      <input
                        className="input"
                        placeholder="Example: https://example.com/campus.jpg"
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

                    {slot.key === 'hero_image_url' && (
                      <div style={{ marginTop: 12 }}>
                        <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>Alt Text</label>
                        <input
                          className="input"
                          placeholder="Example: Students attending an online lecture"
                          value={heroImageAlt}
                          onChange={e => setHeroImageAlt(e.target.value)}
                          style={{ width: '100%' }}
                        />
                      </div>
                    )}
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
