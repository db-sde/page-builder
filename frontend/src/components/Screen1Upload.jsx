import { useState, useRef } from 'react';
import { parseDocx, saveTempJson } from '../api';

export default function Screen1Upload({ session, updateSession, onNext }) {
  const [activeTab, setActiveTab] = useState('docx'); // 'docx' or 'json'
  const [jsonText, setJsonText] = useState(
    session.acf_data && Object.keys(session.acf_data).length > 0
      ? JSON.stringify(session.acf_data, null, 2)
      : ''
  );
  const [file, setFile] = useState(null);
  const [autoDetect, setAutoDetect] = useState(false);
  const [pageType, setPageType] = useState('course');
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const processPayload = (acf_data, detectedType) => {
    let data = JSON.parse(JSON.stringify(acf_data));
    let page_type = detectedType;
    
    // Normalize page type keywords to canonical keys
    if (page_type) {
      const ptLower = page_type.toLowerCase();
      if (ptLower.includes('blog') || ptLower === 'generic') page_type = 'blog';
      else if (ptLower.includes('spec')) page_type = 'specialization';
      else if (ptLower.includes('course')) page_type = 'course';
      else if (ptLower.includes('uni')) page_type = 'university';
    }
    
    if (!page_type) {
      if (data.spec_name) page_type = 'specialization';
      else if (data.program_name) page_type = 'course';
      else if (data.university_full_name || data.established_year) page_type = 'university';
      else if (data.posts || data.content_html) page_type = 'blog';
      else page_type = 'course';
    }

    // Force university_slug to be the one selected/created in Step 1
    let university_slug = session.workspace?.slug;
    if (!university_slug) {
      university_slug = data.university_slug;
    }
    if (!university_slug) {
      const uni_name = data.university_name || data.university_full_name || 'unknown';
      university_slug = uni_name.toLowerCase().replace(' online', '').replace(/'/g, '').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '').trim();
    }

    let slug = data.slug;
    if (!slug) {
      const name = data.spec_name || data.program_name || data.university_name || data.hero_title || data.title;
      if (name) {
        slug = name.toLowerCase().replace(/'/g, '').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '').trim();
        if ((page_type === 'course' || page_type === 'specialization') && !slug.startsWith(university_slug)) {
          slug = `${university_slug}-${slug}`;
        }
      } else {
        slug = 'untitled';
      }
    }

    let parent_slug = data.parent_slug || null; // Backend heuristic resolves the correct parent for specializations

    // Clean metadata keys from data block to prevent duplicate editing fields in Step 2
    delete data.slug;
    delete data.page_type;
    delete data.university_slug;
    delete data.parent_slug;

    updateSession({
      acf_data: data,
      slug,
      page_type,
      university_slug,
      parent_slug
    });
    onNext();
  };

  const handleNextJson = () => {
    setError('');
    let parsed;
    try {
      parsed = JSON.parse(jsonText);
    } catch {
      setError('Invalid JSON — check the ACF data pasted above');
      return;
    }
    
    let payload = parsed.payload || parsed.data || parsed;
    let page_type = parsed.page_type || null;
    processPayload(payload, page_type);
  };

  const handleNextDocx = async () => {
    if (!file) {
      setError('Please select a Word document (.docx) to parse.');
      return;
    }
    setError('');
    setParsing(true);

    try {
      const res = await parseDocx(file, autoDetect ? null : pageType);
      if (!res || !res.payload) {
        throw new Error('Failed to parse document or empty payload returned.');
      }
      await saveTempJson(res);
      processPayload(res.payload, res.page_type);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || 'Error occurred while calling the parser API.');
    } finally {
      setParsing(false);
    }
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      if (!selected.name.toLowerCase().endsWith('.docx')) {
        setError('Only .docx files are supported.');
        setFile(null);
      } else {
        setError('');
        setFile(selected);
      }
    }
  };

  const label = {
    display: 'block',
    fontSize: 12.5,
    fontWeight: 700,
    color: '#33363f',
    marginBottom: 6
  };

  return (
    <div>
      <div className="topbar">
        <div className="topbar-left">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h1 className="topbar-title">Upload Data</h1>
            {session.workspace && (
              <span className="badge badge--published" style={{ fontSize: 12, padding: '4px 10px', height: 'fit-content' }}>
                📁 Workspace: {session.workspace.name}
              </span>
            )}
          </div>
          <p className="topbar-subtitle">Upload a Word document or paste ACF JSON from the Degreebaba PageBuilder pipeline to generate the page.</p>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <button
          onClick={() => { setActiveTab('docx'); setError(''); }}
          className={`btn ${activeTab === 'docx' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, padding: 14 }}
        >
          📄 Parse Word Document (.docx)
        </button>
        <button
          onClick={() => { setActiveTab('json'); setError(''); }}
          className={`btn ${activeTab === 'json' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, padding: 14 }}
        >
          ✏️ Paste ACF JSON
        </button>
      </div>

      {/* Card Body */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-body" style={{ position: 'relative', padding: 28 }}>
          {/* Glassmorphic Loader Overlay */}
          {parsing && (
            <div style={{
              position: 'absolute',
              top: 0, left: 0, right: 0, bottom: 0,
              background: 'rgba(255, 255, 255, 0.8)',
              backdropFilter: 'blur(5px)',
              borderRadius: 'var(--radius-lg)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 10,
              animation: 'fadeIn 0.2s ease'
            }}>
              <div style={{
                width: 48, height: 48,
                border: '4px solid var(--color-border)',
                borderTop: '4px solid var(--color-orange)',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                marginBottom: 16
              }} />
              <div style={{ fontWeight: 700, color: 'var(--color-text-primary)', fontSize: 16 }}>Parsing Document...</div>
              <div style={{ color: 'var(--color-text-secondary)', fontSize: 13, marginTop: 4 }}>This may take 10-15 seconds for AI extraction</div>
            </div>
          )}

          {activeTab === 'docx' ? (
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 16 }}>Word Document (.docx) Parser</div>
              <label style={label}>Select Word Document</label>
              
              {/* Drag & Drop Zone */}
              <div
                onClick={() => fileInputRef.current.click()}
                className={`dropzone ${file ? 'dropzone--has-file' : ''}`}
                style={{
                  border: '2px dashed var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '40px 20px',
                  textAlign: 'center',
                  background: file ? '#f0fdf4' : 'var(--color-bg)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  marginBottom: 20
                }}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".docx"
                  style={{ display: 'none' }}
                />
                {file ? (
                  <div>
                    <div style={{ fontSize: 28, marginBottom: 8 }}>✅</div>
                    <div style={{ fontWeight: 700, color: 'var(--color-success)', fontSize: 15 }}>{file.name}</div>
                    <div style={{ fontSize: 12.5, color: 'var(--color-success)', marginTop: 4 }}>
                      {(file.size / 1024).toFixed(1)} KB · Click to change file
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="dropzone-icon" style={{ margin: '0 auto 12px' }}>
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                    </div>
                    <div style={{ fontWeight: 700, color: 'var(--color-text-primary)', fontSize: 15 }}>Click to browse or drag your file here</div>
                    <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', marginTop: 4 }}>Supports .docx formatted documents</div>
                  </div>
                )}
              </div>

              {/* Options */}
              <div style={{ borderTop: '1px solid var(--color-border-light)', paddingTop: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--color-text-primary)' }}>Auto-detect page type</div>
                    <div style={{ fontSize: 12.5, color: 'var(--color-text-secondary)', marginTop: 2 }}>Uses text analysis to identify the template type</div>
                  </div>
                  <label className="toggle-wrap" htmlFor="toggle-auto-detect">
                    <div className="toggle">
                      <input
                        type="checkbox"
                        id="toggle-auto-detect"
                        checked={autoDetect}
                        onChange={(e) => setAutoDetect(e.target.checked)}
                      />
                      <span className="toggle-slider" />
                    </div>
                  </label>
                </div>

                {!autoDetect && (
                  <div style={{ animation: 'fadeIn 0.2s ease' }}>
                    <label style={label}>Page Type</label>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      {[
                        { value: 'course', label: '🎓 Course Page' },
                        { value: 'specialization', label: '🔬 Specialization Page' },
                        { value: 'university', label: '🏛️ University Page' },
                        { value: 'blog', label: '✍️ Blog Page' }
                      ].map((opt) => {
                        const active = pageType === opt.value;
                        return (
                          <button
                            key={opt.value}
                            type="button"
                            onClick={() => setPageType(opt.value)}
                            className="btn"
                            style={{
                              flex: '1 1 calc(50% - 5px)',
                              padding: '14px 18px',
                              background: active ? 'var(--color-navy)' : '#fff',
                              color: active ? '#fff' : 'var(--color-text-primary)',
                              border: active ? '1.5px solid var(--color-navy)' : '1.5px solid var(--color-border)',
                              borderRadius: 'var(--radius-md)',
                              fontWeight: 700,
                              boxShadow: active ? 'var(--shadow-sm)' : 'none',
                              textAlign: 'center',
                              cursor: 'pointer',
                              transition: 'all 0.15s ease',
                              display: 'inline-block'
                            }}
                          >
                            {opt.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 16 }}>ACF JSON Data</div>
              <label style={label}>Paste ACF JSON output from the Degreebaba PageBuilder pipeline</label>
              <textarea
                rows={12}
                placeholder='{ "program_name": "Degreebaba Online MBA", "hero_description": "...", ... }'
                value={jsonText}
                onChange={e => setJsonText(e.target.value)}
                className="input"
                style={{
                  width: '100%',
                  fontFamily: 'var(--font-code)',
                  background: '#f8fafc',
                  resize: 'vertical',
                }}
              />
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 8 }}>
                This is the raw ACF output from the Degreebaba PageBuilder pipeline. Slug, page type, and metadata will be derived dynamically.
              </div>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div style={{ background: 'var(--color-error-light)', border: '1px solid var(--color-error)', borderRadius: 'var(--radius-md)', padding: '12px 16px', color: 'var(--color-error)', fontSize: 14, fontWeight: 500, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* Footer Navigation */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        {activeTab === 'docx' ? (
          <button
            onClick={handleNextDocx}
            disabled={!file || parsing}
            className="btn btn-primary btn-lg"
          >
            {parsing ? 'Parsing Document…' : 'Parse & Import Document →'}
          </button>
        ) : (
          <button
            onClick={handleNextJson}
            className="btn btn-primary btn-lg"
          >
            Continue to Review →
          </button>
        )}
      </div>
    </div>
  );
}
