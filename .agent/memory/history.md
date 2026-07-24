# memory/history.md — Session History

One section per development session. Newest first.

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
