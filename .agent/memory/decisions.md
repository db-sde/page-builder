# memory/decisions.md — Architecture Decision Records

Each record follows the format: Problem → Decision → Reason → Trade-offs → Files → Date.

---

## ADR-001: Flat Specialization Storage

**Problem:** Specializations could be nested inside their parent course directories,
or stored flat at the top workspace level.

**Decision:** Specializations are stored flat at `workspaces/<uni>/Specializations/<slug>/`,
regardless of which course they belong to. The parent relationship is expressed only via
`parent_slug` in `source.json`.

**Reason:** Avoids the need to move files on disk when a parent assignment changes.
Simplifies path resolution (`resolve_page_dir` returns a single flat path for all specs).
The compiler resolves parent-child relationships at compile time via the index.

**Trade-offs:** A slug collision between two specializations of different courses is
theoretically possible (though slug generation includes the university prefix, reducing risk).

**Affected files:**
- `backend/workspace/manager.py` (`resolve_page_dir`)
- `backend/workspace/compiler.py` (`_build_workspace_spec_list`, `_enrich_resolved`)
- `backend/workspace/builder.py` (route map)

**Date:** Established before git history window (pre-first-commit convention).

---

## ADR-002: Decoupled Lead Capture App

**Problem:** Lead capture forms could be embedded in each static page, requiring
per-page form logic and CRM integration in every compiled HTML file.

**Decision:** All CTA buttons link to a separate, centrally hosted React app (`contact/`),
deployed to Vercel. The app receives context via a URL-safe Base64-encoded JSON payload.

**Reason:** Eliminates CRM API keys from static HTML files. Allows the lead form UI to be
updated independently of any page recompile. Centralises validation and webhook logic in
one place. Enables referrer-based back navigation without passing full URLs in query strings.

**Trade-offs:** Requires the contact app to be deployed and healthy for leads to work.
A down contact app breaks all CTAs across all university sites.

**Affected files:**
- `backend/workspace/builder.py` (CTA URL generation)
- `backend/renderer/engine.py` (LEAD_BASE_URL injection into templates)
- `contact/src/App.jsx` (form logic)
- `contact/src/utils/payload.js` (Base64 decoder)
- `contact/src/services/webhook.js` (Supabase submission)

**Date:** Established based on git commit `2f5f807` ("feat: webhook issue resolving in contact").

---

## ADR-003: Two-Pass Workspace Compiler

**Problem:** Rendering a specialization page requires knowing its parent course's data.
Rendering a course page requires knowing which specializations belong to it. This is a
circular dependency if pages are rendered on upload.

**Decision:** A two-pass compiler. Pass 1 indexes all `source.json` files into memory.
Pass 2 re-renders every page with the full index available, injecting parent/sibling/
workspace relationships.

**Reason:** Separates indexing from rendering. Any page can be uploaded in any order.
Relationships are resolved at compile time, not at upload time.

**Trade-offs:** Every compile re-renders all pages, even unchanged ones. Expensive for
large workspaces. (A caching TODO exists in `engine.py`.)

**Affected files:**
- `backend/workspace/compiler.py`
- `backend/renderer/engine.py`

**Date:** Established based on codebase structure; refined in commit `5b65cd0`.

---

## ADR-004: University Knowledge Base

**Problem:** Every DOCX for a university (courses, specializations, blogs) contains the
same NAAC grade, UGC status, established year, and contact info. If each page stores
its own copy, updating a shared fact requires re-uploading every DOCX.

**Decision:** A `university_knowledge.json` file per workspace stores shared fields.
`BaseTransformer.resolve()` uses a three-level chain: Page data → Knowledge file → System default.

**Reason:** Allows a course page uploaded without NAAC grade to still display the correct
grade if it was captured from the university page or any earlier page.

**Trade-offs:** Conflict detection is needed when two pages provide different values for the
same field. Conflicts are logged in `university_knowledge.json["conflicts"]` but not
automatically resolved — requires human review.

**Affected files:**
- `backend/workspace/knowledge.py`
- `backend/transformers/base.py` (`resolve`, `resolve_list`)

**Date:** Established in commit `62f23c9` ("feat: implement dynamic field resolution and knowledge-based context injection").

---

## ADR-005: Canonical Utility Functions in core/utils.py

**Problem:** `format_fee()` was duplicated verbatim in `renderer/engine.py` and
`transformers/base.py`. `read_parent_course_data()` was duplicated in three places
in `main.py` and `ingestion/ingest.py`.

**Decision:** All shared utilities live in `core/utils.py`. Duplicates were removed.
Every caller imports from `core.utils`.

**Reason:** Single source of truth for formatting and data-access logic. Prevents silent
divergence between copies.

**Trade-offs:** None significant.

**Affected files:**
- `backend/core/utils.py`
- `backend/renderer/engine.py`
- `backend/transformers/base.py`

**Date:** Commit `532b518` ("refactor: consolidate shared utilities for fee formatting, course data retrieval, and tenant-specific site configurations").

---

## ADR-006: Generic Site Config for Multi-Tenancy

**Problem:** The original `SITE_CONFIG` dict in `core/site_config.py` contained NMIMS's
real contact details (WhatsApp, email, address). Every other university workspace was
inheriting NMIMS's contact information because they all called the same config.

**Decision:** `get_site_config()` returns `SITE_CONFIG` only for `university_slug == "nmims"`.
All other workspaces get `_generic_site_config()` (blank contact fields), with optional
overrides loaded from `metadata.json`'s `contact` section.

**Reason:** Prevents NMIMS's personal contact details leaking into other university sites.

**Trade-offs:** Each new workspace must populate `metadata.json["contact"]` to have real
contact info in its pages.

**Affected files:**
- `backend/core/site_config.py`

**Date:** Commit `532b518`.

---

## ADR-007: Backend-Owned Post-Parser Field Contract

**Problem:** Parsed fields had no shared ownership/completeness contract. The editor had
an incomplete UI-specific required-field list, while renderer fallbacks implicitly decided
what missing content meant.

**Decision:** `backend/core/field_definitions.py` is the single canonical ownership map for
University, Course, and Specialization fields. After metadata extraction, APIs generate a
non-mutating `field_state` containing value, source, missing, required, optional, manual,
and derived flags. The React session carries it; it is not persisted into `source.json`.

**Reason:** Field ownership must be known before transformation/rendering, while parser JSON
and current production output must remain unchanged in Phase 1.

**Trade-offs:** The existing `frontend/src/fieldSchema.js` remains temporarily for current UI
labels and health-display behaviour. A later editor phase may consume `field_state` directly.
Renderer fabrication remains unchanged until Phase 2.

**Affected files:**
- `backend/core/field_definitions.py`
- `backend/main.py`
- `frontend/src/App.jsx`
- `frontend/src/api.js`
- `frontend/src/fieldSchema.js`
- `frontend/src/components/Screen0Workspace.jsx`
- `frontend/src/components/Screen1Upload.jsx`
- `frontend/src/components/Screen2Review.jsx`

**Date:** 2026-07-24.
