# memory/regressions.md — Known Regressions & Fixes

Each entry documents a regression that occurred, how it was fixed, and how to avoid it.
This is the most important file for preventing repeated mistakes.

---

## REG-012: Phase 4 Template Mapping Changed V2 Geometry (FIXED 2026-07-27)

**Status:** FIXED. The last visually correct reference is
`3970dc3e56348abf0fb5f82cd39de0ea19c802e1`; commit `5b65cd0` copied those V2 templates and
their CSS into the unified paths byte-for-byte.

**Cause:** Uncommitted Phase 4 template-mapping work added standalone University sections,
made established grids conditionally one-column, removed persistent image/CTA/supporting-text
containers, and allowed missing images to collapse columns. The Phase 1/2 commit `2bfe8a8`
did not touch templates or CSS. Phase 3 commit `97a899b` added data guards and removed fabricated
content but did not change CSS; its correctness fixes were not reverted. Experiment commits
`c0a65aa` and `767454d` are not ancestors of the current `main` branch.

**Fix:** Restored the V2 HTML geometry in `university.html`, `course.html`, and
`specialization.html`; retained dynamic values, empty-data guards, preview-only placeholder text,
and no-fabrication behavior. Parsed University facts reuse the existing Why-us card grid instead
of introducing a new visual section. No CSS or backend pipeline code changed.

**How to avoid:** Treat the V2 markup and CSS as a visual contract. Template data mapping may
replace values and add guards, but must not change wrappers, grid columns, section ordering, or
responsive class hooks without a separately approved design change.

**Verification:** CSS hashes match V2; 35 tests pass; 39 real pages render; IGNOU and NMIMS
compile with zero failures; responsive browser checks show no overflow.

---

## REG-010: Fabricated Fallback Content in Renderer & Templates (FIXED 2026-07-24)

**Status:** FIXED in the Phase 3 pipeline refactor. Discovered in the 2026-07-24
schema-coverage audit. This was the inverse of REG-001: REG-001 fixed *listing* cards,
but the same fabricate-on-empty anti-pattern was alive across the *detail* pages.

**Cause:** `renderer/engine.py::render_resolved` rebuilds most repeater collections and, when the
schema/source value is empty, substitutes hardcoded fabricated content instead of hiding the
section:
- fake named student reviews — `engine.py:866`
- fake job profiles + salaries — `engine.py:836`
- NMIMS recruiter logos as universal fallback — `engine.py:1008`
- full hardcoded MBA syllabus — `engine.py:908` (and syllabus `<section>` has no `{% if %}` guard)
- hardcoded FAQs — `engine.py:895` (also emitted into `FAQPage` JSON-LD)
- 3-row fee table — `engine.py:794`; 7-row other-specs table — `engine.py:965`; demo blog posts — `engine.py:1156`
- features / financing / banks — `engine.py:998,1025,1034`

Transformers add their own fabrications: hardcoded admission steps (`transformers/course.py:41`),
invented accreditation prose (`transformers/course.py:184`), "Most Popular Specialization" badge
(`transformers/specialization.py:87`). Templates hardcode `NIRF #24` / `AIU Member` / `WES Recognised`
(`university.html:84,128`) and a `₹14.2L` spec salary (`specialization.html:115`), and hardcode every
section title (no `*_heading` schema field is consumed).

**Effect:** a page compiled from a sparse-but-valid DOCX still ships fake reviews, salaries,
recruiters, syllabus, FAQs and accreditation claims. Because `engine.py` repopulates the
collections, template `{% if %}` guards are effectively always true. Directly violates R1 and R2.

**Fix:** every empty-collection fallback in `engine.py` was removed, the transformer
fallbacks (admission steps, accreditation prose, "Most Popular" badge, EMI clause) were
removed, the fabricated facts in the templates were removed, and empty sections are now
guarded so they hide in production / show a placeholder in preview. Kept-vs-removed
boundary: `.agent/systems/schema-pipeline.md`.

**How to avoid:** never add an `if not <collection>: <collection> = [...]` fallback in the
renderer or a transformer. Empty means the section is hidden. `backend/tests/
test_no_fabricated_content.py` renders sparse pages of all three types and fails if any of
the removed strings return — extend that list when adding content-bearing fields.

**Still open (product decision, not a regression):** `university.html` renders neither
`facts` nor `accreditations` even though both are parsed and populated, and section titles
still ignore the `*_heading` schema fields. Adding those sections is deliberate product
work — templates decide what is displayed.

**Files involved:** `backend/renderer/engine.py`, `backend/transformers/course.py`,
`backend/transformers/specialization.py`, `backend/templates/university.html`,
`backend/templates/course.html`, `backend/templates/specialization.html`.

---

## REG-011: Workspace Slug Leaks into Fallback Email (FIXED 2026-07-24)

**Status:** FIXED in the Phase 3 refactor — the fallback was deleted; the contact line now
renders only when `site.email` is set. Violated R6.

**Cause:** `templates/specialization.html:429` falls back to
`admissions@{{ university_slug }}online.edu`, placing the internal workspace slug (e.g. `nmims-2`)
into a user-facing email address when `site.email` is unset.

**How to avoid:** never use `university_slug` in rendered UI. Use `metadata.json["contact"].email`
or omit the line. Mirrors REG-007's rule.

**Files involved:** `backend/templates/specialization.html`.

---

## REG-001: Fabricated Blog Cards

**Cause:** A transformer or template was rendering blog listing cards using hardcoded/invented
content when no real blog pages existed in the workspace. The listing page appeared populated
but with fabricated data.

**Fix:** Listing pages now only render cards for entries that exist in the workspace index.
If `_workspace_blogs` is empty, the listing page renders an empty state.

**How to avoid:** Never provide a hardcoded fallback list of items for listing pages.
If the workspace has no blogs, the blog listing must say so — not invent placeholder cards.

**Files involved:**
- `backend/transformers/blog_listing.py`
- `backend/templates/blog_listing.html`
- `backend/workspace/compiler.py` (`_build_workspace_blog_list`)

---

## REG-002: Duplicated UGC Labels

**Cause:** `ugc_status` and `ugc_approved` were treated as separate fields in some
transformers. If both were present, the UGC badge appeared twice in the rendered page.

**Fix:** `core/router.py`'s `normalize_value()` and the knowledge base `FIELD_MAPPING`
in `knowledge.py` now map both `ugc_status` and `ugc_approved` to the same canonical
key (`approvals.ugc_status`). Transformers only read one resolved field.

**How to avoid:** When adding new ACF field aliases, add them only to the `FIELD_MAPPING`
in `knowledge.py` — not as separate fields in the transformer context dict.

**Files involved:**
- `backend/workspace/knowledge.py` (`FIELD_MAPPING`)
- `backend/core/router.py` (`normalize_value`)

---

## REG-003: Hidden Listing Pages

**Cause:** After the workspace directory structure was reorganised, the `Pages/` folder
(which stores system-generated listing pages) was not initialised for new workspaces.
The compiler scanned for listing pages but found nothing, so `programs_listing`,
`specializations_listing`, and `blog_listing` were silently absent from the build.

**Fix:** `workspace/manager.py`'s `init_system_pages()` is called when creating or
opening a workspace. It creates stub `source.json` files for all three listing page types
if they don't already exist.

**How to avoid:** Always call `init_system_pages()` after `ensure_metadata()` when
setting up a new workspace. Never assume listing pages exist without checking.

**Files involved:**
- `backend/workspace/manager.py` (`init_system_pages`)
- `backend/main.py` (workspace creation endpoint)

---

## REG-004: Broken Syllabus Tables

**Cause:** The syllabus section in some DOCX files had merged header rows or all-identical
headers (e.g., "Subject" repeated across all columns). The original table parser assumed
the first row was always a header, causing the table to render with no data rows or
with the actual headers treated as data.

**Fix:** `parser.py`'s `process_table_block()` now:
1. Detects merged title rows (all cells identical) and treats them as a title, not headers.
2. Recovers from all-identical header rows by treating them as the title and promoting
   the second row to headers.
3. Records a `TABLE_HEADER_DETECTION_FAILED` or `TABLE_HEADER_RECOVERED` warning in the block.

**How to avoid:** Run the parser on any new university's DOCX before committing to see if
table warnings appear. Table warnings in the block output mean the rendered table may be
wrong — review in the Preview screen before saving.

**Files involved:**
- `backend/ingestion/parser.py` (`process_table_block`)

---

## REG-005: Placeholder Hero Images in Production

**Cause:** Early builds did not validate image existence. Pages compiled and exported
successfully even when `hero_image_url` pointed to a non-existent file. The template
rendered an empty `<img>` or a broken image in production.

**Fix:** `workspace/builder.py`'s `_validate_pages()` checks every required image field
against the workspace `Assets/images/` directory. If a file is missing, the build returns
a validation error and does not proceed.

**How to avoid:** Always upload images before building. The Review screen's field health
panel flags missing required images. Never skip the build validation step.

**Files involved:**
- `backend/workspace/builder.py` (`_validate_pages`, `_IMAGE_FIELD_BY_TYPE`)

---

## REG-006: NMIMS Contact Info Leaking into Other Workspaces

**Cause:** `core/site_config.py` contained a single `SITE_CONFIG` dict with NMIMS's real
WhatsApp number, email, and address. All tenants called `get_site_config()` and received
this config, so every university site showed NMIMS's contact details.

**Fix:** `get_site_config()` now returns `SITE_CONFIG` only for `university_slug == "nmims"`.
All other workspaces get a blank generic config, with overrides from `metadata.json["contact"]`.

**How to avoid:** Never add university-specific contact details to the shared `SITE_CONFIG`
dict. Put them in the workspace's `metadata.json` under the `contact` key.

**Files involved:**
- `backend/core/site_config.py`

---

## REG-007: Workspace Slug Appearing in Page Titles

**Cause:** When `university_name` was not found in the workspace index, some code paths
fell back to `university_slug.replace("-", " ").title()`. This caused `nmims-2` to appear
as "Nmims 2" in page headings, breadcrumbs, and the admin UI.

**Fix:** `_resolve_university_context()` in `compiler.py` has a priority chain:
1. University page's `university_name` from `source.json`
2. `metadata.json`'s `university_name`
3. Title-cased slug (last resort, acceptable only if workspace has no University page)

The UI was also patched to strip version suffixes from display names.

**How to avoid:** Always create the University page first when setting up a new workspace.
This ensures `university_name` is available in the index before any other pages compile.

**Files involved:**
- `backend/workspace/compiler.py` (`_resolve_university_context`)
- `backend/workspace/manager.py`

---

## REG-008: Duplicated `format_fee` Implementation

**Cause:** The fee formatting function was written inline in `renderer/engine.py` and
again in `transformers/base.py`. The two copies diverged — one stripped `INR` prefix,
the other didn't, causing fees to display as `₹INR 1,20,000` in some templates.

**Fix:** Single canonical `format_fee()` in `core/utils.py`. Both files now import from there.
A comment in both files explains the delegation.

**How to avoid:** All shared text/value processing belongs in `core/utils.py`. Do not
reimplement formatting logic in transformers or templates.

**Files involved:**
- `backend/core/utils.py`
- `backend/transformers/base.py`
- `backend/renderer/engine.py`

---

## REG-009: Parser Not Moved to Backend (Historical)

**Cause:** Based on the previous conversation summary ("Moving Parser to Backend"),
the parser was originally not in the backend package, causing import issues or deployment
complications.

**Fix:** Parser and all ingestion modules now live under `backend/ingestion/`.
CLI entrypoint `ingestion/ingest.py` can still be run directly for testing.

**How to avoid:** All Python backend modules must be importable from the `backend/`
working directory. Do not place shared Python logic outside the `backend/` package.

**Files involved:**
- `backend/ingestion/parser.py`
- `backend/ingestion/extractor.py`
- `backend/ingestion/ingest.py`
