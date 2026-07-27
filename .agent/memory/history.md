# memory/history.md — Session History

One section per development session. Newest first.

---

## 2026-07-24 — Schema-Driven Content Pipeline Phase 1

**What changed:**
- Added the canonical University/Course/Specialization field ownership contract in
  `backend/core/field_definitions.py`.
- Added non-mutating field-state generation after parser/metadata processing.
- Returned field state from `/parse-docx`, `/ingest-acf`, workspace saves, and existing-page reads.
- Carried field state through the React editor session without changing the current UI.
- Added focused unit tests for schema coverage, ownership flags, missing-state reporting,
  derived identity, extension-field preservation, and input immutability.
- Fixed the non-blog `/parse-docx` warning collection branch to read its existing parsed blocks;
  the previous code referenced a blog-only local variable.

**Files modified:** backend field contract/API plumbing, frontend session plumbing, tests,
and relevant `.agent` architecture/editor/parser memory.

**Outcome:**
- Every audited schema field now has an explicit owner and completeness state before rendering.
- Parser values and production HTML behaviour remain unchanged; no template, transformer,
  renderer, compiler, builder, route, SEO, publishing, workspace format, or image-flow changes.

**Next steps:**
- Phase 2 can consume this contract to remove renderer fabrication and add preview warnings.

---

## 2026-07-24 — Phase 3: Editing Workflow + Fake-Content Removal

**What changed:**
- `core/page_blueprint.py` (new) — one build contract per page type: ordered sections plus
  required / optional / manual / derived / image fields and explicit defaults.
- `core/editing_state.py` (new) — `apply_auto_population()` (declared defaults only) and
  `build_editing_state()` (fields + sections + `needs_attention` + `ready`).
- `main.py` — auto-population runs before the editor opens; `editing_state` returned by
  `/ingest-acf`, `/parse-docx`, `/save-to-workspace` and the page read; new `GET /page-blueprint`.
- **Removed all fabricated content** from `renderer/engine.py`, `transformers/course.py`,
  `transformers/specialization.py`, `transformers/base.py` and the templates (REG-010),
  and the workspace-slug email leak (REG-011). Dead `spec_desc_map` deleted.
- Empty sections are now guarded: hidden in production, placeholder in preview.
- `render_resolved(..., preview=False)` — one renderer for both modes; preview adds
  in-template placeholders plus an "incomplete sections" panel, nothing else.
- Frontend: `editing_state` carried through the session; `FieldHealthPanel` now derives its
  rows from the backend state (unused schema fields never warn), with `diffFields` as the
  blog fallback.
- Tests: `test_page_blueprint`/`test_editing_state` (13) and `test_no_fabricated_content` (6).
  Suite 35/35 green. Verified against the real `nmims-2` and `ignou` workspaces.

**Outcome:**
- Upload → 7 of 9 required course fields already filled; the operator's whole to-do list is
  the two images. Pages are fully data-driven; no fake reviews/jobs/recruiters/syllabus/FAQs.

**Known impact:** university pages shrink where sections had no real data — `features`,
`recruiters`, `banks`, `financing` exist only in `university_knowledge.json` `shared_lists`,
which is empty in both current workspaces. Populate the knowledge base, or decide as product
work whether `university.html` should render the already-parsed `facts` / `accreditations`.

**Next steps:** product decision on the university page sections and `*_heading` consumption;
optionally drive the editor's field list and image slots from `GET /page-blueprint` so
`fieldSchema.js` stops duplicating the schema.

---

## 2026-07-24 — Schema-Driven Pipeline Phase 2 (Page Requirements + Page State)

**What changed:**
- Added `backend/core/page_requirements.py` — template-derived `PAGE_REQUIREMENTS`
  (university/course/specialization) + `build_page_state()` / `build_page_state_from_values()`.
- Wired `page_state` alongside the existing `field_state` in `backend/main.py` (ingest-acf,
  parse-docx, save-page, source-record read). Additive JSON only.
- Tests: `backend/tests/test_page_requirements.py` (9) + extended `test_post_parser_pipeline.py`.
  Full suite 16/16 green (`uv run python -m unittest discover -s tests`).
- Docs: `.agent/systems/schema-pipeline.md` (three-layer model + Preview usage), linked from AGENTS.md.

**Files modified:** `core/page_requirements.py` (new), `main.py` (4 additive spots), tests,
`.agent/systems/schema-pipeline.md` (new), `AGENTS.md`. No templates/renderer/builder/compiler/
workspace/routing/SEO/storage changes.

**Outcome:**
- Section-level render readiness now derivable per page; unused schema fields (faculty, `*_heading`,
  university-dropped content) are classified and excluded from completion — never warn.
- Fabricated-content sections flagged (`fabricated_when_empty`) so Phase 3 can remove fake fallbacks
  (REG-010) with a data signal instead of guessing.

**Next steps:** Phase 3 — Preview placeholder UI (frontend consumes `page_state`) and renderer
cleanup (remove fabricated fallbacks), which will also update `PAGE_REQUIREMENTS` as templates change.

---

## 2026-07-24 — Micro-App Schema Coverage Audit

**What changed:**
- Full read-only audit of the pipeline vs. the latest Micro App JSON schema.
- Produced 5 root-level reports: `SCHEMA_COVERAGE_REPORT.md`, `PIPELINE_TRACE.md`,
  `HARDCODED_CONTENT_AUDIT.md`, `TEMPLATE_AUDIT.md`, `PLATFORM_AUDIT.md`.
- Updated `.agent`: rewrote `audits/latest.md` (archived prior to `audits/archive/2026-07-24-initial.md`),
  added REG-010 (fabricated fallback content) + REG-011 (slug-in-email) to `memory/regressions.md`,
  corrected the stale "no lastmod" note in `systems/seo.md`, refreshed `memory/active.md`.

**Files modified:** documentation only (`.agent/**`, root `*_REPORT.md`/`*_AUDIT.md`). No backend/frontend code touched.

**Outcome:**
- Established that the platform is schema-ready for scalar/identity fields but not schema-faithful
  for editorial content: pervasive fabricated fallbacks (R1/R2 drift), all `*_heading` + faculty
  fields unconsumed, university template drops parsed content.

**Next steps:**
- Prioritise REG-010 remediation (remove fabrication) before shipping schema-dependent features.

---

## 2026-07-24 — .agent/ Memory System Created

**What changed:**
- Created `.agent/` directory with full project memory structure
- Wrote `AGENTS.md`, `PROJECT.md`, `ARCHITECTURE.md`, `RULES.md`, `ROADMAP.md`
- Wrote `memory/active.md`, `memory/decisions.md`, `memory/regressions.md`, `memory/history.md`
- Wrote `systems/parser.md`, `systems/renderer.md`, `systems/templates.md`,
  `systems/editor.md`, `systems/publishing.md`, `systems/seo.md`
- Wrote `audits/latest.md`
- Wrote `tasks/current.md`, `tasks/backlog.md`

**Files modified:**
- None (all `.agent/` files are new additions)

**Outcome:**
- Complete project memory established from reading the full codebase, git log, and REPORT.md

**Next steps:**
- Update `memory/active.md` after the next coding session
- Record any new architectural decisions in `memory/decisions.md`
- Add any new regressions discovered to `memory/regressions.md`

---

## Prior Sessions (Summary from Git Log)

The following is a condensed summary of significant git commits before this memory system was created.

| Date (approx.) | Summary |
|---|---|
| 2026-07 | Migrated static assets and templates to unified directory structure; removed legacy v2 codebase |
| 2026-07 | Standardised public routing with canonical logic and improved URL path resolution |
| 2026-07 | Implemented automatic SEO and Open Graph meta tag injection with canonical URL normalisation |
| 2026-07 | Migrated to local font hosting; improved image preloading; non-blocking image validation |
| 2026-07 | Implemented robust table parsing, header normalisation, and warning system |
| 2026-07 | Optimised images with WebP conversion, responsive source sets, and lazy loading |
| 2026-06 | Implemented dynamic field resolution and knowledge-based context injection |
| 2026-06 | Implemented `robots.txt` generation pointing to sitemap |
| 2026-06 | Consolidated shared utilities (`format_fee`, `read_parent_course_data`, site config) |
| 2026-06 | Implemented workspace and page deletion endpoints and UI controls |
| 2026-06 | Implemented page editing functionality |
| 2026-06 | Added branding support for custom logos and favicons |
| 2026-06 | Removed legacy migration scripts; introduced unified ingestion adapter |
| 2026-06 | Introduced specialization normalisation and fee plan classification |
| 2026-06 | Fixed all responsive design issues |
| 2026-06 | Implemented parent course detection and manual remapping for specializations |
| 2026-06 | Implemented mobile-responsive navigation |
| 2026-06 | Moved parser to backend (from previous conversation) |

> For full details, run: `git log --oneline` from the repository root.
