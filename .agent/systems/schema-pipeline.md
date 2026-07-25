# systems/schema-pipeline.md — Schema-Driven Content Pipeline (Field Definitions → Page Requirements → Page State)

Status: Phase 2 complete (2026-07-24). **Read-only metadata layer.** It changes no
rendering, templates, transformers, builder, compiler, workspace, routing, SEO, or
storage. It prepares data the admin **Preview** will consume later and that the
**renderer cleanup** (Phase 3) will use to drop fabricated fallbacks.

---

## The three-layer model

Two different questions, deliberately kept separate:

| Layer | File | Question it answers | Source of truth |
|---|---|---|---|
| **1. Field Definitions** | `backend/core/field_definitions.py` | *"What data exists?"* — the schema of a parsed page + who owns each field | the Micro-App JSON schema |
| **2. Page Requirements** | `backend/core/page_requirements.py` | *"What data does this page's template actually use?"* | the Jinja2 **templates** |
| **3. Page State** | `backend/core/page_requirements.py::build_page_state` | *"Given the parsed values, which template sections can render, and which missing fields actually matter?"* | Layers 1 + 2 + parser values |

```
Field Definitions ─┐
Page Requirements ─┼─► build_page_state() ─► Page State  (section-level readiness)
Parser Values ─────┘        (via field_state)
```

> **Schema ≠ Template.** The schema defines *available* data; the template defines
> *displayed* data. A field can exist in the schema and stay in `field_state` while
> no section renders it — e.g. `faculty_members`, every `*_heading`, and (on the
> university page) `about_content` / `why_choose_content` / `emi_content` / etc.
> These are **unused schema fields**. They stay in the schema, stay editable, and
> **must never generate page-completion warnings**.

---

## Layer 1 — Field Definitions (Phase 1)

`PAGE_FIELD_DEFINITIONS[page_type][field] = {source, required, optional, manual, derived}`
- `source`: `AUTO` (parser), `MANUAL` (operator upload, e.g. images), `DERIVED` (slug/page_type/…).
- `build_field_state(page_type, values, derived_values)` → per-field
  `{name, source, required, optional, manual, derived, missing, value}`.
- Parser-extension fields outside the canonical schema are kept (as `AUTO`) so the editor still sees them.
- Read-only: never mutates parsed values. Unsupported page types (e.g. `blog`) return `{}`.

## Layer 2 — Page Requirements (Phase 2)

`PAGE_REQUIREMENTS[page_type] = [ section, … ]`, read straight from the templates.
Defined for `university`, `course`, `specialization` (blog keeps its legacy parser).

Each **section** carries:
- `section`, `label`
- `required` — is the section essential to the page (**only the hero is**)
- `required_fields` — fields that gate the section. An entry may be a plain name
  (must be present) or a **list = any-of** (e.g. course About renders from
  `about_content` OR `hero_description`)
- `optional_fields` — rendered when present, not required
- `always_rendered` — template emits the section even with no data (no `{% if %}` guard)
- `fabricated_when_empty` — the renderer injects hardcoded/fabricated content when the
  real fields are empty (Phase 3 cleanup target; see `HARDCODED_CONTENT_AUDIT.md`)
- `data_source` — `page` | `workspace` (courses/specs/blogs, resolved at compile time) | `shared` (knowledge base / site config / hardcoded marketing)

Helper: `template_field_usage(page_type)` → `{field: [section_ids]}`.

### Why some sections have no `required_fields`
Workspace- and shared-sourced sections (programs grid, specializations grid,
recruiters, why-choose, blog preview, other-specs comparison) are not filled from
this page's own fields, so their real-data readiness is decided outside a single
page. They are marked with `data_source` and (where applicable) `fabricated_when_empty`.

## Layer 3 — Page State (Phase 2)

`build_page_state(page_type, field_state)` (or `build_page_state_from_values(...)`) returns:

```jsonc
{
  "page_type": "course",
  "sections": [
    {
      "section": "about", "label": "About", "required": false,
      "fields_used": ["about_content", "hero_description"],
      "required_fields": [["about_content", "hero_description"]],
      "optional_fields": [],
      "renderable": false,                 // any-of group unsatisfied
      "missing_required": [["about_content", "hero_description"]],
      "missing_optional": [],
      "always_rendered": false,
      "fabricated_when_empty": false,
      "data_source": "page"
    }
    // …
  ],
  "unused_schema_fields": ["about_heading", "faculty_members", "validity", …],
  "infrastructure_fields": ["_meta", "page_type", "slug", "university_slug", "parent_slug"],
  "field_usage": { "faculty_members": {"used_by_template": false, "sections": []}, … },
  "summary": {
    "required_sections_incomplete": [],    // essential (hero) sections not renderable
    "optional_sections_incomplete": ["about"],
    "renderable_sections": ["seo", "hero", "stats", …],
    "fabricated_sections": ["fees", "syllabus", "jobs", "reviews", "faqs", "admission"]
  }
}
```

- `renderable` = no `required_fields` missing (any-of groups satisfied if ≥1 member present).
- `unused_schema_fields` = defined fields not used by any section (excluding infrastructure). **These never warn.**
- `infrastructure_fields` = `_meta` + all `DERIVED` fields — routing/plumbing, never "unused", never warn.
- Pure/read-only: does not mutate `field_state` or values. Unsupported page types return `{}`.

---

## Only template-used fields count toward completion

Page completion is derived **only** from sections' `required_fields`
(`summary.required_sections_incomplete` / `optional_sections_incomplete`). Fields in
`unused_schema_fields` are excluded by construction, so an absent `faculty_members`
or `about_heading` cannot mark a page incomplete.

---

## Where it is wired

`build_page_state` runs next to `build_field_state` in `backend/main.py`, and
`page_state` is added to the same responses that already carry `field_state`:
- `POST /ingest-acf`
- `POST /parse-docx` (university/course/specialization branch)
- `POST /save-page`
- the source-record read used by preview

Purely additive JSON. No endpoint changed shape destructively; no render path touched.

---

## How Preview will use Page State (future — no UI yet)

The frontend Preview will read `page_state.sections` to show, per section:
- `label`, `fields_used`
- `renderable` → render normally vs. show a placeholder
- `missing_required` → "this required section is incomplete: add X"
- `missing_optional` → soft hints, no warning weight
- `fabricated_when_empty` + `data_source` → mark sections currently backed by fake or
  workspace/shared content, so Preview and the Phase 3 renderer cleanup can
  distinguish real data from fabricated fallback.

No placeholder UI and no renderer change were made in this phase — only the data.

---

## Boundaries (YAGNI)

No rule engine, no plugin system, no new rendering engine. Page Requirements are plain
static Python dicts read from the templates. When a template changes (e.g. Phase 3 makes
the university page render `about_content` and add a faculty section), update the
matching `PAGE_REQUIREMENTS` section — the templates remain the source of truth.

See also: `systems/parser.md`, `systems/renderer.md`, `systems/templates.md`,
and root `SCHEMA_COVERAGE_REPORT.md` / `HARDCODED_CONTENT_AUDIT.md`.
