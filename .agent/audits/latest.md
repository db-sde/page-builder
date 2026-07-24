# audits/latest.md — Codebase Audit

**Date:** 2026-07-24 (schema-coverage audit)
**Auditor:** AI Agent (end-to-end Micro-App schema verification)
**Scope:** Full pipeline read — ingestion, adapter, transformers, renderer, templates, compiler, builder, editor — traced against the latest Micro App JSON schema (University / Course / Specialization).
**Prior audit:** archived at `audits/archive/2026-07-24-initial.md` (it predates this schema trace and over-stated content fidelity).
**Deliverables (repo root):** `SCHEMA_COVERAGE_REPORT.md`, `PIPELINE_TRACE.md`, `HARDCODED_CONTENT_AUDIT.md`, `TEMPLATE_AUDIT.md`, `PLATFORM_AUDIT.md`.

---

## Headline

The pipeline **plumbing** is sound (deterministic ingestion, two-pass compiler, canonical URLs, WebP, image-validation gate, SEO scaffolding, tenant isolation). The **content contract is not honoured**: the platform is schema-ready for scalar/identity data but **not schema-faithful for editorial content**.

This corrects the previous audit's "No fabricated data" strength claim — that is **false in the current code**.

---

## Confirmed drift from RULES.md

- **R1 (never fabricate)** — 🟥 violated pervasively. `renderer/engine.py` injects fabricated fallbacks when schema collections are empty: fake named reviews (`engine.py:866`), fake job salaries (`:836`), NMIMS recruiter logos (`:1008`), full hardcoded MBA syllabus (`:908`), hardcoded FAQs (`:895`, also emitted into `FAQPage` JSON-LD), 3-row fee table (`:794`), 7-row other-specs table (`:965`), demo blog posts (`:1156`). `transformers/course.py` adds hardcoded admission steps (`:41`) and invented accreditation prose (`:184`). Templates add `NIRF #24`, `AIU Member`, `WES Recognised` (`university.html:84,128`) and a fabricated spec salary `₹14.2L` (`specialization.html:115`).
- **R2 (templates render only transformed data)** — 🟥 violated. Section titles are hardcoded (no `*_heading` field is consulted); `university.html` renders hardcoded marketing prose instead of `about/why_choose/emi/exam/placement/facts/accreditations`.
- **R6 (slug never in UI)** — 🟥 violated at `specialization.html:429` (`admissions@{{university_slug}}online.edu`).
- **R11/R13** — ⚠️ dead `spec_desc_map` (`course.py:49`), duplicate transform layer (engine rebuilds transformer collections), two spec-name cleaners.

## Schema coverage in one line

Scalars (names, fees, approvals, SEO, duration, mode) flow correctly. **Dropped with zero consumers:** all `*_heading`, `faculty_members`, `faculty_intro`, `validity`, `certificate_heading`, `linked_university`, `linked_course`. **Overwritten on empty:** jobs, reviews, faqs, fee_plans, syllabus, other_specs. **Transformed but not rendered (university):** about_content, why_choose_content, emi_content, exam_content, placement_content, facts, accreditations, admission_fee_note, programs_intro.

## Structural notes

- `renderer/engine.py` is a *second transformer* that discards most per-type transformer output for repeaters — this is where fabrication lives.
- Editor (`fieldSchema.js`) exposes no repeaters at all, so operators cannot review list data (or spot fabrication) before publish.
- Tenant-specific logic still in shared code: GA hardcoded to `nmims-2` + real GA ID (`builder.py:231`), `engine.py:1048` nmims-2 EMBA rule, `engine.py:502` `"nmims"` default.

## Corrected facts vs. old docs

- `systems/seo.md` said "No per-page lastmod in sitemap" — **outdated**: `builder.py::_write_sitemap` emits `<lastmod>` per page. (Corrected in this pass.)
- Old `audits/latest.md` "No fabricated data" strength — **removed** (was incorrect).

## Action items (for a future change effort — NOT done here)

| Priority | Item |
|---|---|
| Critical | Remove fabricated fallbacks in `engine.py`; guard syllabus with `{% if %}`; restore R1 |
| Critical | Render university schema content + faculty; stop hardcoded marketing blocks |
| High | Consume `*_heading` fields |
| High | Fix R6 slug-in-email; parameterise GA via `metadata.json["ga_id"]` |
| Medium | Collapse double transform layer; expose repeaters in editor |
| Medium | Remove dead code (`spec_desc_map`, unused vars) |
| Low | Ingestion + compiler unit tests |
