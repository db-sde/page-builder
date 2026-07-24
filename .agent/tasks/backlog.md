# tasks/backlog.md — Future Improvements

Items here are not in the current sprint. They are organised by subsystem.
Move items to `tasks/current.md` when they become active.

---

## Parser / Ingestion

- [ ] Unit tests for `parser.py` (table parsing, heading detection, list items)
- [ ] Unit tests for `extractor.py` (section extraction, fuzzy heading matching)
- [ ] Unit tests for `adapter.py` (merge logic, field normalisation)
- [ ] Unit tests for `ingestion/ingest.py` CLI
- [ ] Handle DOCX footnotes and endnotes (currently silently dropped)
- [ ] Handle embedded images in DOCX (extract and save to Assets/images/)
- [ ] Improve heuristic parent detection confidence threshold — avoid returning
      a "best" match when the real score is too low to be meaningful

---

## Templates

- [ ] Responsive CSS refinement for 768–1024px breakpoint range
- [ ] Shared Jinja2 base template / `extends` hierarchy to reduce duplication across 7 templates
- [ ] Review and improve mobile UX for specialization comparison table
- [ ] Add structured `<table>` ARIA labels for accessibility

---

## Editor (Admin Frontend)

- [ ] Loading state / spinner on submit button in Contact app
- [ ] Better validation message design in Contact form (currently plain browser alerts)
- [ ] Direct image upload (multipart form-data) instead of Base64-over-JSON
  — avoids payload size issues and API timeouts for large images
- [ ] Real-time build status indicator in Screen3 (WebSocket or polling)
- [ ] Display compiler/builder validation errors in the UI instead of requiring console check
- [ ] Auto-save draft to prevent data loss on accidental page refresh

---

## Publishing / Builder

- [ ] Generalise GA tag injection: read `ga_id` from `metadata.json` per workspace
- [ ] Per-page `lastmod` in `sitemap.xml` (use file mtime of `source.json`)
- [ ] Compiler page caching — skip re-rendering unchanged pages (compare `source.json` mtime)
- [ ] Redis caching for `render_resolved()` (TODO exists in `engine.py`)
- [ ] Direct cloud publishing: upload `build/` to AWS S3 or Cloudflare Pages from builder

---

## SEO

- [ ] Fix `primary_domain` resolution — should come from `metadata.json["primary_domain"]`
      not fall back to `LEAD_BASE_URL`
- [ ] Add `hreflang` tags if/when multilingual content is introduced
- [ ] Add `VideoObject` JSON-LD for any course/specialization video embeds

---

## Performance

- [ ] Compiler caching to skip unchanged pages
- [ ] Redis cache for `render_resolved()`
- [ ] Lazy load assessment for all secondary images (below-fold)
- [ ] Preconnect hints for LEAD_BASE_URL in compiled pages

---

## UI / UX

- [ ] Dark mode support for admin frontend (currently light only)
- [ ] Keyboard navigation improvements in Screen2 Review editor
- [ ] Workspace search/filter in Screen0 (for operators managing many universities)

---

## Infrastructure

- [ ] Global search index across all course pages in workspace static files
- [ ] Real-time CRM sync (currently one-way: page builder → CRM via webhook)
- [ ] Workspace version history / rollback (currently one version per workspace)
