# memory/active.md — Current Work

Last updated: 2026-07-24

---

## What Is Being Worked On?

**Schema-driven content pipeline Phase 2** implemented 2026-07-24 (on top of Phase 1).
Added the template-derived **Page Requirements** + **Page State** layer
(`backend/core/page_requirements.py`): per template section — which schema fields it uses,
whether it can render, missing required/optional fields, and `fabricated_when_empty`/`data_source`
flags. `page_state` now rides alongside `field_state` in `/ingest-acf`, `/parse-docx`,
`/save-page`, and existing-page reads. Read-only metadata — no template/renderer/production change.
Full model documented in [systems/schema-pipeline.md](../systems/schema-pipeline.md).

Phase 1 (still in place): one post-parser ownership contract per field
(`backend/core/field_definitions.py`), exposed as `field_state`.

Three-layer model: **Field Definitions** (schema — what data exists) →
**Page Requirements** (templates — what data is displayed) → **Page State** (render readiness).

---

## Why?

Phase 1 makes missing/manual/derived/optional state explicit after parsing. Phase 2 makes
*page requirements* explicit: only fields a template actually uses count toward completion, so
unused schema fields (faculty, `*_heading`, university-dropped content) never warn — and each
section knows whether it can render, ready for Preview placeholders and renderer cleanup.

---

## Current boundary

- Ownership: `backend/core/field_definitions.py`; page requirements: `backend/core/page_requirements.py`
- Parser JSON unchanged; unused fields preserved and classified (never warn)
- `field_state` / `page_state` are transient API/editor metadata, not part of `source.json`
- Templates, renderer, compiler, builder, routing, SEO, publishing, image behaviour **unchanged**

## Key finding still to address

The pipeline is schema-ready for scalar data but **NOT schema-faithful for editorial content**:
- `renderer/engine.py` fabricates content on empty collections (fake reviews/jobs/recruiters/
  syllabus/FAQs/fees) — violates R1/R2. See REG-010.
- All `*_heading` fields, `faculty_members`, `faculty_intro`, `validity`, `certificate_heading`,
  `linked_*` are unconsumed (zero references).
- `university.html` drops parsed `about/why_choose/emi/exam/placement/facts/accreditations`.
- R6 slug leak at `specialization.html:429` (REG-011).

---

## What Remains?

**Phase 3 (next):**
1. Preview placeholder UI — frontend consumes `page_state.sections` (renderable / missing / placeholders)
2. Remove fabricated fallbacks in `engine.py`; guard syllabus section (REG-010) — use the
   `fabricated_when_empty` flags as the removal map; update `PAGE_REQUIREMENTS` as templates change
3. Render university schema content + faculty section where product-approved
4. Consume `*_heading` fields; expose repeaters in the editor
5. Fix R6 slug-in-email (REG-011); parameterise GA via `metadata.json["ga_id"]`

**Pre-existing TODOs / ROADMAP:**
6. Responsive CSS refinement (768–1024px)
7. Contact app polish (loading states, validation UX)
8. Redis caching TODO in `engine.py`; AI gap-fill TODO in `base.py`
9. Tests — parser, extractor, adapter, compiler still lack focused unit tests

---

## Maintenance Note

> After every coding session, update this file with:
> - What was changed
> - What was left incomplete
> - What the next step is
>
> Move completed items to `memory/history.md`.
