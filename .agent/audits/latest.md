# audits/latest.md — Codebase Audit

**Date:** 2026-07-24
**Auditor:** AI Agent (initial .agent/ creation audit)
**Scope:** Full repository read — backend, frontend, contact app, git log, REPORT.md

---

## Summary

The codebase is in good working order. The architecture is coherent and well-structured.
The pipeline is deterministic and consistent. Both the backend server and frontend admin UI
are confirmed running (`uv run main.py`, `npm run dev`).

---

## Findings

### ✅ Strengths

1. **Clear separation of concerns** — parser, extractor, adapter, transformers, renderer,
   compiler, builder, and editor are all distinct subsystems with well-defined interfaces.

2. **No fabricated data** — the `normalize_value()` function in `core/router.py` strips all
   NA/null variants before transformers run. Templates use `{% if %}` guards throughout.

3. **DRY utility layer** — `core/utils.py` contains canonical implementations of
   `format_fee()`, `normalize_specialization_name()`, `read_parent_course_data()`, and
   `build_public_route()`. No duplicates found in the current codebase.

4. **Multi-tenant isolation** — workspace slugs are correctly isolated. NMIMS contact info
   does not leak into other workspaces (fixed in commit `532b518`).

5. **Robust table parser** — `process_table_block()` handles merged title rows, all-identical
   headers, and column count mismatches. Emits structured warnings, not silent failures.

6. **Build validation** — `_validate_pages()` blocks the build if required images are missing.
   Prevents broken-image production deploys.

7. **WebP optimisation** — images are converted to WebP with responsive variants at build time.
   `<picture>` elements in templates use these variants correctly.

8. **JSON-LD coverage** — BreadcrumbList, Course, FAQPage, and Organization are all implemented
   correctly with no invented values.

---

### ⚠️ Concerns

1. **`main.py` is 1774 lines** — the FastAPI application file contains route handlers,
   helper functions, heuristic detection logic, and image processing utilities mixed together.
   This creates a large surface area for bugs and makes it hard to test individual concerns.
   *Recommendation: future refactor could extract helpers into domain modules, but only
   when there is a concrete need (YAGNI).*

2. **No automated tests** — `test_spec.py` exists (2772 bytes) but appears minimal.
   The parser, extractor, adapter, compiler, and builder have no unit test coverage.
   Any regression must be caught manually through the Review UI.

3. **`engine.py` is 1380 lines** — the renderer is also very large. It combines Jinja2
   setup, custom filters, structured data builders, SEO injectors, HTML parsers, and the
   main render function in one file.

4. **GA tag is hardcoded to nmims-2** — `_finalize_html()` in `builder.py` checks
   `if university_slug == "nmims-2":` and injects a specific GA tracking ID. If other
   workspaces need analytics, this needs generalisation.

5. **`primary_domain` resolution is fragile** — the sitemap and canonical URLs rely on
   `metadata.json["primary_domain"]`, which may not exist in all workspaces.
   The fallback to `LEAD_BASE_URL` is likely incorrect (the lead app domain ≠ the site domain).

6. **Image upload is Base64 over JSON** — large images (> a few MB) may cause timeouts
   or hit FastAPI's body size limits when sent as Base64-encoded JSON from the frontend.

7. **No Redis caching** — `engine.py` has a `TODO` comment for caching `render_resolved()`.
   Large workspaces with many pages will re-render everything on every compile.

8. **Heuristic parent detection can be wrong** — the token-overlap scorer in `main.py`
   will return the best-scoring course even if the score is very low. For unique
   specialization slugs that share no tokens with any course, this may produce incorrect
   pre-fills that an operator might not notice and correct.

---

### ❌ Not Found / Not Implemented

- No real-time build status UI (listed in roadmap)
- No direct cloud storage publishing (listed in roadmap)
- No global search across pages (listed in roadmap)
- No loading indicators in contact form (listed in roadmap)

---

## Action Items

| Priority | Item |
|---|---|
| High | Add unit tests for parser, extractor, adapter |
| High | Fix `primary_domain` resolution for sitemap/canonical URLs |
| Medium | Generalise GA tag injection via `metadata.json["ga_id"]` |
| Medium | Add loading state to contact form inputs |
| Low | Split `main.py` helpers into domain modules when it causes a concrete problem |
| Low | Implement Redis caching for `render_resolved()` |
