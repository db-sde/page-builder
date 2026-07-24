# SCHEMA_COVERAGE_REPORT.md

**Audit date:** 2026-07-24
**Scope:** Micro App JSON schema (University / Course / Specialization) vs. the DegreeBaba backend pipeline.
**Mode:** Read-only audit. No code changed.

---

## How to read this

For every field in the supplied Micro App schema, the matrix records whether the field is:

- **Parser** — produced by the ingestion layer. The **Micro App is canonical** and emits every schema field; the local `extractor.py` is only a fallback and covers a subset. `M` = micro only, `M+L` = micro and local both produce it, `—` = neither.
- **Transformer** — read by a `transformers/*.py` class (or `renderer/engine.py`, which acts as a second transformer).
- **Editor** — present in `frontend/src/fieldSchema.js` (visible/editable in the Review UI).
- **Renderer** — the field's own value reaches a template variable.
- **HTML** — the value can appear in the final page.
- **Status** — one of:
  - ✅ **Flows** — parsed → rendered → HTML using the field's own value.
  - ⚠️ **Partial** — reaches HTML but altered, conditionally dropped, or only via knowledge base.
  - 🟥 **Dropped** — parsed and stored in `source.json`, but no consumer renders it.
  - 🟧 **Overwritten** — value is rendered *only if present*, but the renderer replaces the section with fabricated fallback content when absent (see `HARDCODED_CONTENT_AUDIT.md`).

> **Headline finding:** every `*_heading` field in the schema (about_heading, why_choose_heading, facts_heading, …), plus `faculty_members`, `faculty_intro`, `validity`, and the `certificate_heading`, are **completely unconsumed**. Section titles are hardcoded English strings in the templates. Confirmed by a repository-wide grep: those field names have **zero references** outside `source.json`.

---

## 1. University

Schema source fields (Type 1 example) → pipeline coverage.

| Field | Parser | Transformer | Editor | Renderer | HTML | Status |
|---|---|---|---|---|---|---|
| `_meta` (document_title, page_type, generated_by) | M | page_type only | — | — | — | 🟥 Dropped (page_type read in `main.py`; rest stored, unused) |
| `university_name` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `university_full_name` | M+L | ✅ | — | ✅ (hero H1) | ✅ | ✅ Flows |
| `hero_description` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `established_year` | M+L | ✅ | ✅ | ✅ | ✅ | ⚠️ Partial (template default `2010` if absent) |
| `naac_grade` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `ugc_approved` | M+L | ✅ (as `ugc_status`) | ✅ | ✅ | ✅ | ⚠️ Partial (alias-merged with `ugc_status`) |
| `mode_of_learning` | M+L | ✅ (hero pill) | — | ✅ | ✅ | ⚠️ Partial (not in editor; falls back to `mode`) |
| `starting_fee` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `num_programs` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `about_heading` | M | — | — | — | — | 🟥 Dropped (title hardcoded) |
| `why_choose_heading` | M | — | — | — | — | 🟥 Dropped |
| `facts_heading` | M | — | — | — | — | 🟥 Dropped |
| `accreditations_heading` | M | — | — | — | — | 🟥 Dropped |
| `programs_heading` | M | — | — | — | — | 🟥 Dropped |
| `admission_heading` | M | — | — | — | — | 🟥 Dropped |
| `emi_heading` | M | — | — | — | — | 🟥 Dropped |
| `exam_heading` | M | — | — | — | — | 🟥 Dropped |
| `faculty_heading` | M | — | — | — | — | 🟥 Dropped |
| `placement_heading` | M | — | — | — | — | 🟥 Dropped |
| `reviews_heading` | M | — | — | — | — | 🟥 Dropped |
| `faqs_heading` | M | — | — | — | — | 🟥 Dropped |
| `about_content` | M+L | ✅ (transformer) | ✅ | 🟥 **not in university.html** | ❌ | 🟥 Dropped (see Template Audit — `university.html` renders no About section) |
| `why_choose_content` | M+L | ✅ (transformer) | ✅ | 🟥 not rendered (hardcoded "Why us" copy instead) | ❌ | 🟥 Dropped |
| `admission_steps` | M+L | ✅ | ✅ | ✅ (parsed to steps) | ✅ | 🟧 Overwritten (hardcoded 4-step fallback) |
| `admission_fee_note` | M | ✅ | — | ⚠️ (transformer builds it, but university.html admission uses `steps` only) | ❌ | 🟥 Dropped in university.html |
| `emi_content` | M+L | ✅ (transformer) | ✅ | 🟥 not rendered (hardcoded "Fees & Financing" copy) | ❌ | 🟥 Dropped |
| `exam_content` | M+L | ✅ (transformer) | ✅ | 🟥 not rendered in university.html | ❌ | 🟥 Dropped |
| `faculty_intro` | M | — (knowledge map only) | — | — | — | 🟥 Dropped |
| `placement_content` | M+L | ✅ (transformer) | ✅ | 🟥 not rendered in university.html | ❌ | 🟥 Dropped |
| `facts` (repeater) | M+L | ✅ (transformer) | — | 🟥 not rendered (replaced by hardcoded `features`) | ❌ | 🟥 Dropped |
| `accreditations` (repeater) | M+L | ✅ (transformer) | — | 🟥 not rendered (accreditation strip hardcoded) | ❌ | 🟥 Dropped |
| `programs_table` (repeater) | M+L | ✅ (transformer) | — | ⚠️ (transformer builds it; university.html renders `programs` from workspace courses / hardcoded card) | ⚠️ | 🟥 Mostly dropped |
| `faculty_members` (repeater) | M | — | — | — | — | 🟥 Dropped (no consumer anywhere) |
| `reviews` (repeater) | M+L | ✅ | — | ✅ (as `testimonials`) | ✅ | 🟧 Overwritten (3 hardcoded named reviews if absent) |
| `faqs` (repeater) | M+L | ✅ | — | ✅ | ✅ | 🟧 Overwritten (5 hardcoded FAQs if absent) |
| `seo_title` | M | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `meta_description` | M | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `programs_intro` | M | ✅ (transformer) | — | ⚠️ (transformer only; university.html uses hardcoded intro) | ❌ | 🟥 Dropped in template |

---

## 2. Course

| Field | Parser | Transformer | Editor | Renderer | HTML | Status |
|---|---|---|---|---|---|---|
| `_meta` | M | page_type only | — | — | — | 🟥 Dropped |
| `program_name` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `university_name` | M+L | ✅ | — | ✅ | ✅ | ✅ Flows |
| `linked_university` | M | — | — | — | — | 🟥 Dropped (relations derived from workspace, not this field) |
| `hero_description` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `duration` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `mode` | M+L | ✅ | ✅ | ✅ | ✅ | ⚠️ Partial (defaults to `100% Online`) |
| `naac_grade` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `ugc_status` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `total_fee` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `num_specializations` | M | ✅ (stats) | ✅ | ✅ | ✅ | ✅ Flows |
| `about_heading` … `faqs_heading` (all 10 heading fields) | M | — | — | — | — | 🟥 Dropped (titles hardcoded in course.html) |
| `about_content` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows (falls back to `<p>hero_description</p>`) |
| `specializations_intro` | M | ✅ (transformer) | — | 🟥 (course.html hardcodes "Choose your specialization at the start of year two…") | ❌ | 🟥 Dropped in template |
| `eligibility_content` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `admission_steps` | M+L | ✅ | ✅ | ✅ | ✅ | 🟧 Overwritten (hardcoded 4-step fallback in transformer **and** engine) |
| `admission_fee_note` | M | ✅ | — | ⚠️ (built but course.html admission renders only `steps`) | ❌ | 🟥 Dropped in template |
| `syllabus_content` | M+L | ✅ | ✅ | ✅ | ✅ | 🟧 Overwritten (full hardcoded NMIMS MBA curriculum if absent; section always shown) |
| `placement_content` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `certificate_description` | M+L | ✅ | — (editor lists it under spec only) | ✅ | ✅ | ⚠️ Partial (not in course editor schema) |
| `validity` | M | — | — | — | — | 🟥 Dropped (no consumer) |
| `emi_amount` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `highlights` (repeater) | M+L | ✅ | — | ✅ | ✅ | ✅ Flows (hidden if absent) |
| `fee_plans` (repeater) | M+L | ✅ | — | ✅ | ✅ | 🟧 Overwritten (3 hardcoded plans if absent — engine `fee_list` fallback) |
| `job_profiles` (repeater) | M+L | ✅ | — | ✅ | ✅ | 🟧 Overwritten (6 hardcoded jobs+salaries if absent) |
| `reviews` (repeater) | M+L | ✅ | — | ✅ | ✅ | 🟧 Overwritten (3 hardcoded named reviews if absent) |
| `faqs` (repeater) | M+L | ✅ | — | ✅ | ✅ | 🟧 Overwritten (5 hardcoded FAQs if absent) |
| `seo_title` | M | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `meta_description` | M | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `starting_fee` | M | ✅ (via university card / listing) | ✅ | ⚠️ | ⚠️ | ⚠️ Partial (used for cross-page cards, not the course page itself) |
| `eligibility_summary` | M | ✅ (read by university/listing cards) | — | ⚠️ | ⚠️ | ⚠️ Partial (not shown on course page; feeds parent cards) |

---

## 3. Specialization

| Field | Parser | Transformer | Editor | Renderer | HTML | Status |
|---|---|---|---|---|---|---|
| `_meta` | M | page_type only | — | — | — | 🟥 Dropped |
| `spec_name` | M+L | ✅ | ✅ | ✅ | ✅ | ⚠️ Partial (rewritten by `normalize_specialization_name` + `clean_spec_name`) |
| `university_name` | M+L | ✅ | — | ✅ | ✅ | ✅ Flows |
| `linked_university` | M | — | — | — | — | 🟥 Dropped |
| `linked_course` | M | — | — | — | — | 🟥 Dropped (parent resolved via `parent_slug` heuristic, not this field) |
| `duration` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `mode` | M+L | ✅ | ✅ | ✅ | ✅ | ⚠️ Partial (defaults to `100% Online`) |
| `naac_grade` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `ugc_status` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `total_fee` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| all `*_heading` fields (about/highlights/eligibility/fee/other_specs/syllabus/exam/admission/placement/jobs/certificate/faqs) | M | — | — | — | — | 🟥 Dropped (titles hardcoded in specialization.html) |
| `about_content` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `eligibility_content` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `syllabus_content` | M+L | ✅ | ✅ | ✅ | ✅ | 🟧 Overwritten (hardcoded MBA curriculum if absent; section always shown) |
| `exam_content` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `admission_steps` | M+L | ✅ | ✅ | ✅ | ✅ | 🟧 Overwritten (hardcoded fallback in engine) |
| `admission_fee_note` | M | ✅ | — | ⚠️ (spec.html admission renders `steps` only) | ❌ | 🟥 Dropped in template |
| `placement_content` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `certificate_description` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `emi_amount` | M+L | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `highlights` (repeater) | M+L | ✅ | — | ✅ | ✅ | ✅ Flows |
| `other_specs` (repeater) | M | ✅ (fallback only) | — | ⚠️ | ⚠️ | ⚠️ Partial (schema value used only if no workspace siblings; else replaced by workspace data, then hardcoded 7-row fallback) |
| `job_profiles` (repeater) | M+L | ✅ | — | ✅ | ✅ | 🟧 Overwritten (6 hardcoded jobs if absent) |
| `reviews` (repeater) | M+L | ✅ | — | ✅ | ✅ | 🟧 Overwritten (3 hardcoded named reviews if absent) |
| `faqs` (repeater) | M+L | ✅ | — | ✅ | ✅ | 🟧 Overwritten (5 hardcoded FAQs if absent) |
| `seo_title` | M | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `meta_description` | M | ✅ | ✅ | ✅ | ✅ | ✅ Flows |
| `eligibility_summary` | M | ⚠️ (sibling cards) | — | ⚠️ | ⚠️ | ⚠️ Partial |

---

## Coverage summary

| Category | University | Course | Specialization |
|---|---|---|---|
| Scalar identity/stat fields flowing cleanly | ~8 | ~9 | ~9 |
| `*_heading` fields dropped | 12 | 10 | 12 |
| Content sections dropped by the **template** (parsed + transformed but not rendered) | 7 (`about`, `why_choose`, `emi`, `exam`, `placement`, `facts`, `accreditations`) | 1 (`admission_fee_note`) | 1 (`admission_fee_note`) |
| Repeaters overwritten by fabricated fallback | reviews, faqs | fee_plans, jobs, reviews, faqs, syllabus | jobs, reviews, faqs, syllabus |
| Fields with **no consumer at all** | faculty_members, faculty_intro | validity, linked_university | linked_university, linked_course |

**Net:** the schema's *scalar* contract (names, fees, approvals, SEO) flows. The schema's *editorial* contract (all section titles, faculty block, and — on the university page — the About/Why-Choose/EMI/Exam/Placement/Facts/Accreditations content) is largely **not honoured**: it is dropped or replaced by hardcoded template copy and fabricated fallbacks. This directly contradicts `.agent/RULES.md` R1 (never fabricate) and R2 (templates render only transformed data). See `PIPELINE_TRACE.md` and `HARDCODED_CONTENT_AUDIT.md`.
