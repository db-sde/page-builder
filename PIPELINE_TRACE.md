# PIPELINE_TRACE.md

**Audit date:** 2026-07-24 · Read-only.

Field-by-field trace through every layer:

```
DOCX → Micro App (canonical) / local extractor (fallback)
     → adapter.merge_micro_and_local + adapt_and_validate
     → main.extract_metadata_from_json
     → core.router.normalize_value
     → transformers/<type>.transform()
     → renderer.engine.render_resolved()  ← second, heavier transform
     → templates/<type>.html
     → workspace/builder.py → build/*.html
```

---

## Stage map (what each layer actually does)

| Stage | File | Responsibility as-built |
|---|---|---|
| Parse (canonical) | external `MICRO_APP_URL` | Emits the full schema JSON (all `*_heading`, repeaters, scalars). |
| Parse (fallback) | `ingestion/parser.py` + `ingestion/extractor.py` | Local DOCX→blocks→ACF. Covers a subset; no `*_heading`, no faculty. |
| Merge | `ingestion/adapter.py::merge_micro_and_local` | Micro wins per key; local fills empty keys. |
| Adapt/validate | `ingestion/adapter.py::adapt_and_validate` | Renames (`course_name`→`program_name`, `fee`→`total_fee`, `fees`→`total_fee`, `university_full_name`→`university_name`); coerces year/num_programs/credits; length-warns scalars. |
| Metadata | `main.py::extract_metadata_from_json` | Derives `page_type`, `slug`, `university_slug`, `parent_slug`; normalises spec names. |
| Normalise | `core/router.py::normalize_value` | Recursively maps `NA/N-A/null/none/dashes` → `None`. |
| Transform | `transformers/*.py` | Builds hero/stats/rail/section dicts; **injects hardcoded fallbacks** (admission steps, accreditation prose, mode). |
| Render | `renderer/engine.py::render_resolved` | Rebuilds most collections into `*_json` template vars and **injects fabricated fallbacks** when a collection is empty. This is where most drift happens. |
| Template | `templates/*.html` | Hardcoded section titles + hardcoded marketing copy; renders the engine collections. |
| Build | `workspace/builder.py` | Routes, sitemap, robots, WebP, link rewrite, GA (nmims-2 only). |

> **Key structural fact:** `renderer/engine.py` is a *second transformer*. The per-type transformer's output for repeaters (`jobs`, `reviews`, `faqs`, `fees`, `syllabus`, `other_specs`, `specs`, `programs`, `features`, `recruiters`, `financing`, `banks`) is **discarded and rebuilt** by `render_resolved`, which supplies fabricated defaults whenever the source is empty. So `{% if jobs %}` etc. in templates are effectively *always true*.

---

## Traces — representative fields

### `naac_grade` (all types) — ✅ clean
Micro `naac_grade` → adapter (length-validated) → normalize_value → `transformer.resolve("naac_grade")` (Page→Knowledge→default chain) → hero badge / stats / accreditation strip → HTML. Also written to `university_knowledge.json` `approvals.naac_grade` for cross-page reuse. **No loss.**

### `ugc_approved` / `ugc_status` — ⚠️ renamed & merged
University schema uses `ugc_approved`; course/spec use `ugc_status`. `knowledge.FIELD_MAPPING` maps **both** to `approvals.ugc_status`. `core/router` normalize + REG-002 fix collapse them. University transformer exposes it back to the template as `ugc_approved`; course/spec as `ugc_status` (prefixed `UGC ` if the value doesn't already contain "ugc"). Single badge — no duplicate. **Renamed but consistent.**

### `about_content` (university) — 🟥 lost at the template
Micro `about_content` → adapter → `UniversityTransformer` sets `"about": about_content` in its context. **`university.html` has no About section** — it renders a hardcoded "Why {{ university_name }} Online / A legacy of excellence…" block and a `features` grid instead. The transformed value is never emitted. Same fate for `why_choose_content`, `emi_content`, `exam_content`, `placement_content`, `facts`, `accreditations`.

### `about_content` (course/spec) — ✅ flows
Course/spec templates *do* have `{% if about %}` sections, so the value flows. (The heading "About the {{ hero.title }}" is hardcoded, ignoring `about_heading`.)

### `admission_steps` (course) — 🟧 overwritten
Two fabricated fallbacks stack:
1. `CourseTransformer` defaults `admission_steps` to a hardcoded 4-paragraph "Step 1…4" block when absent (`transformers/course.py:41`).
2. `render_resolved` parses steps via `parse_admission_html`; if still empty, injects a 4-step hardcoded list (`engine.py:809`).
Result: every course/spec page shows admission steps even when the DOCX has none.

### `syllabus_content` (course/spec) — 🟧 overwritten & always shown
Transformer passes the HTML through. `engine.parse_syllabus_html`; if empty → **hardcoded NMIMS 2-year MBA curriculum** (`engine.py:908`). The syllabus `<section>` in course.html/spec.html has **no `{% if %}` guard**, so it always renders — real or fabricated.

### `job_profiles`, `reviews`, `faqs`, `fee_plans` — 🟧 overwritten
Transformer sets them (or `None`). `render_resolved` rebuilds each; on empty it substitutes hardcoded data: 6 named jobs w/ salaries (`engine.py:836`), 3 named student reviews (`engine.py:866`), 5 FAQs (`engine.py:895`), 3 fee plans (`engine.py:794`). Then reassigns `ctx["jobs"|"reviews"|"faqs"|"fees"]`, so template guards pass.

### `facts` / `accreditations` (university) — 🟥 dropped
`UniversityTransformer` builds both. `university.html` renders neither: the "Recognised & Accredited" strip is hardcoded (`AIU Member`, `NIRF #24`, `WES Recognised`), and the "Why us" area uses the hardcoded/knowledge `features` list. Transformer output unused.

### `faculty_members` / `faculty_intro` (university) — 🟥 fully dropped
Schema provides a faculty repeater and intro. **No transformer, engine path, or template references them.** `faculty_intro` exists only as a key in `knowledge.FIELD_MAPPING` (stored, never read back for rendering). The university page has no faculty section at all.

### `other_specs` (specialization) — ⚠️ replaced
Schema `other_specs` is used **only** as a last-resort fallback in `engine.py:952`. Normally the "Compare Other Specializations" table is built from `_workspace_sibling_specs` (compiler-injected). If there are no siblings *and* no `other_specs`, a **hardcoded 7-row MBA table** (`engine.py:965`) is emitted.

### `*_heading` (all types) — 🟥 dropped
Every schema heading field (about_heading, why_choose_heading, facts_heading, accreditations_heading, programs_heading, admission_heading, emi_heading, exam_heading, faculty_heading, placement_heading, reviews_heading, faqs_heading, highlights_heading, specializations_heading, fee_heading, eligibility_heading, syllabus_heading, jobs_heading, certificate_heading, other_specs_heading, exam_heading) has **zero references** anywhere in `transformers/`, `renderer/`, or `templates/`. Section titles are hardcoded English constants inside each template.

### `seo_title` / `meta_description` — ✅ clean
Transformer → template `<title>`/`<meta>` → `render_resolved` post-processor also injects OG/Twitter tags from the same values → HTML. `_build_structured_data` adds JSON-LD (BreadcrumbList always; Organization for university; Course+Offer for course/spec using `_schema_price`, no invented price; FAQPage from the *rendered* faqs — **note:** because faqs are fabricated on fallback, the FAQPage JSON-LD can also carry fabricated Q&A).

### `slug` / `university_slug` — ⚠️ derived, leak risk
Derived in `extract_metadata_from_json`. `normalize_public_slug` strips numeric workspace suffixes (`nmims-2-…`→`…`) for public routes. **Leak:** `specialization.html:429` falls back to `admissions@{{ university_slug }}online.edu` — puts the internal slug in a user-facing email (violates R6). `engine.py:502` defaults `uni_slug` to `"nmims"`.

---

## Mismatch ledger

| Field(s) | Mismatch type | Where |
|---|---|---|
| `course_name`→`program_name`, `fee`/`fees`→`total_fee`, `university_full_name`→`university_name` | Renamed | `adapter.adapt_schema`, transformers |
| `ugc_approved`↔`ugc_status` | Merged (alias) | `knowledge.FIELD_MAPPING`, `router.normalize_value` |
| `about/why_choose/emi/exam/placement_content`, `facts`, `accreditations` (university) | Lost at template | `university.html` |
| `admission_fee_note` (all) | Lost at template | uni/course/spec templates render `steps` only |
| all `*_heading` | Ignored | templates hardcode titles |
| `faculty_members`, `faculty_intro`, `validity`, `linked_university`, `linked_course` | Ignored (no consumer) | whole pipeline |
| `job_profiles`, `reviews`, `faqs`, `fee_plans`, `syllabus_content` | Overwritten on empty | `engine.py` fallbacks |
| `other_specs` | Replaced by workspace siblings, then hardcoded | `engine.py` |
| `spec_name` | Transformed (regex stripping) | `normalize_specialization_name`, `clean_spec_name` |
