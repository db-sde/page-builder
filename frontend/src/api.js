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
