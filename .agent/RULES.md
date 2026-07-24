# RULES.md — Permanent Project Rules

These rules are permanent. They are not preferences. Do not override them without explicit
discussion and a written decision entry in `memory/decisions.md`.

---

## Content Rules

### R1 — Never fabricate content
If a field is `None`, empty, `"NA"`, `"N/A"`, `"null"`, or `"none"`, the section
is hidden. Do not insert placeholder text, lorem ipsum, or invented data.
The `normalize_value()` in `core/router.py` normalises all these variants to `None`
before any transformer runs.

### R2 — Templates only render transformed data
Jinja2 templates receive the context dict from a transformer. They never compute,
derive, or look up new data. All data preparation happens in Python.

### R3 — Listing pages are system-generated
`programs_listing`, `specializations_listing`, and `blog_listing` are automatically
rebuilt by the compiler. Never create or edit them manually. Never upload a DOCX
to create a listing page.

### R4 — Generated HTML is never edited manually
Every `.html` file in a workspace is an output of the compiler. Editing it directly
will be overwritten on the next compile. Always fix the transformer, template, or
`source.json` instead.

### R5 — source.json is the source of truth
`source.json` is the on-disk database record for every page. Do not edit it manually
in production except to fix corrupt data. The authoritative path to update it is via
the Review UI or a pipeline re-run.

---

## Architecture Rules

### R6 — Workspace slug must never appear in the UI
The workspace directory name (e.g., `nmims-2`, `test-1`) is internal. User-facing
titles, breadcrumbs, headers, footers, and badges must use the `university_name`
derived from the workspace's University page or `metadata.json`.

### R7 — Specializations are flat
Specializations are stored at `workspaces/<uni>/Specializations/<slug>/`. They are
never nested inside `Courses/<course-slug>/Specializations/`. The parent relationship
is expressed only via the `parent_slug` field in `source.json`.

### R8 — Preserve parser contracts
`parser.py` produces a list of typed blocks (`h1`, `h2`, `h3`, `bold_para`, `paragraph`,
`list_item`, `table`). `extractor.py` consumes these with `HEADING_ANCHORS` fuzzy matching.
Do not change block type names or the `HEADING_ANCHORS` mapping without updating both sides.

### R9 — Lead capture is fully decoupled
No lead form logic, CRM calls, or webhook submissions exist in the page builder backend.
All CTAs link to `LEAD_BASE_URL` with a Base64-encoded payload. The contact app is
independent and deployed separately.

### R10 — The build/ directory is ephemeral
`build/` is wiped and rebuilt on every `build_website()` call. Do not store anything
important there. The workspace source files (source.json, Assets/) are the permanent store.

---

## Engineering Rules

### R11 — YAGNI
Build only what is currently required. Do not add abstraction layers, configuration
options, or generalisation that has no immediate use case.

### R12 — Do not redesign working systems
If a subsystem works correctly, do not refactor it to be "cleaner" without a concrete
bug or performance problem. Unnecessary refactors introduce regressions.

### R13 — Single canonical implementation for shared logic
`format_fee()` lives in `core/utils.py`. `normalize_specialization_name()` lives in
`core/utils.py`. `read_parent_course_data()` lives in `core/utils.py`. If a utility
is needed in two places, it goes in `core/utils.py` — not duplicated.

### R14 — Never remove existing features without evidence of harm
Do not delete endpoints, template sections, or transformer fields unless there is
confirmed evidence that they are broken or unused. Use deprecation markers first.

### R15 — Image validation blocks the build
Missing or invalid `hero_image_url` / `certificate_image_url` files cause the builder
to emit validation errors. This is intentional — broken asset references must not
silently produce blank images in production.

### R16 — No hardcoded university contact info in shared paths
`core/site_config.py` has a `SITE_CONFIG` dict for the original `nmims` workspace.
For all other workspaces, the generic `_generic_site_config()` is used, with overrides
loaded from `metadata.json`'s `contact` section. Never bake another university's
contact info into shared code.

---

## Maintenance Rules (for AI agents)

- **Update `memory/active.md`** after every coding session.
- **Record architectural decisions** in `memory/decisions.md` using the ADR format.
- **Record every regression** and its fix in `memory/regressions.md`.
- **Move finished work** from `active.md` into `memory/history.md`.
- **Keep AGENTS.md concise** — under ~200 lines. Move details to subsystem files.
- **Never duplicate information** across `.agent/` files. Cross-reference instead.
- **Archive old audits** into `audits/archive/` instead of deleting them.
- **Keep the folder useful, not large** — one file per subsystem, not one file per feature.
