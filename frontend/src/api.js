import axios from 'axios';

const BASE = 'http://localhost:8000';

export async function ingestAcf(payload) {
  const res = await axios.post(`${BASE}/ingest-acf`, payload);
  return res.data;
}

export async function previewHtml(payload) {
  // Returns raw HTML string for iframe srcdoc
  const res = await axios.post(`${BASE}/preview-html`, payload, {
    responseType: 'text',
  });
  return res.data;
}

export async function renderHtml(payload) {
  const res = await axios.post(`${BASE}/render-html`, payload, {
    responseType: 'blob',
  });
  return res.data;
}

export async function parseDocx(file, pageType) {
  const formData = new FormData();
  formData.append('file', file);
  if (pageType && pageType !== 'auto') {
    formData.append('page_type', pageType);
  }

  const endpoint = `${BASE}/parse-docx`;

  const res = await axios.post(endpoint, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
}

export async function saveTempJson(data) {
  try {
    const res = await axios.post(`${BASE}/save-temp-json`, { data });
    return res.data;
  } catch (err) {
    console.warn('Failed to save temporary debug JSON:', err);
  }
}

// ── Workspace API ─────────────────────────────────────────────────────────────

/**
 * Save the current page (ACF JSON + images) into the university workspace.
 * The backend determines the folder path from page_type + slug.
 * @param {object} acf_data  - Full ACF JSON (includes slug, page_type, university_slug, parent_slug)
 * @param {object} images    - Image URL map { hero_image_url: '...', ... }
 * @param {object} metadataOverrides - Optional university-level metadata overrides
 */
export async function saveToWorkspace(acf_data, images = {}, metadataOverrides = null) {
  const payload = { acf_data, images };
  if (metadataOverrides) payload.metadata_overrides = metadataOverrides;
  const res = await axios.post(`${BASE}/save-to-workspace`, payload);
  return res.data;
}

/**
 * Trigger a full two-pass compilation of the workspace for a university.
 * Returns a summary: { pages_compiled, pages_failed, errors, compiled_at }
 */
export async function compileWorkspace(universitySlug) {
  const formData = new FormData();
  formData.append('university_slug', universitySlug);
  const res = await axios.post(`${BASE}/compile-workspace`, formData);
  return res.data;
}

/**
 * Fetch the workspace folder tree for a university.
 * Returns nested structure: { university, courses: [{..., specializations}], blogs }
 */
export async function getWorkspaceTree(universitySlug) {
  const res = await axios.get(`${BASE}/workspace-tree`, {
    params: { university_slug: universitySlug },
  });
  return res.data;
}

/**
 * Delete a page from the university workspace.
 */
export async function deletePage(universitySlug, pageType, slug, parentSlug = null) {
  const res = await axios.delete(`${BASE}/delete-page`, {
    params: {
      university_slug: universitySlug,
      page_type: pageType,
      slug,
      parent_slug: parentSlug,
    },
  });
  return res.data;
}

/**
 * Delete a workspace from the backend disk.
 */
export async function deleteWorkspace(universitySlug) {
  const res = await axios.delete(`${BASE}/workspaces/${universitySlug}`);
  return res.data;
}

/**
 * Return all university workspaces that have workspaces on disk.
 * Each item: { slug, name, lead_url, last_compiled_at, created_at }
 */
export async function listWorkspaces() {
  const res = await axios.get(`${BASE}/workspaces`);
  return res.data;
}

/**
 * Create a new university workspace on disk and initialise the 3 system
 * listing pages (Programs, Specializations, Blog).
 * @param {string} universitySlug  - URL-safe slug, e.g. "nmims"
 * @param {string} universityName  - Human-readable name, e.g. "NMIMS Online"
 * @param {object} metadataOverrides - Optional extra metadata fields
 */
export async function createWorkspace(universitySlug, universityName = null, metadataOverrides = null) {
  const payload = { university_slug: universitySlug };
  if (universityName) payload.university_name = universityName;
  if (metadataOverrides) payload.metadata_overrides = metadataOverrides;
  const res = await axios.post(`${BASE}/workspaces`, payload);
  return res.data;
}

// ── Website Builder API (Pass 4 — deployable static export) ───────────────────

/**
 * Build a deployable static website package for a workspace.
 * Runs a full compile first (Pass 1–3), then exports to workspaces/<uni>/build/.
 * Returns a summary: { pages_compiled, pages_failed, images_copied,
 *                      downloads_copied, routes_generated, build_path,
 *                      build_url, routes, errors, built_at }
 */
export async function buildWebsite(universitySlug, { skipCompile = false } = {}) {
  const formData = new FormData();
  formData.append('university_slug', universitySlug);
  if (skipCompile) formData.append('skip_compile', 'true');
  const res = await axios.post(`${BASE}/build-website`, formData);
  return res.data;
}

/**
 * Check whether a build exists for a workspace (without rebuilding).
 * Returns { exists, build_path, build_url, routes, routes_count,
 *           pages_compiled, images_copied, built_at }
 */
export async function getBuildStatus(universitySlug) {
  const res = await axios.get(`${BASE}/build-status`, {
    params: { university_slug: universitySlug },
  });
  return res.data;
}

/**
 * Trigger a browser download of the entire build/ folder as a ZIP.
 */
export function downloadBuild(universitySlug) {
  // Direct navigation lets the browser handle the ZIP attachment download.
  window.location.href = `${BASE}/download-build?university_slug=${encodeURIComponent(universitySlug)}`;
}

/**
 * Absolute URL to a file inside the build/ folder (for iframe/new-tab preview).
 */
export function buildFileUrl(universitySlug, path = 'index.html') {
  return `${BASE}/build-file?university_slug=${encodeURIComponent(universitySlug)}&path=${encodeURIComponent(path)}`;
}

// ── Hybrid Parent Mapping API ─────────────────────────────────────────────────

/**
 * Detect the best-matching parent course for a specialization.
 * Returns { detected_parent_slug, confidence, available_courses }
 */
export async function detectParent(specSlug, universitySlug, currentParentSlug = null) {
  const payload = { spec_slug: specSlug, university_slug: universitySlug };
  if (currentParentSlug) payload.current_parent_slug = currentParentSlug;
  const res = await axios.post(`${BASE}/detect-parent`, payload);
  return res.data;
}

/**
 * Update the parent_slug of an already-saved specialization in the workspace.
 * Returns { status, spec_slug, old_parent_slug, new_parent_slug }
 */
export async function remapParent(universitySlug, specSlug, newParentSlug) {
  const res = await axios.post(`${BASE}/remap-parent`, {
    university_slug: universitySlug,
    spec_slug: specSlug,
    new_parent_slug: newParentSlug,
  });
  return res.data;
}

export async function generateSpecializationStub(universitySlug, specName, parentCourseSlug) {
  const res = await axios.post(`${BASE}/generate-specialization-stub`, {
    university_slug: universitySlug,
    spec_name: specName,
    parent_course_slug: parentCourseSlug,
  });
  return res.data;
}

/**
 * Upload university logo and/or favicon.
 */
export async function uploadBranding(universitySlug, logoFile, faviconFile) {
  const formData = new FormData();
  if (logoFile) formData.append('logo', logoFile);
  if (faviconFile) formData.append('favicon', faviconFile);
  const res = await axios.post(`${BASE}/workspaces/${universitySlug}/branding`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
}

/**
 * Retrieve source.json for a specific page.
 */
export async function getWorkspacePage(universitySlug, pageType, slug, parentSlug = null) {
  let url = `${BASE}/workspaces/${universitySlug}/pages/${pageType}/${slug}`;
  if (parentSlug) url += `?parent_slug=${parentSlug}`;
  const res = await axios.get(url);
  return res.data;
}

