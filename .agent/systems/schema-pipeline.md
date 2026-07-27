# systems/schema-pipeline.md — Schema-Driven Content Pipeline

The complete lifecycle of a page, from `.docx` upload to published HTML.

Status: **Phase 3 complete (2026-07-24)** — editing workflow + fake-content removal.
Phases 1 and 2 built the metadata layers; Phase 3 turned them into the editing
workflow and made rendering fully data-driven.

---

## The editor workflow (what all of this exists to support)

```
Upload DOCX
  ↓  parser extracts everything it can            (external Micro App)
  ↓  page type detected                           (main.extract_metadata_from_json)
  ↓  page blueprint loaded                        (core/page_blueprint.py)
  ↓  derived fields resolved                      (slug / university_slug / parent_slug)
  ↓  explicit defaults auto-filled                (core/editing_state.apply_auto_population)
  ↓  Editing State built                          (core/editing_state.build_editing_state)
  ↓  editor opens on an almost-complete page — only manual fields are empty
  ↓  operator fills what is left + uploads images
  ↓  Preview  = same renderer, placeholders for incomplete sections
  ↓  Publish  = same renderer, incomplete sections hidden
```

There are no other steps. Anything that adds one should be questioned.

---

## The four layers

| Layer | File | Question it answers | Source of truth |
|---|---|---|---|
| **1. Field Definitions** | `core/field_definitions.py` | *What data exists?* — schema + ownership (AUTO / MANUAL / DERIVED, required) | the Micro-App JSON schema |
| **2. Page Requirements** | `core/page_requirements.py` | *What does the template display?* — sections, per-section fields | the Jinja2 **templates** |
| **3. Page Blueprint** | `core/page_blueprint.py` | *What is needed to build this page type?* — layers 1+2 in one contract | layers 1 + 2 |
| **4. Editing State** | `core/editing_state.py` | *Given the parsed values, what is left to do?* | blueprint + parser values |

```
Field Definitions ─┐
Page Requirements ─┼─► Page Blueprint ─┐
                                       ├─► Editing State ─► editor + preview
Parser JSON ───────────────────────────┘
```

> **Schema ≠ Template.** The schema defines *available* data; the template defines
> *displayed* data. Fields the template does not use — `faculty_members`, every
> `*_heading`, `validity`, `linked_*` — are **kept in the data, reported as
> `unused_schema_fields`, and never warned about**. Templates are never forced to
> render every schema field, and sections are never added automatically.

Supported page types: `university`, `course`, `specialization`. Blog keeps the
legacy blog parser and has no blueprint (all builders return `{}` for it).

---

## Parser responsibilities

The parser (external Micro App, `MICRO_APP_URL`; `ingestion/` is the local
fallback) owns extraction. **Assume it is correct.**

- If a value is missing from the parser JSON, that is a parser problem.
- The pipeline never compensates for a parser failure and never fabricates a value.
- `ingestion/adapter.py` merges micro (wins) with the local parser (fills gaps),
  normalises field names and coerces simple types. Nothing else invents data.

## Page Blueprint responsibilities

`build_page_blueprint(page_type)` returns the single contract the editor needs:

- `sections` — ordered (`order` = template order) with `label`, `required`,
  `required_fields` (a nested list means *any-of*), `optional_fields`,
  `always_rendered`, `data_source` (`page` / `workspace` / `shared`)
- `fields` — every schema field with ownership, `image`, `used_by_template`,
  `sections`, and any declared `default`
- `required_fields` / `optional_fields` / `manual_fields` / `derived_fields` /
  `image_fields` / `template_fields` / `defaults`

Image fields are just manual fields whose name ends in `_image_url`; they carry
`label` / `hint` / `dims` so the upload UI needs no second hardcoded list.
There is **no separate image workflow**.

Exposed over HTTP: `GET /page-blueprint` (all) or `GET /page-blueprint?page_type=course`.

## Field ownership

| Source | Meaning | Examples |
|---|---|---|
| `AUTO` | parser supplies it | `program_name`, `about_content`, `faqs` |
| `MANUAL` | only a human can supply it | `hero_image_url`, `certificate_image_url`, `reviews` |
| `DERIVED` | the pipeline computes it | `slug`, `page_type`, `university_slug`, `parent_slug` |

## Automatic population

`apply_auto_population(page_type, values)` fills **only** the defaults declared in
`page_blueprint.EXPLICIT_DEFAULTS` (currently `mode = "100% Online"` for course and
specialization — mirroring what the transformers already did, now visible instead
of hidden). It returns a new dict and the list of names it filled; it never
invents editorial content. It runs at `/ingest-acf` and `/parse-docx`, before the
editor opens.

## Editing State

`build_editing_state(page_type, values, derived_values)` returns everything the
editor screen needs, so the frontend computes nothing:

```jsonc
{
  "page_type": "course",
  "fields": {                      // every field, already classified
    "hero_image_url": {
      "value": null, "source": "MANUAL", "required": true, "optional": false,
      "manual": true, "derived": false, "missing": true, "image": true,
      "used_by_template": true, "infrastructure": false, "sections": ["hero"],
      "auto_filled": false, "in_schema": true, "needs_attention": true,
      "label": "Hero Image", "hint": "...", "dims": "480 × 420px"
    }
  },
  "sections": [ { "section": "about", "renderable": false,
                  "missing_required": [["about_content","hero_description"]],
                  "missing_optional": [], "filled_fields": [], "completion": 0.0 } ],
  "auto_filled": ["mode"],
  "needs_attention": ["certificate_image_url", "hero_image_url"],  // required + missing
  "optional_suggestions": ["reviews"],        // manual + optional: offered, never a warning
  "missing_images": ["certificate_image_url", "hero_image_url"],
  "unused_schema_fields": ["about_heading", "faculty_members", "..."],
  "summary": { "required_total": 9, "required_complete": 7, "ready": false, "..." : [] }
}
```

`needs_attention` is the operator's entire to-do list. A page is `ready` when it
is empty. Unused schema fields can never appear in it.

Returned alongside `field_state` and `page_state` by `/ingest-acf`, `/parse-docx`,
`/save-to-workspace`, and the workspace page read.

---

## Preview flow vs production flow

**One renderer, one template, one pipeline.** `render_resolved(resolved, standalone, preview)`.

| | Preview (`preview=True`) | Production (default) |
|---|---|---|
| Renderer | `renderer/engine.py` | same |
| Template | same | same |
| Context | same | same |
| Sections with no data | placeholder indicator | hidden |
| Fabricated filler | never | never |

Preview is used by `/preview-html` and `/preview-file` only. Everything else —
compiler, builder, workspace save, download — renders in production mode.

Preview adds two things and nothing else:
1. In-template placeholders (`{% elif preview_mode %}`) for guarded sections.
2. A fixed "incomplete sections" panel appended after render (`_build_preview_panel`),
   built from the same Editing State the editor uses.

Both are marked with `data-preview-placeholder` / `data-preview-indicator` and are
absent from production output.

---

## No fabricated content (Phase 3 change — see REG-010)

The renderer used to substitute hardcoded editorial content whenever a field was
empty. All of it is gone:

| Removed | Was in |
|---|---|
| fake named student reviews | `engine.py` |
| fake job profiles + salaries | `engine.py` |
| hardcoded recruiter list | `engine.py` |
| fabricated 2-year MBA syllabus | `engine.py` |
| hardcoded FAQs (also leaked into `FAQPage` JSON-LD) | `engine.py` |
| fabricated fee plans | `engine.py` |
| features / financing / banks filler | `engine.py` |
| hardcoded other-specialization comparison table | `engine.py` |
| demo blog posts | `engine.py` |
| invented "Online MBA" program card | `engine.py` |
| hardcoded admission steps | `transformers/course.py`, `engine.py` |
| invented accreditation claims | `transformers/course.py` |
| "Most Popular Specialization" badge | `transformers/specialization.py` |
| "start with just ₹50,000" EMI clause | `transformers/base.py` |
| `NIRF #24`, `AIU Member`, `WES Recognised`, `default('2010')` | `university.html` |
| `₹14.2L` salary, `₹2,00,000` / `₹8,334/mo` defaults | `specialization.html`, `course.html` |
| `admissions@{{university_slug}}online.edu` (R6 leak, REG-011) | `specialization.html` |
| NMIMS copyright defaults | `course.html`, `blog.html` |

**Kept deliberately:** page layouts, section order, UI labels, navigation, buttons,
CTA copy, design text, and brand-neutral formatting defaults (`mode`, `Contact for fee`).
Only *content* became data-driven.

Sections whose data is empty are now guarded and hidden (`university.html`
programs / specializations / why-choose / admission / fees / recruiters /
testimonials / FAQ / blog; `course.html` + `specialization.html` syllabus).

**Consequence to know:** university pages get visibly shorter where those sections
had no real data. `features`, `recruiters`, `banks`, and `financing` come only from
`university_knowledge.json` `shared_lists`, which is empty in existing workspaces —
so those sections now disappear until populated. `facts` and `accreditations` *are*
parsed and populated but `university.html` still does not render them (a pre-existing
template gap, not a regression). Adding those sections is a product decision, not an
automatic one.

Guard test: `backend/tests/test_no_fabricated_content.py` renders sparse pages of all
three types and asserts none of the removed strings reappear.

---

## Boundaries (YAGNI)

No rendering engine #2, no plugin system, no configurable rule engine, no dynamic
schema builder, no storage-format change. Blueprints are plain static Python dicts
read from the templates. Compiler, builder, workspace layout, routing, SEO and
publishing are untouched.

**When a template changes, update the matching `PAGE_REQUIREMENTS` section** — the
templates remain the source of truth for what is displayed.

See also: `systems/parser.md`, `systems/renderer.md`, `systems/templates.md`,
`memory/regressions.md` (REG-010, REG-011), and root `SCHEMA_COVERAGE_REPORT.md`.
