import { useState, useEffect } from 'react';
import { listWorkspaces, getWorkspaceTree, compileWorkspace, createWorkspace } from '../api';

export default function Screen0Workspace({ session, updateSession, onNext }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Selection and Creation States
  const [selectedSlug, setSelectedSlug] = useState(session.workspace?.slug || '');
  const [newUniName, setNewUniName] = useState('');
  const [newUniSlug, setNewUniSlug] = useState('');
  const [creating, setCreating] = useState(false);
  
  // Workspace Tree View
  const [treeData, setTreeData] = useState(null);
  const [treeLoading, setTreeLoading] = useState(false);

  // Compile States
  const [compiling, setCompiling] = useState(false);
  const [compileResult, setCompileResult] = useState(null);

  // Load available workspaces
  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const fetchWorkspaces = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await listWorkspaces();
      // API now returns array of objects: { slug, name, ... }
      setWorkspaces(res.workspaces || []);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch workspaces from backend.');
    } finally {
      setLoading(false);
    }
  };

  // Helper to slugify university name in real-time
  const handleNameChange = (val) => {
    setNewUniName(val);
    const slug = val
      .toLowerCase()
      .replace(' online', '')
      .replace(/'/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '')
      .trim();
    setNewUniSlug(slug);
  };

  // Load Tree when a workspace is selected
  useEffect(() => {
    if (selectedSlug) {
      loadTree(selectedSlug);
    } else {
      setTreeData(null);
    }
  }, [selectedSlug]);

  const loadTree = async (slug) => {
    setTreeLoading(true);
    setCompileResult(null);
    try {
      const data = await getWorkspaceTree(slug);
      setTreeData(data);
    } catch (err) {
      console.warn('Failed to load workspace tree', err);
      setTreeData(null);
    } finally {
      setTreeLoading(false);
    }
  };

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    if (!newUniSlug) return;

    setError('');
    setCreating(true);
    try {
      // Call backend: creates metadata.json + 3 system listing pages
      await createWorkspace(newUniSlug, newUniName || newUniSlug);
    } catch (err) {
      console.warn('Backend workspace init failed (may already exist):', err?.response?.data?.error || err.message);
    } finally {
      setCreating(false);
    }

    const newWorkspace = {
      slug: newUniSlug,
      name: newUniName || newUniSlug.replace(/-/g, ' ').toUpperCase(),
      is_new: true
    };

    updateSession({
      workspace: newWorkspace,
      university_slug: newUniSlug
    });
    setSelectedSlug(newUniSlug);
    setNewUniName('');
    setNewUniSlug('');
    
    // Refresh workspace list from server
    await fetchWorkspaces();
  };

  const handleSelectWorkspace = (slug, name) => {
    setSelectedSlug(slug);
    updateSession({
      workspace: {
        slug,
        name: name || slug.replace(/-/g, ' ').toUpperCase(),
        is_new: false
      },
      university_slug: slug
    });
  };

  const handleCompile = async () => {
    if (!selectedSlug) return;
    setCompiling(true);
    setCompileResult(null);
    try {
      const res = await compileWorkspace(selectedSlug);
      setCompileResult(res);
      // Reload tree to reflect new files or statuses
      loadTree(selectedSlug);
    } catch (err) {
      console.error(err);
      setError('Compilation failed: ' + (err.response?.data?.error || err.message));
    } finally {
      setCompiling(false);
    }
  };

  return (
    <div>
      <div className="topbar">
        <div className="topbar-left">
          <h1 className="topbar-title">Select University Workspace</h1>
          <p className="topbar-subtitle">
            Choose an existing file-system workspace database, or initialize a new one to store source JSONs and HTML pages.
          </p>
        </div>
      </div>

      {error && (
        <div style={{ background: 'var(--color-error-light)', border: '1px solid var(--color-error)', borderRadius: 'var(--radius-md)', padding: '12px 16px', color: 'var(--color-error)', fontSize: 14, fontWeight: 500, marginBottom: 20 }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24, alignItems: 'start' }}>
        
        {/* Left Side: Selector and Creator */}
        <div>
          {/* Create Workspace Card */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-body" style={{ padding: 24 }}>
              <div style={{ fontSize: 15, fontWeight: 800, color: 'var(--navy)', marginBottom: 12 }}>Create New Workspace</div>
              <form onSubmit={handleCreateWorkspace} style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 240 }}>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#33363f', marginBottom: 6 }}>University Name</label>
                  <input
                    className="input"
                    placeholder="e.g. NMIMS Online"
                    value={newUniName}
                    onChange={(e) => handleNameChange(e.target.value)}
                    style={{ width: '100%', height: 42 }}
                    required
                  />
                </div>
                <div style={{ width: 180 }}>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#33363f', marginBottom: 6 }}>Workspace Slug</label>
                  <input
                    className="input"
                    placeholder="e.g. nmims"
                    value={newUniSlug}
                    readOnly
                    style={{ width: '100%', height: 42, background: '#f1f5f9', cursor: 'not-allowed', color: '#64748b', fontWeight: 600 }}
                  />
                </div>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ height: 42, padding: '0 24px' }}
                  disabled={!newUniSlug || creating}
                >
                  {creating ? 'Creating…' : 'Create & Open'}
                </button>
              </form>
              {newUniSlug && (
                <div style={{ fontSize: 11.5, color: 'var(--color-text-secondary)', marginTop: 8 }}>
                  Folder will be generated at: <code style={{ color: 'var(--color-orange)', fontWeight: 600 }}>backend/workspaces/{newUniSlug}/</code>
                </div>
              )}
            </div>
          </div>

          {/* Select Workspace Card */}
          <div className="card">
            <div className="card-body" style={{ padding: 24 }}>
              <div style={{ fontSize: 15, fontWeight: 800, color: 'var(--navy)', marginBottom: 16 }}>Existing Workspaces</div>
              
              {loading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text-secondary)', padding: '12px 0' }}>
                  <div style={{
                    width: 20, height: 20,
                    border: '2.5px solid var(--color-border)',
                    borderTop: '2.5px solid var(--color-orange)',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite'
                  }} />
                  <span>Loading workspaces...</span>
                </div>
              ) : workspaces.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', border: '1px dashed var(--color-border)', borderRadius: 8, background: '#fcfcfc' }}>
                  <div style={{ fontSize: 32, marginBottom: 12 }}>📁</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--navy)' }}>No Workspace Databases Found</div>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Create your first workspace using the form above.</div>
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 14 }}>
                  {workspaces.map((ws) => {
                    // Support both old string format and new object format
                    const slug = typeof ws === 'string' ? ws : ws.slug;
                    const name = typeof ws === 'string' ? slug.replace(/-/g, ' ').toUpperCase() : (ws.name || slug.replace(/-/g, ' ').toUpperCase());
                    const active = selectedSlug === slug;
                    return (
                      <div
                        key={slug}
                        onClick={() => handleSelectWorkspace(slug, name)}
                        style={{
                          border: active ? '2px solid var(--color-orange)' : '1.5px solid var(--color-border)',
                          borderRadius: 'var(--radius-md)',
                          padding: 16,
                          background: active ? 'var(--color-orange-light)' : '#fff',
                          cursor: 'pointer',
                          boxShadow: active ? 'var(--shadow-md)' : 'var(--shadow-xs)',
                          transition: 'all 0.2s ease',
                          position: 'relative'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <span style={{ fontSize: 24 }}>🏫</span>
                          <div>
                            <div style={{ fontWeight: 700, color: 'var(--navy)', fontSize: 14 }}>
                              {name}
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', fontFamily: 'var(--font-code)', marginTop: 2 }}>
                              {slug}
                            </div>
                          </div>
                        </div>
                        {active && (
                          <div style={{
                            position: 'absolute', top: 12, right: 12,
                            width: 8, height: 8, borderRadius: '50%', background: 'var(--color-orange)'
                          }} />
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Tree / Info Context panel */}
        <div>
          <div className="card" style={{ height: '100%' }}>
            <div className="card-body" style={{ padding: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--navy)', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>👁️</span> Workspace Structure
              </div>

              {!selectedSlug ? (
                <div style={{ color: 'var(--muted)', fontSize: 13, textAlign: 'center', padding: '60px 0' }}>
                  Select or create a workspace to view its contents.
                </div>
              ) : treeLoading ? (
                <div style={{ color: 'var(--color-text-secondary)', fontSize: 13, textAlign: 'center', padding: '60px 0' }}>
                  Scanning workspace...
                </div>
              ) : treeData ? (
                <div>
                  {/* Action row */}
                  <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                    <button
                      onClick={handleCompile}
                      disabled={compiling}
                      className="btn btn-secondary btn-sm"
                      style={{ flex: 1, padding: '8px 12px', fontSize: 12 }}
                    >
                      {compiling ? 'Compiling…' : '⚡ Compile Workspace'}
                    </button>
                  </div>

                  {compileResult && (
                    <div style={{
                      padding: 10, background: compileResult.pages_failed > 0 ? '#fffbeb' : '#f0f9f4',
                      border: `1px solid ${compileResult.pages_failed > 0 ? '#fde68a' : '#b7e4c7'}`,
                      borderRadius: 6, fontSize: 11.5, marginBottom: 14
                    }}>
                      <div style={{ fontWeight: 700, color: compileResult.pages_failed > 0 ? '#92400e' : '#1a6b3c' }}>
                        {compileResult.pages_failed > 0 ? '⚠️ Compiled with errors' : '✓ Compiled Successfully'}
                      </div>
                      <div style={{ marginTop: 2, color: 'var(--color-text-secondary)' }}>
                        Processed {compileResult.pages_compiled} page(s).
                      </div>
                    </div>
                  )}

                  {/* Render tree */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 420, overflowY: 'auto', paddingRight: 4 }}>
                    
                    {/* University Page */}
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 4 }}>
                        University
                      </div>
                      {treeData.university ? (
                        <div style={{ padding: '6px 10px', background: '#f8fafc', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12.5, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span>🏛️ {treeData.university.slug}.html</span>
                          <span style={{ fontSize: 10, color: 'var(--color-success)' }}>✓ Live</span>
                        </div>
                      ) : (
                        <div style={{ fontSize: 12, color: 'var(--muted)', fontStyle: 'italic', paddingLeft: 4 }}>
                          Not generated yet
                        </div>
                      )}
                    </div>

                    {/* Courses */}
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 4 }}>
                        Courses ({treeData.courses?.length || 0})
                      </div>
                      {treeData.courses && treeData.courses.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                          {treeData.courses.map(course => (
                            <div key={course.slug} style={{ padding: '6px 10px', background: '#f8fafc', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}>
                              <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <span>🎓 {course.slug}</span>
                                {course.has_html && <span style={{ fontSize: 9, color: 'var(--color-success)' }}>✓ HTML</span>}
                              </div>
                              
                              {/* Nest specs */}
                              {course.specializations && course.specializations.length > 0 && (
                                <div style={{ borderLeft: '1.5px solid var(--color-border)', marginLeft: 8, paddingLeft: 8, marginTop: 4, display: 'flex', flexDirection: 'column', gap: 4 }}>
                                  {course.specializations.map(spec => (
                                    <div key={spec.slug} style={{ fontSize: 11, color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                      <span>├─ 🔬 {spec.slug.replace(`${selectedSlug}-`, '')}</span>
                                      {spec.has_html && <span style={{ fontSize: 9, color: 'var(--color-success)' }}>✓</span>}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ fontSize: 12, color: 'var(--muted)', fontStyle: 'italic', paddingLeft: 4 }}>
                          No course pages yet
                        </div>
                      )}
                    </div>

                    {/* Blogs */}
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 4 }}>
                        Blogs ({treeData.blogs?.length || 0})
                      </div>
                      {treeData.blogs && treeData.blogs.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          {treeData.blogs.map(blog => (
                            <div key={blog.slug} style={{ padding: '6px 10px', background: '#f8fafc', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span>✍️ {blog.slug}</span>
                              {blog.has_html && <span style={{ fontSize: 9, color: 'var(--color-success)' }}>✓ HTML</span>}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ fontSize: 12, color: 'var(--muted)', fontStyle: 'italic', paddingLeft: 4 }}>
                          No blog pages yet
                        </div>
                      )}
                    </div>

                    {/* Flat Specializations */}
                    {treeData.specializations && treeData.specializations.length > 0 && (
                      <div>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 4 }}>
                          Specializations ({treeData.specializations.length})
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          {treeData.specializations.map(sp => (
                            <div key={sp.slug} style={{ padding: '6px 10px', background: '#f8fafc', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span>🔬 {sp.slug}{sp.parent_slug ? <span style={{ fontWeight: 400, color: 'var(--muted)', fontSize: 10 }}> ← {sp.parent_slug}</span> : ''}</span>
                              {sp.has_html && <span style={{ fontSize: 9, color: 'var(--color-success)' }}>✓</span>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* System Pages */}
                    {treeData.pages && treeData.pages.length > 0 && (
                      <div>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 4 }}>
                          System Pages (auto-generated)
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          {treeData.pages.map(pg => (
                            <div key={pg.slug} style={{ padding: '6px 10px', background: pg.has_html ? '#f0f9f4' : '#fdf6ef', border: `1px solid ${pg.has_html ? '#b7e4c7' : '#fde68a'}`, borderRadius: 6, fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span>⚡ {pg.page_type.replace('_listing', '')} listing</span>
                              <span style={{ fontSize: 9, color: pg.has_html ? 'var(--color-success)' : '#92400e' }}>{pg.has_html ? '✓ Live' : '⚠ Not compiled'}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  </div>
                </div>
              ) : (
                <div style={{ color: 'var(--muted)', fontSize: 12, textAlign: 'center', padding: '40px 0' }}>
                  Could not load files from workspace.
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* Navigation Footer */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 28, borderTop: '1px solid var(--border-light)', paddingTop: 20 }}>
        <button
          onClick={onNext}
          disabled={!selectedSlug}
          className="btn btn-primary btn-lg"
          style={{
            padding: '12px 32px',
            background: selectedSlug ? 'var(--color-orange)' : '#ccc',
            boxShadow: selectedSlug ? '0 4px 12px rgba(232, 64, 16, 0.2)' : 'none',
          }}
        >
          Continue to Document Upload →
        </button>
      </div>
    </div>
  );
}
