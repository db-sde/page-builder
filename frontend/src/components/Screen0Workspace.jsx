import { useState, useEffect } from 'react';
import { 
  listWorkspaces, 
  getWorkspaceSettings,
  getWorkspaceTree, 
  createWorkspace, 
  buildWebsite, 
  getBuildStatus, 
  downloadBuild, 
  buildFileUrl, 
  uploadBranding, 
  updateWorkspaceGtm,
  getWorkspacePage, 
  deletePage, 
  deleteWorkspace,
  listDrafts,
  getDraft,
  deleteDraft,
  saveDraft,
  publishDraft,
  API_BASE,
} from '../api';

// Helper for relative timestamps ("Last built 5 mins ago")
function formatRelativeTime(dateString) {
  if (!dateString) return 'Never';
  const date = new Date(dateString);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);
  if (diffSec < 30) return 'Just now';
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} min${diffMin > 1 ? 's' : ''} ago`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour} hr${diffHour > 1 ? 's' : ''} ago`;
  const diffDays = Math.floor(diffHour / 24);
  return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
}

// Clean SVG Icons for VS Code Explorer Style
const ChevronIcon = ({ open }) => (
  <svg 
    width="12" 
    height="12" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2.5" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    style={{ transform: open ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.15s ease', color: '#64748b' }}
  >
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

const FolderIcon = ({ open }) => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: open ? '#3b82f6' : '#64748b' }}>
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
  </svg>
);

const FileIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#94a3b8' }}>
    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
    <polyline points="13 2 13 9 20 9" />
  </svg>
);

function formatPageName(slug, universitySlug = '') {
  return String(slug || '')
    .replace(new RegExp(`^${universitySlug}-`), '')
    .replace(/-/g, ' ')
    .replace(/\b\w/g, letter => letter.toUpperCase());
}

export default function Screen0Workspace({ session, updateSession, onNext, setStep }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [drafts, setDrafts] = useState([]);
  const [draftsLoading, setDraftsLoading] = useState(false);
  const [publishingDraftKey, setPublishingDraftKey] = useState('');
  
  // Selection & Creation
  const [selectedSlug, setSelectedSlug] = useState(session.workspace?.slug || '');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUniName, setNewUniName] = useState('');
  const [newUniSlug, setNewUniSlug] = useState('');
  const [creating, setCreating] = useState(false);
  
  // Workspace Tree View & Search & Filters
  const [treeData, setTreeData] = useState(null);
  const [treeLoading, setTreeLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [expandedFolders, setExpandedFolders] = useState({
    university: false,
    courses: false,
    blogs: false,
    specializations: false,
  });
  const [expandedCourses, setExpandedCourses] = useState({});

  // Hover & Overflow Menu State
  const [activeMenuSlug, setActiveMenuSlug] = useState(null);

  // Build States
  const [building, setBuilding] = useState(false);
  const [buildResult, setBuildResult] = useState(null);
  const [buildError, setBuildError] = useState('');
  const [, setBuildTime] = useState(null);
  const [buildStatusData, setBuildStatusData] = useState(null);

  // Accordions & Modals inside Inspector
  const [brandingOpen, setBrandingOpen] = useState(false);
  const [dangerOpen, setDangerOpen] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [confirmSlugInput, setConfirmSlugInput] = useState('');

  // Branding Upload States
  const [logoFile, setLogoFile] = useState(null);
  const [faviconFile, setFaviconFile] = useState(null);
  const [defaultOgImageFile, setDefaultOgImageFile] = useState(null);
  const [, setLogoPreview] = useState(null);
  const [, setFavPreview] = useState(null);
  const [primaryDomain, setPrimaryDomain] = useState('');
  const [isUnsaved, setIsUnsaved] = useState(false);
  const [brandingUploading, setBrandingUploading] = useState(false);
  const [gtmEnabled, setGtmEnabled] = useState(false);
  const [gtmHead, setGtmHead] = useState('');
  const [gtmBodyStart, setGtmBodyStart] = useState('');
  const [gtmUnsaved, setGtmUnsaved] = useState(false);
  const [gtmSaving, setGtmSaving] = useState(false);

  // Toast Notification System
  const [toasts, setToasts] = useState([]);

  const addToast = (type, title, message) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4500);
  };

  useEffect(() => {
    fetchWorkspaces();
    // The initial fetch intentionally runs once; later refreshes are explicit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchWorkspaces() {
    setLoading(true);
    setError('');
    try {
      const res = await listWorkspaces();
      const list = res.workspaces || [];
      setWorkspaces(list);

      if (!selectedSlug && list.length > 0) {
        const first = list[0];
        const slug = typeof first === 'string' ? first : first.slug;
        const name = typeof first === 'string' ? slug.replace(/-/g, ' ').toUpperCase() : (first.name || slug.replace(/-/g, ' ').toUpperCase());
        handleSelectWorkspace(slug, name);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to fetch workspaces.');
      addToast('error', 'Error', 'Failed to load workspaces.');
    } finally {
      setLoading(false);
    }
  }

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

  useEffect(() => {
    let cancelled = false;
    if (selectedSlug) {
      loadTree(selectedSlug);
      loadBuildStatus(selectedSlug);
      loadDraftList(selectedSlug);
      loadWorkspaceSettings(selectedSlug);
      const activeWorkspace = workspaces.find(w => (typeof w === 'string' ? w : w.slug) === selectedSlug);
      if (activeWorkspace) {
        queueMicrotask(() => {
          if (cancelled) return;
          setPrimaryDomain(activeWorkspace.site?.primary_domain || '');
          setLogoFile(null);
          setFaviconFile(null);
          setDefaultOgImageFile(null);
          setGtmEnabled(Boolean(activeWorkspace.gtm?.enabled));
          setGtmHead(activeWorkspace.gtm?.head || '');
          setGtmBodyStart(activeWorkspace.gtm?.body_start || '');
          setGtmUnsaved(false);
          setLogoPreview(null);
          setFavPreview(null);
          setIsUnsaved(false);
        });
      }
    } else {
      queueMicrotask(() => {
        if (cancelled) return;
        setTreeData(null);
        setBuildResult(null);
        setBuildError('');
        setDrafts([]);
        setPrimaryDomain('');
        setGtmEnabled(false);
        setGtmHead('');
        setGtmBodyStart('');
        setGtmUnsaved(false);
        setIsUnsaved(false);
      });
    }
    return () => { cancelled = true; };
  }, [selectedSlug, workspaces]);

  async function loadTree(slug) {
    setTreeLoading(true);
    try {
      const data = await getWorkspaceTree(slug);
      setTreeData(data);
    } catch (err) {
      console.warn('Failed to load workspace tree', err);
      setTreeData(null);
    } finally {
      setTreeLoading(false);
    }
  }

  async function loadBuildStatus(slug) {
    setBuildResult(null);
    setBuildStatusData(null);
    setBuildError('');
    try {
      const status = await getBuildStatus(slug);
      setBuildStatusData(status);
      if (status && status.exists) {
        setBuildResult({
          university_slug: status.university_slug,
          build_path: status.build_path,
          build_url: status.build_url,
          pages_compiled: status.pages_compiled,
          images_copied: status.images_copied,
          routes_generated: status.routes_count,
          built_at: status.built_at,
          restored: true,
        });
      }
    } catch (err) {
      console.warn('Failed to load build status', err);
      setBuildStatusData({ exists: false });
    }
  }

  async function loadWorkspaceSettings(slug) {
    try {
      const settings = await getWorkspaceSettings(slug);
      setPrimaryDomain(settings.site?.primary_domain || '');
      setGtmEnabled(Boolean(settings.gtm?.enabled));
      setGtmHead(settings.gtm?.head || '');
      setGtmBodyStart(settings.gtm?.body_start || '');
      setGtmUnsaved(false);
    } catch (err) {
      console.warn('Failed to load workspace settings', err);
    }
  }

  async function loadDraftList(slug) {
    setDraftsLoading(true);
    try {
      const result = await listDrafts(slug);
      setDrafts(result.drafts || []);
    } catch {
      setDrafts([]);
    } finally {
      setDraftsLoading(false);
    }
  }

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    if (!newUniSlug) return;

    setError('');
    setCreating(true);
    try {
      await createWorkspace(newUniSlug, newUniName || newUniSlug);
      addToast('success', 'Created', `Workspace ${newUniSlug} initialized.`);
    } catch (err) {
      console.warn('Backend workspace init failed:', err?.response?.data?.error || err.message);
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
    setShowCreateModal(false);
    
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

  const handleBuildWebsite = async () => {
    if (!selectedSlug) return;
    setBuilding(true);
    setBuildError('');
    setBuildResult(null);
    setBuildTime(null);
    addToast('info', 'Build Started', 'Compiling workspace templates into HTML...');
    const start = performance.now();
    try {
      const result = await buildWebsite(selectedSlug);
      const end = performance.now();
      const duration = ((end - start) / 1000).toFixed(2);
      setBuildTime(duration);
      if (result.errors && result.errors.length === 0 && result.pages_failed === 0) {
        setBuildResult(result);
        addToast('success', 'Build Complete', `Compiled ${result.pages_compiled} pages in ${duration}s.`);
      } else if (result.build_path) {
        setBuildResult(result);
        addToast('success', 'Build Complete', `Compiled with warnings.`);
      } else {
        const msg = result.error || 'Build failed.';
        setBuildError(msg);
        addToast('error', 'Build Failed', msg);
      }
      loadTree(selectedSlug);
      loadBuildStatus(selectedSlug);
    } catch (err) {
      const msg = err.response?.data?.error || err.message || String(err);
      setBuildError(msg);
      addToast('error', 'Build Failed', msg);
    } finally {
      setBuilding(false);
    }
  };

  const handleBrandingUpload = async (e) => {
    e.preventDefault();
    setBrandingUploading(true);
    try {
      const res = await uploadBranding(selectedSlug, logoFile, faviconFile, primaryDomain, defaultOgImageFile);
      if (res.status === 'success') {
        setIsUnsaved(false);
        setLogoFile(null);
        setFaviconFile(null);
        setDefaultOgImageFile(null);
        addToast('success', 'Settings Saved', 'Branding configuration saved.');
        await fetchWorkspaces();
      }
    } catch (err) {
      addToast('error', 'Save Failed', err.message || 'Failed to save branding.');
    } finally {
      setBrandingUploading(false);
    }
  };

  const handleGtmSave = async (e) => {
    e.preventDefault();
    setGtmSaving(true);
    try {
      await updateWorkspaceGtm(selectedSlug, {
        enabled: gtmEnabled,
        head: gtmHead,
        body_start: gtmBodyStart,
      });
      setGtmUnsaved(false);
      addToast('success', 'GTM Settings Saved', 'Google Tag Manager settings saved for this workspace.');
      await fetchWorkspaces();
    } catch (err) {
      addToast('error', 'Save Failed', err.response?.data?.detail || err.message || 'Failed to save GTM settings.');
    } finally {
      setGtmSaving(false);
    }
  };

  const handleEditPage = async (pageType, slug, parentSlug = null) => {
    try {
      setError('');
      const targetSlug = (pageType === 'university' && (!slug || slug === 'undefined')) ? selectedSlug : (slug || selectedSlug);
      const record = await getWorkspacePage(selectedSlug, pageType, targetSlug, parentSlug);
      const acf_data = record.data || record;
      const data = { ...acf_data };
      delete data.slug;
      delete data.page_type;
      delete data.university_slug;
      delete data.parent_slug;

      await saveDraft({
        ...data,
        slug: record.slug || targetSlug,
        page_type: record.page_type || pageType,
        university_slug: selectedSlug,
        parent_slug: record.parent_slug || parentSlug,
      }, {}, 'edit');

      updateSession({
        workspace: selectedWorkspace,
        university_slug: selectedSlug,
        slug: record.slug || targetSlug,
        page_type: record.page_type || pageType,
        parent_slug: record.parent_slug || parentSlug,
        acf_data: data,
        raw_acf_data: acf_data,
        field_state: record.field_state || {},
        images: {},
        page_action: 'edit'
      });
      setStep(3);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to open page.';
      setError(msg);
      addToast('error', 'Error', msg);
    }
  };

  const handleContinueDraft = async (draftSummary) => {
    try {
      setError('');
      const draft = await getDraft(selectedSlug, draftSummary.page_type, draftSummary.slug);
      updateSession({
        workspace: selectedWorkspace,
        university_slug: selectedSlug,
        slug: draft.slug,
        page_type: draft.page_type,
        parent_slug: draft.parent_slug,
        acf_data: draft.data || {},
        raw_acf_data: draft.data || {},
        field_state: draft.field_state || {},
        images: draft.images || {},
        page_action: draft.identity_mode || 'import',
      });
      setStep(3);
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Could not open this draft.';
      addToast('error', 'Draft unavailable', message);
    }
  };

  const handleDeleteDraft = async (draftSummary) => {
    if (!window.confirm(`Delete the draft “${draftSummary.title}”?`)) return;
    try {
      await deleteDraft(selectedSlug, draftSummary.page_type, draftSummary.slug);
      setDrafts(current => current.filter(draft => draft.slug !== draftSummary.slug || draft.page_type !== draftSummary.page_type));
      addToast('success', 'Draft deleted', 'The draft was removed.');
    } catch (err) {
      addToast('error', 'Delete failed', err.message || 'Could not delete the draft.');
    }
  };

  const handlePublishDraft = async (draftSummary) => {
    const key = `${draftSummary.page_type}:${draftSummary.slug}`;
    setPublishingDraftKey(key);
    try {
      const result = await publishDraft(selectedSlug, draftSummary.page_type, draftSummary.slug);
      if (result.status !== 'saved') {
        throw new Error(result.error || 'Could not publish draft.');
      }
      setDrafts(current => current.filter(draft => `${draft.page_type}:${draft.slug}` !== key));
      await Promise.all([loadTree(selectedSlug), loadBuildStatus(selectedSlug)]);
      addToast('success', 'Published', `${draftSummary.title} is now in Pages.`);
    } catch (err) {
      addToast('error', 'Publish failed', err.response?.data?.detail || err.message || 'Could not publish draft.');
    } finally {
      setPublishingDraftKey('');
    }
  };

  const handleDeletePage = async (pageType, slug, parentSlug = null) => {
    setActiveMenuSlug(null);
    if (!window.confirm(`Permanently delete page "${slug}" from disk?`)) return;

    try {
      setTreeLoading(true);
      await deletePage(selectedSlug, pageType, slug, parentSlug);
      addToast('success', 'Page Deleted', `${slug} removed from disk.`);
      const tree = await getWorkspaceTree(selectedSlug);
      setTreeData(tree);
      loadBuildStatus(selectedSlug);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to delete page.';
      addToast('error', 'Delete Failed', msg);
    } finally {
      setTreeLoading(false);
    }
  };

  const handleDeleteWorkspaceConfirm = async () => {
    if (confirmSlugInput !== selectedSlug) {
      addToast('error', 'Mismatch', 'Slug did not match.');
      return;
    }

    try {
      setLoading(true);
      setShowDeleteModal(false);
      await deleteWorkspace(selectedSlug);
      addToast('success', 'Workspace Removed', `Workspace ${selectedSlug} was deleted.`);
      setSelectedSlug('');
      setTreeData(null);
      await fetchWorkspaces();
      updateSession({
        workspace: null,
        university_slug: '',
        slug: '',
        page_type: '',
        parent_slug: null,
        acf_data: null,
        raw_acf_data: null,
        field_state: {},
        images: {}
      });
    } catch (err) {
      addToast('error', 'Delete Failed', err.message || 'Failed to delete workspace.');
    } finally {
      setLoading(false);
      setConfirmSlugInput('');
    }
  };

  const selectedWorkspace = workspaces.find(w => (typeof w === 'string' ? w : w.slug) === selectedSlug);
  
  // Counts & Stats
  const totalCourses = treeData?.courses?.length || 0;
  const totalSpecs = treeData?.specializations?.length || (treeData?.courses?.reduce((acc, c) => acc + (c.specializations?.length || 0), 0) || 0);
  const totalBlogs = treeData?.blogs?.length || 0;
  const hasUni = treeData?.university ? 1 : 0;
  const totalPages = hasUni + totalCourses + totalSpecs + totalBlogs;
  const totalImages = buildStatusData?.images_copied ?? 0;

  // Folder & Course Toggles
  const toggleFolder = (folderKey) => {
    setExpandedFolders(prev => ({ ...prev, [folderKey]: !prev[folderKey] }));
  };

  const toggleCourse = (courseSlug) => {
    setExpandedCourses(prev => ({ ...prev, [courseSlug]: !prev[courseSlug] }));
  };

  // Search & Type Filter Logic
  const q = searchQuery.trim().toLowerCase();
  const matchesSearchAndType = (slug, type) => {
    const textMatch = !q || slug.toLowerCase().includes(q);
    const typeMatch = typeFilter === 'all' || typeFilter === type;
    return textMatch && typeMatch;
  };

  const hasCourseMatches = treeData?.courses?.some(c => matchesSearchAndType(c.slug, 'course') || c.specializations?.some(s => matchesSearchAndType(s.slug, 'specialization')));
  const hasBlogMatches = treeData?.blogs?.some(b => matchesSearchAndType(b.slug, 'blog'));
  const hasSpecMatches = treeData?.specializations?.some(s => matchesSearchAndType(s.slug, 'specialization'));
  const hasUniMatch = matchesSearchAndType(treeData?.university?.slug || 'homepage', 'university');
  const hasTotalMatches = hasUniMatch || hasCourseMatches || hasBlogMatches || hasSpecMatches;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, paddingBottom: 40, fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color: '#0f172a' }}>
      
      {/* VS Code Style Explorer Hover Styles */}
      <style>{`
        .tree-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 13px;
          color: #334155;
          cursor: pointer;
          user-select: none;
          transition: background 0.1s ease, color 0.1s ease;
          position: relative;
        }
        .tree-row:hover {
          background: #f1f5f9;
          color: #0f172a;
        }
        .tree-row-actions {
          opacity: 0;
          pointer-events: none;
          display: flex;
          align-items: center;
          gap: 4px;
          transition: opacity 0.12s ease;
        }
        .tree-row:hover .tree-row-actions,
        .tree-row.active-menu .tree-row-actions {
          opacity: 1;
          pointer-events: auto;
        }
        .tree-action-btn {
          font-size: 11px;
          font-weight: 600;
          color: #475569;
          background: #ffffff;
          border: 1px solid #cbd5e1;
          border-radius: 4px;
          padding: 2px 6px;
          cursor: pointer;
        }
        .tree-action-btn:hover {
          background: #e2e8f0;
          color: #0f172a;
        }
      `}</style>

      {/* ── 1. TOP WORKSPACE HEADER ── */}
      <div className="topbar" style={{ marginBottom: 16 }}>
        <div className="topbar-left">
          <h1 className="topbar-title" style={{ fontSize: 22, fontWeight: 800, color: '#0f172a' }}>Select University Workspace</h1>
          <p className="topbar-subtitle" style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
            Choose an existing file-system workspace database, or initialize a new one to store source JSONs and HTML pages.
          </p>
        </div>
      </div>

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 6, padding: '8px 12px', color: '#991b1b', fontSize: 12 }}>
          {error}
        </div>
      )}

      {/* ── 2. WORKSPACE SELECTION & CREATION GRID ── */}
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        
        {/* Existing Workspaces Cards (Main Area) */}
        <div style={{ flex: '1 1 480px', minWidth: 300, background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: 15, fontWeight: 800, color: '#0f172a', marginBottom: 16 }}>Existing Workspaces</div>
          
          {workspaces.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px 20px', border: '1px dashed #cbd5e1', borderRadius: 8, background: '#f8fafc' }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>📁</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#0f172a' }}>No Workspace Databases Found</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>Create your first workspace using the panel on the right.</div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 14 }}>
              {workspaces.map((ws) => {
                const slug = typeof ws === 'string' ? ws : ws.slug;
                const name = typeof ws === 'string' ? slug.replace(/-/g, ' ').toUpperCase() : (ws.name || slug.replace(/-/g, ' ').toUpperCase());
                const logo = typeof ws === 'object' && ws?.branding?.logo ? ws.branding.logo : null;
                const active = selectedSlug === slug;
                return (
                  <div
                    key={slug}
                    onClick={() => handleSelectWorkspace(slug, name)}
                    style={{
                      border: active ? '2px solid #F45D22' : '1.5px solid #e2e8f0',
                      borderRadius: 8,
                      padding: 14,
                      background: active ? '#FFF3E8' : '#ffffff',
                      cursor: 'pointer',
                      boxShadow: active ? '0 4px 12px rgba(244, 93, 34, 0.12)' : '0 1px 2px rgba(0,0,0,0.04)',
                      transition: 'all 0.15s ease',
                      position: 'relative'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      {logo ? (
                        <img 
                          src={`${API_BASE}${logo}`} 
                          alt={name} 
                          style={{ width: 36, height: 36, objectFit: 'contain', borderRadius: 6, background: '#fff', border: '1px solid #e2e8f0', padding: 2 }} 
                        />
                      ) : (
                        <span style={{ fontSize: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', width: 36, height: 36, background: '#f1f5f9', borderRadius: 6 }}>🏫</span>
                      )}
                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div style={{ fontWeight: 700, color: '#0f172a', fontSize: 13.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {name}
                        </div>
                        <div style={{ fontSize: 11, color: '#64748b', fontFamily: 'monospace', marginTop: 2 }}>
                          {slug}
                        </div>
                      </div>
                    </div>
                    {active && (
                      <div style={{
                        position: 'absolute', top: 10, right: 10,
                        width: 8, height: 8, borderRadius: '50%', background: '#F45D22'
                      }} />
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Create Workspace Sticky Right Box */}
        <div style={{ flex: '0 0 320px', minWidth: 280, position: 'sticky', top: 16, background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: 15, fontWeight: 800, color: '#0f172a', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>✨</span> Create New Workspace
          </div>
          <form onSubmit={handleCreateWorkspace} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#334155', marginBottom: 6 }}>University Name</label>
              <input
                className="input"
                placeholder="e.g. NMIMS Online"
                value={newUniName}
                onChange={(e) => handleNameChange(e.target.value)}
                style={{ width: '100%', height: 38, fontSize: 13, padding: '0 10px', border: '1px solid #cbd5e1', borderRadius: 6 }}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#334155', marginBottom: 6 }}>Workspace Slug</label>
              <input
                className="input"
                placeholder="e.g. nmims"
                value={newUniSlug}
                readOnly
                style={{ width: '100%', height: 38, fontSize: 13, padding: '0 10px', background: '#f1f5f9', cursor: 'not-allowed', color: '#64748b', fontWeight: 600, border: '1px solid #cbd5e1', borderRadius: 6 }}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ height: 38, width: '100%', marginTop: 4, justifyContent: 'center', background: '#F45D22', color: '#fff', border: 'none', borderRadius: 6, fontWeight: 700, cursor: !newUniSlug || creating ? 'not-allowed' : 'pointer' }}
              disabled={!newUniSlug || creating}
            >
              {creating ? 'Creating…' : 'Create & Open'}
            </button>
          </form>
        </div>

      </div>

      {/* ── 2. MINIMALIST WORKSPACE TOOLBAR ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        {/* Build Website (Primary Action) */}
        <button
          onClick={handleBuildWebsite}
          disabled={building || !selectedSlug}
          style={{
            height: 34,
            padding: '0 16px',
            fontSize: 12.5,
            fontWeight: 700,
            color: '#ffffff',
            background: building ? '#94a3b8' : '#F45D22',
            border: 'none',
            borderRadius: 6,
            cursor: (building || !selectedSlug) ? 'not-allowed' : 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6
          }}
        >
          <span>🚀</span>
          <span>{building ? 'Building…' : 'Build Website'}</span>
        </button>

        {/* Upload (Secondary Highlighted Action) */}
        <button
          onClick={onNext}
          disabled={!selectedSlug}
          style={{
            height: 34,
            padding: '0 14px',
            fontSize: 12.5,
            fontWeight: 600,
            color: '#F45D22',
            background: '#FFF3E8',
            border: 'none',
            borderRadius: 6,
            cursor: selectedSlug ? 'pointer' : 'not-allowed',
            opacity: selectedSlug ? 1 : 0.5
          }}
        >
          Create Page
        </button>

        {/* Preview (Ghost Button) */}
        <button
          onClick={() => {
            if (buildResult) window.open(buildFileUrl(selectedSlug, 'index.html'), '_blank');
          }}
          disabled={!buildResult || building}
          style={{
            height: 34,
            padding: '0 14px',
            fontSize: 12.5,
            fontWeight: 500,
            color: buildResult ? '#334155' : '#94a3b8',
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: 6,
            cursor: (buildResult && !building) ? 'pointer' : 'not-allowed',
            opacity: (buildResult && !building) ? 1 : 0.5
          }}
        >
          Preview Site ↗
        </button>

        {/* Download (Ghost Button) */}
        <button
          onClick={() => {
            if (buildResult) downloadBuild(selectedSlug);
          }}
          disabled={!buildResult || building}
          style={{
            height: 34,
            padding: '0 14px',
            fontSize: 12.5,
            fontWeight: 500,
            color: buildResult ? '#334155' : '#94a3b8',
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: 6,
            cursor: (buildResult && !building) ? 'pointer' : 'not-allowed',
            opacity: (buildResult && !building) ? 1 : 0.5
          }}
        >
          Download ZIP
        </button>
      </div>

      {(draftsLoading || drafts.length > 0) && (
        <section style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: drafts.length ? 12 : 0 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 800, color: '#0f172a' }}>Drafts</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>Continue where you left off. Changes are saved automatically.</div>
            </div>
            {draftsLoading && <span style={{ fontSize: 12, color: '#64748b' }}>Loading…</span>}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 10 }}>
            {drafts.map(draft => (
              <article key={`${draft.page_type}:${draft.slug}`} style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: 12, background: '#f8fafc' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 800, color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{draft.title}</div>
                    <div style={{ fontSize: 11, fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '.05em', marginTop: 4 }}>{draft.page_type}</div>
                  </div>
                  <button type="button" onClick={() => handleDeleteDraft(draft)} aria-label={`Delete ${draft.title} draft`} style={{ border: 'none', background: 'none', color: '#94a3b8', fontSize: 15, padding: 2 }}>×</button>
                </div>
                <div style={{ marginTop: 10, fontSize: 12, fontWeight: 800, color: draft.status_label === 'Ready to Publish' ? '#166534' : '#92400e' }}>
                  {draft.status_label || 'Draft'}
                </div>
                <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 5 }}>Updated {formatRelativeTime(draft.updated_at)}</div>
                {draft.missing_items?.length > 0 && (
                  <div style={{ fontSize: 11.5, color: '#b45309', marginTop: 8 }}>
                    <strong>Needs:</strong>
                    {draft.missing_items.map(item => (
                      <div key={item}>• {item === 'hero_image_url' ? 'Hero Image' : item.replace(/_/g, ' ')}</div>
                    ))}
                  </div>
                )}
                <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                  <button type="button" onClick={() => handleContinueDraft(draft)} style={{ flex: 1, height: 31, border: 'none', borderRadius: 6, background: '#0f172a', color: '#fff', fontSize: 12, fontWeight: 700 }}>
                    Continue Editing
                  </button>
                  {draft.status_label === 'Ready to Publish' && (
                    <button
                      type="button"
                      onClick={() => handlePublishDraft(draft)}
                      disabled={publishingDraftKey === `${draft.page_type}:${draft.slug}`}
                      style={{ height: 31, border: 'none', borderRadius: 6, background: '#166534', color: '#fff', fontSize: 12, fontWeight: 700, padding: '0 10px' }}
                    >
                      {publishingDraftKey === `${draft.page_type}:${draft.slug}` ? 'Publishing…' : 'Publish'}
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* ── 3. MAIN WORKSPACE GRID (70% Explorer Panel / 30% Inspector Sidebar Panel) ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '7fr 3fr', gap: 20, alignItems: 'start', marginTop: 4 }}>
        
        {/* LEFT PANEL (70%): EXPLORER PANEL CONTAINER */}
        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: 12,
          padding: 16,
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.03)',
          display: 'flex',
          flexDirection: 'column',
          gap: 12
        }}>
          
          {/* Explorer Header: Title + Search & Filters */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, paddingBottom: 10, borderBottom: '1px solid #f1f5f9' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 800, color: '#0f172a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Pages
              </span>
              <span style={{ fontSize: 11, fontWeight: 600, color: '#64748b', background: '#f1f5f9', padding: '1px 6px', borderRadius: 4 }}>
                {totalPages} pages
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="text"
                placeholder="Filter pages…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: 180,
                  height: 28,
                  padding: '0 8px',
                  fontSize: 12,
                  color: '#0f172a',
                  background: '#f8fafc',
                  border: '1px solid #cbd5e1',
                  borderRadius: 6,
                  outline: 'none'
                }}
              />

              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                style={{ height: 28, padding: '0 6px', fontSize: 11.5, color: '#475569', background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: 6, cursor: 'pointer' }}
              >
                <option value="all">All Types</option>
                <option value="university">University</option>
                <option value="course">Courses</option>
                <option value="specialization">Specializations</option>
                <option value="blog">Blogs</option>
              </select>
            </div>
          </div>

          {/* VS Code Explorer Folder Tree (Independently Scrollable) */}
          <div style={{ maxHeight: 580, overflowY: 'auto', paddingRight: 4 }}>
            {treeLoading ? (
              <div style={{ color: '#64748b', fontSize: 12.5, padding: '24px 0', textAlign: 'center' }}>
                Loading pages...
              </div>
            ) : treeData ? (
              !hasTotalMatches ? (
                <div style={{ padding: '24px 12px', textAlign: 'center', color: '#64748b', fontSize: 12.5 }}>
                  No pages match "{searchQuery}"
                  <button 
                    onClick={() => { setSearchQuery(''); setTypeFilter('all'); }}
                    style={{ display: 'block', margin: '8px auto 0 auto', fontSize: 11.5, color: '#F45D22', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}
                  >
                    Clear Filter
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  
                  {/* ── 1. UNIVERSITY SECTION ── */}
                  <div>
                    <div 
                      onClick={() => toggleFolder('university')}
                      className="tree-row"
                      style={{ fontWeight: 700, color: '#0f172a' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <ChevronIcon open={expandedFolders.university} />
                        <FolderIcon open={expandedFolders.university} />
                        <span>University</span>
                      </div>
                    </div>

                    {expandedFolders.university && hasUniMatch && (
                      <div style={{ paddingLeft: 20 }}>
                        <div 
                          onClick={() => handleEditPage('university', treeData.university?.slug || selectedSlug)}
                          className={`tree-row ${activeMenuSlug === 'uni' ? 'active-menu' : ''}`}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
                            <FileIcon />
                            <span>University Homepage</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* ── 2. COURSES SECTION (VS Code Tree with nested Specializations) ── */}
                  <div>
                    <div 
                      onClick={() => toggleFolder('courses')}
                      className="tree-row"
                      style={{ fontWeight: 700, color: '#0f172a' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <ChevronIcon open={expandedFolders.courses} />
                        <FolderIcon open={expandedFolders.courses} />
                        <span>Courses ({treeData.courses?.length || 0})</span>
                      </div>
                    </div>

                    {expandedFolders.courses && (
                      <div style={{ paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {treeData.courses && treeData.courses.length > 0 ? (
                          treeData.courses.filter(c => matchesSearchAndType(c.slug, 'course') || c.specializations?.some(s => matchesSearchAndType(s.slug, 'specialization'))).map(course => {
                            const isCourseExpanded = Boolean(expandedCourses[course.slug]);
                            return (
                              <div key={course.slug}>
                                {/* Course Folder Row */}
                                <div className={`tree-row ${activeMenuSlug === course.slug ? 'active-menu' : ''}`}>
                                  <div 
                                    onClick={() => toggleCourse(course.slug)}
                                    style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}
                                  >
                                    <ChevronIcon open={isCourseExpanded} />
                                    <FolderIcon open={isCourseExpanded} />
                                    <span style={{ fontWeight: 600, color: '#0f172a' }}>{formatPageName(course.slug, selectedSlug)}</span>
                                  </div>

                                  <div className="tree-row-actions" onClick={(e) => e.stopPropagation()}>
                                    <button 
                                      onClick={(e) => { e.stopPropagation(); handleDeletePage('course', course.slug); }} 
                                      className="tree-action-btn"
                                      title="Delete Course folder and all contents from disk"
                                      style={{ color: '#dc2626' }}
                                    >
                                      Delete
                                    </button>
                                  </div>
                                </div>

                                {/* Nested Specializations Under Course */}
                                {isCourseExpanded && (
                                  <div style={{ paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    {/* Main Course Overview Page */}
                                    <div 
                                      onClick={() => handleEditPage('course', course.slug)}
                                      className="tree-row"
                                    >
                                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
                                        <FileIcon />
                                        <span style={{ color: '#64748b' }}>Course Overview</span>
                                      </div>

                                      <div className="tree-row-actions" onClick={(e) => e.stopPropagation()}>
                                        <button 
                                          onClick={(e) => { e.stopPropagation(); handleDeletePage('course', course.slug); }} 
                                          className="tree-action-btn"
                                          title="Delete Course from disk"
                                          style={{ color: '#dc2626' }}
                                        >
                                          Delete
                                        </button>
                                      </div>
                                    </div>

                                    {/* Specialization Pages */}
                                    {course.specializations && course.specializations.filter(sp => matchesSearchAndType(sp.slug, 'specialization')).map(spec => (
                                      <div 
                                        key={spec.slug} 
                                        onClick={() => handleEditPage('specialization', spec.slug, course.slug)}
                                        className={`tree-row ${activeMenuSlug === spec.slug ? 'active-menu' : ''}`}
                                      >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
                                          <FileIcon />
                                          <span style={{ color: '#334155' }}>{formatPageName(spec.slug, selectedSlug)}</span>
                                        </div>

                                        <div className="tree-row-actions" onClick={(e) => e.stopPropagation()}>
                                          <button 
                                            onClick={(e) => { e.stopPropagation(); handleDeletePage('specialization', spec.slug, course.slug); }} 
                                            className="tree-action-btn"
                                            title="Delete Specialization from disk"
                                            style={{ color: '#dc2626' }}
                                          >
                                            Delete
                                          </button>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            );
                          })
                        ) : (
                          <div style={{ fontSize: 12, color: '#94a3b8', fontStyle: 'italic', padding: '2px 6px' }}>No courses ingested</div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* ── 3. BLOGS SECTION ── */}
                  <div>
                    <div 
                      onClick={() => toggleFolder('blogs')}
                      className="tree-row"
                      style={{ fontWeight: 700, color: '#0f172a' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <ChevronIcon open={expandedFolders.blogs} />
                        <FolderIcon open={expandedFolders.blogs} />
                        <span>Blogs ({treeData.blogs?.length || 0})</span>
                      </div>
                    </div>

                    {expandedFolders.blogs && (
                      <div style={{ paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {treeData.blogs && treeData.blogs.length > 0 ? (
                          treeData.blogs.filter(b => matchesSearchAndType(b.slug, 'blog')).map(blog => (
                            <div 
                              key={blog.slug} 
                              onClick={() => handleEditPage('blog', blog.slug)}
                              className={`tree-row ${activeMenuSlug === blog.slug ? 'active-menu' : ''}`}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
                                <FileIcon />
                                <span style={{ color: '#334155' }}>{formatPageName(blog.slug, selectedSlug)}</span>
                              </div>

                              <div className="tree-row-actions" onClick={(e) => e.stopPropagation()}>
                                <button 
                                  onClick={(e) => { e.stopPropagation(); handleDeletePage('blog', blog.slug); }} 
                                  className="tree-action-btn"
                                  title="Delete Blog from disk"
                                  style={{ color: '#dc2626' }}
                                >
                                  Delete
                                </button>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div style={{ fontSize: 12, color: '#94a3b8', fontStyle: 'italic', padding: '2px 6px' }}>No blogs ingested</div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* ── 4. STANDALONE SPECIALIZATIONS SECTION ── */}
                  {treeData.specializations && treeData.specializations.length > 0 && (
                    <div>
                      <div 
                        onClick={() => toggleFolder('specializations')}
                        className="tree-row"
                        style={{ fontWeight: 700, color: '#0f172a' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <ChevronIcon open={expandedFolders.specializations} />
                          <FolderIcon open={expandedFolders.specializations} />
                          <span>Specializations ({treeData.specializations.length})</span>
                        </div>
                      </div>

                      {expandedFolders.specializations && (
                        <div style={{ paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {treeData.specializations.filter(sp => matchesSearchAndType(sp.slug, 'specialization')).map(sp => (
                            <div 
                              key={sp.slug} 
                              onClick={() => handleEditPage('specialization', sp.slug, sp.parent_slug)}
                              className={`tree-row ${activeMenuSlug === sp.slug ? 'active-menu' : ''}`}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
                                <FileIcon />
                                <span style={{ color: '#334155' }}>{formatPageName(sp.slug, selectedSlug)}</span>
                              </div>
                              <div className="tree-row-actions" onClick={(e) => e.stopPropagation()}>
                                <button 
                                  onClick={(e) => { e.stopPropagation(); handleDeletePage('specialization', sp.slug, sp.parent_slug); }} 
                                  className="tree-action-btn"
                                  title="Delete Specialization from disk"
                                  style={{ color: '#dc2626' }}
                                >
                                  Delete
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                </div>
              )
            ) : (
              <div style={{ color: '#94a3b8', fontSize: 12, padding: '24px 0', textAlign: 'center' }}>
                No workspace data loaded.
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL (30%): STICKY INSPECTOR SIDEBAR PANEL CONTAINER */}
        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: 12,
          padding: 16,
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.03)',
          position: 'sticky',
          top: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 16
        }}>
          
          {/* Build Status Metadata */}
          <div>
            <div style={{ fontSize: 11.5, fontWeight: 800, color: '#0f172a', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>
              Build Status
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12.5, color: '#334155' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Status</span>
                {building ? (
                  <span style={{ fontSize: 11.5, fontWeight: 600, color: '#d97706', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#d97706' }} />
                    Building…
                  </span>
                ) : buildStatusData?.exists ? (
                  <span style={{ fontSize: 11.5, fontWeight: 600, color: '#16a34a', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#16a34a' }} />
                    Ready
                  </span>
                ) : (
                  <span style={{ fontSize: 11.5, color: '#64748b' }}>Not Built</span>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Pages</span>
                <strong>{totalPages}</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Images</span>
                <strong>{totalImages}</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Last Build</span>
                <strong style={{ color: '#0f172a' }}>{formatRelativeTime(buildStatusData?.built_at)}</strong>
              </div>
            </div>

            {buildError && (
              <div style={{ marginTop: 8, padding: 8, background: '#fef2f2', borderRadius: 4, color: '#dc2626', fontSize: 11, fontFamily: 'monospace' }}>
                {buildError}
              </div>
            )}
          </div>

          <div style={{ borderTop: '1px solid #f1f5f9' }} />

          {/* Collapsible Branding & Settings */}
          <div>
            <button
              onClick={() => setBrandingOpen(!brandingOpen)}
              style={{
                width: '100%',
                background: 'none',
                border: 'none',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                fontSize: 11.5,
                fontWeight: 800,
                color: '#0f172a',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}
            >
              <span>Workspace Settings</span>
              <ChevronIcon open={brandingOpen} />
            </button>

            {brandingOpen && (
              <div>
              <form onSubmit={handleBrandingUpload} style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: '#334155', marginBottom: 2 }}>University Logo</label>
                  <input type="file" accept=".svg,.png" onChange={(e) => { setLogoFile(e.target.files?.[0] || null); setIsUnsaved(true); }} style={{ fontSize: 11, width: '100%' }} />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: '#334155', marginBottom: 2 }}>Favicon</label>
                  <input type="file" accept=".ico,.png,.svg" onChange={(e) => { setFaviconFile(e.target.files?.[0] || null); setIsUnsaved(true); }} style={{ fontSize: 11, width: '100%' }} />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: '#334155', marginBottom: 2 }}>Primary Domain</label>
                  <input type="text" value={primaryDomain} onChange={(e) => { setPrimaryDomain(e.target.value); setIsUnsaved(true); }} placeholder="https://nmimsonline.co" style={{ fontSize: 12, width: '100%', padding: '4px 6px', border: '1px solid #cbd5e1', borderRadius: 4 }} />
                </div>

                <button
                  type="submit"
                  disabled={brandingUploading || !isUnsaved}
                  style={{
                    height: 30,
                    fontSize: 11.5,
                    fontWeight: 600,
                    color: '#ffffff',
                    background: isUnsaved ? '#0f172a' : '#94a3b8',
                    border: 'none',
                    borderRadius: 4,
                    cursor: isUnsaved ? 'pointer' : 'not-allowed'
                  }}
                >
                  {brandingUploading ? 'Saving…' : 'Save Settings'}
                </button>
              </form>

              <form onSubmit={handleGtmSave} style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid #f1f5f9', display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontSize: 11.5, fontWeight: 800, color: '#0f172a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Google Tag Manager
                </div>

                <label style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12, color: '#334155', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={gtmEnabled}
                    onChange={(e) => { setGtmEnabled(e.target.checked); setGtmUnsaved(true); }}
                  />
                  Enable GTM for this workspace
                </label>

                <div>
                  <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: '#334155', marginBottom: 4 }}>Head Snippet</label>
                  <textarea
                    value={gtmHead}
                    onChange={(e) => { setGtmHead(e.target.value); setGtmUnsaved(true); }}
                    placeholder="Paste the GTM script snippet"
                    rows={6}
                    style={{ fontFamily: 'var(--font-code)', fontSize: 11, width: '100%', resize: 'vertical', padding: '6px', border: '1px solid #cbd5e1', borderRadius: 4 }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: '#334155', marginBottom: 4 }}>Body Start Snippet</label>
                  <textarea
                    value={gtmBodyStart}
                    onChange={(e) => { setGtmBodyStart(e.target.value); setGtmUnsaved(true); }}
                    placeholder="Paste the GTM noscript snippet"
                    rows={6}
                    style={{ fontFamily: 'var(--font-code)', fontSize: 11, width: '100%', resize: 'vertical', padding: '6px', border: '1px solid #cbd5e1', borderRadius: 4 }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={gtmSaving || !gtmUnsaved}
                  style={{ height: 30, fontSize: 11.5, fontWeight: 600, color: '#ffffff', background: gtmUnsaved ? '#0f172a' : '#94a3b8', border: 'none', borderRadius: 4, cursor: gtmUnsaved ? 'pointer' : 'not-allowed' }}
                >
                  {gtmSaving ? 'Saving GTM…' : 'Save GTM Settings'}
                </button>
              </form>
              </div>
            )}
          </div>

          <div style={{ borderTop: '1px solid #f1f5f9' }} />

          {/* Collapsible Danger Zone */}
          <div>
            <button
              onClick={() => setDangerOpen(!dangerOpen)}
              style={{
                width: '100%',
                background: 'none',
                border: 'none',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                fontSize: 11.5,
                fontWeight: 800,
                color: '#dc2626',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}
            >
              <span>Danger Zone</span>
              <ChevronIcon open={dangerOpen} />
            </button>

            {dangerOpen && (
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <p style={{ fontSize: 11.5, color: '#64748b' }}>
                  Permanently delete workspace <strong>{selectedSlug}</strong>.
                </p>
                <button
                  onClick={() => setShowDeleteModal(true)}
                  style={{
                    height: 30,
                    fontSize: 11.5,
                    fontWeight: 600,
                    color: '#ffffff',
                    background: '#dc2626',
                    border: 'none',
                    borderRadius: 4,
                    cursor: 'pointer'
                  }}
                >
                  Delete Workspace
                </button>
              </div>
            )}
          </div>

        </div>
      </div>

      {/* ── CREATE WORKSPACE MODAL ── */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(15, 23, 42, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: 16
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: 8,
            width: '100%',
            maxWidth: 380,
            padding: 18,
            boxShadow: '0 10px 25px rgba(0,0,0,0.1)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: '#0f172a' }}>Add University</h3>
              <button onClick={() => setShowCreateModal(false)} style={{ background: 'none', border: 'none', fontSize: 15, cursor: 'pointer', color: '#64748b' }}>✕</button>
            </div>

            <form onSubmit={handleCreateWorkspace} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div>
                <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: '#334155', marginBottom: 2 }}>University Name</label>
                <input
                  type="text"
                  placeholder="e.g. NMIMS Online"
                  value={newUniName}
                  onChange={(e) => handleNameChange(e.target.value)}
                  style={{ width: '100%', height: 34, padding: '0 8px', fontSize: 12.5, border: '1px solid #cbd5e1', borderRadius: 4 }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 6 }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  style={{ height: 32, padding: '0 12px', fontSize: 12, fontWeight: 600, color: '#475569', background: '#f1f5f9', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newUniSlug || creating}
                  style={{ height: 32, padding: '0 14px', fontSize: 12, fontWeight: 700, color: '#ffffff', background: '#F45D22', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                >
                  {creating ? 'Creating…' : 'Add University'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── 2-STEP DELETE WORKSPACE CONFIRMATION MODAL ── */}
      {showDeleteModal && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(15, 23, 42, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1100,
          padding: 16
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: 8,
            width: '100%',
            maxWidth: 400,
            padding: 18,
            boxShadow: '0 15px 30px rgba(0,0,0,0.15)',
            border: '1px solid #fca5a5'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: '#dc2626' }}>Delete Workspace</h3>
              <button onClick={() => setShowDeleteModal(false)} style={{ background: 'none', border: 'none', fontSize: 15, cursor: 'pointer', color: '#64748b' }}>✕</button>
            </div>

            <p style={{ fontSize: 12, color: '#475569', marginBottom: 10 }}>
              Permanently delete <strong>{selectedSlug}</strong>? Type <code style={{ color: '#dc2626' }}>{selectedSlug}</code> to confirm:
            </p>

            <input
              type="text"
              value={confirmSlugInput}
              onChange={(e) => setConfirmSlugInput(e.target.value)}
              placeholder={selectedSlug}
              style={{ width: '100%', height: 34, padding: '0 8px', fontSize: 12.5, border: '1px solid #cbd5e1', borderRadius: 4, marginBottom: 12 }}
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                style={{ height: 32, padding: '0 12px', fontSize: 12, fontWeight: 600, color: '#475569', background: '#f1f5f9', border: 'none', borderRadius: 4, cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteWorkspaceConfirm}
                disabled={confirmSlugInput !== selectedSlug}
                style={{
                  height: 32,
                  padding: '0 14px',
                  fontSize: 12,
                  fontWeight: 700,
                  color: '#ffffff',
                  background: confirmSlugInput === selectedSlug ? '#dc2626' : '#fca5a5',
                  border: 'none',
                  borderRadius: 4,
                  cursor: confirmSlugInput === selectedSlug ? 'pointer' : 'not-allowed'
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── TOAST NOTIFICATIONS FLOATING CONTAINER ── */}
      <div style={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        zIndex: 2000,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        pointerEvents: 'none'
      }}>
        {toasts.map(t => (
          <div
            key={t.id}
            style={{
              pointerEvents: 'auto',
              minWidth: 240,
              maxWidth: 320,
              padding: '8px 12px',
              background: '#ffffff',
              borderRadius: 6,
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              borderLeft: `3px solid ${t.type === 'success' ? '#10b981' : t.type === 'error' ? '#ef4444' : '#3b82f6'}`,
              display: 'flex',
              alignItems: 'flex-start',
              gap: 8
            }}
          >
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: '#0f172a' }}>{t.title}</div>
              <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 2 }}>{t.message}</div>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
