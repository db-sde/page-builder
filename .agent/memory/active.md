# memory/active.md — Current Work

Last updated: 2026-07-24

---

## What Is Being Worked On?

A full **schema-coverage audit** was completed 2026-07-24, tracing the latest Micro App JSON
schema (University / Course / Specialization) end-to-end. Read-only — no code changed.
Deliverables at repo root: `SCHEMA_COVERAGE_REPORT.md`, `PIPELINE_TRACE.md`,
`HARDCODED_CONTENT_AUDIT.md`, `TEMPLATE_AUDIT.md`, `PLATFORM_AUDIT.md`.
Updated `.agent`: `audits/latest.md`, `memory/regressions.md` (REG-010, REG-011), `systems/seo.md`.

---

## Why?

To verify whether the platform fully supports the new Micro-App schema before any further changes.

---

## Key finding (must address before further feature work)

The pipeline is schema-ready for scalar data but **NOT schema-faithful for editorial content**:
- `renderer/engine.py` fabricates content on empty collections (fake reviews/jobs/recruiters/
  syllabus/FAQs/fees) — violates R1/R2. See REG-010.
- All `*_heading` fields, `faculty_members`, `faculty_intro`, `validity`, `certificate_heading`,
  `linked_*` are unconsumed (zero references).
- `university.html` drops parsed `about/why_choose/emi/exam/placement/facts/accreditations`.
- R6 slug leak at `specialization.html:429` (REG-011).

---

## What Remains?

**From the audit (highest priority — not yet started):**
1. Remove fabricated fallbacks in `engine.py`; guard syllabus section (REG-010)
2. Render university schema content + faculty section
3. Consume `*_heading` fields; expose repeaters in the editor
4. Fix R6 slug-in-email (REG-011); parameterise GA via `metadata.json["ga_id"]`

**Pre-existing TODOs / ROADMAP:**
5. Responsive CSS refinement (768–1024px)
6. Contact app polish (loading states, validation UX)
7. Redis caching TODO in `engine.py`; AI gap-fill TODO in `base.py`
8. Tests — parser, extractor, adapter, compiler all lack unit tests

---

## Maintenance Note

> After every coding session, update this file with:
> - What was changed
> - What was left incomplete
> - What the next step is
>
> Move completed items to `memory/history.md`.
