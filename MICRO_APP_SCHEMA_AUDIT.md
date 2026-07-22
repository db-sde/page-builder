# DegreeBaba Micro App Schema Integration Audit

## 1. Executive Summary

**PASS** — the backend, workspace storage, editor, compiler, and templates are compatible with the documented DegreeBaba Content Publisher output for university, course, and specialization pages.

The project does not contain a database-backed content model. Its durable content store is each page's `source.json` record under `backend/workspaces/<university>/`; generated HTML is derived output. The audit therefore treats `source.json` as the “Database Storage” stage requested by the brief.

Verified flow:

`Micro App JSON → extract_metadata_from_json → adapt_schema → API/editor → source.json → transformer → renderer/template → compile/build`

Legend: **Stored** means the original field survives in `source.json`; **Rendered** means it directly affects visible HTML or metadata; **Relationship** means it drives workspace/parent resolution and is not printed as page content; **Tracking** means it is preserved for provenance but intentionally not printed.

## 2. Complete Mapping Matrix

All fields use the unfiltered `acf_data` API payload, are stored under `source.json.data`, and are editable through `FIELD_SCHEMA`/`Screen2Review`. The Backend/Output column records the field-specific mapping after those shared stages.

### University (39/39 fields)

| Micro App field(s) | Backend / API mapping | Editor | Template / rendered output | Status |
|---|---|---|---|---|
| `_meta.document_title`, `_meta.page_type`, `_meta.generated_by` | `_meta.page_type` selects the transformer; complete object is preserved | JSON object editor | Tracking only | OK |
| `university_name` | `UniversityTransformer.hero.title`, workspace identity | University Name | Hero, navigation, breadcrumbs, schemas | OK |
| `university_full_name` | `hero.full_name` | University Full Name | Hero H1 | OK |
| `hero_description` | `hero.description` | Hero Description | Hero copy and Course schema description fallback | OK |
| `established_year`, `naac_grade`, `ugc_approved`, `mode_of_learning`, `starting_fee`, `num_programs` | Stats/pills; `ugc_approved` is canonical for university aliases | Individual scalar inputs | Hero pills/stats/accreditation strip | OK |
| `about_heading`, `why_choose_heading`, `facts_heading`, `accreditations_heading`, `programs_heading`, `admission_heading`, `emi_heading`, `exam_heading`, `faculty_heading`, `placement_heading`, `reviews_heading`, `faqs_heading` | `context.headings.*` with existing template text as fallback | Individual heading inputs | Corresponding section H2 | OK |
| `about_content`, `why_choose_content` | `about`, `why_choose` | HTML textareas | About and Why Choose sections | OK |
| `admission_steps`, `admission_fee_note` | Parsed `admission` steps plus fee note | HTML/scalar editors | Admission cards and note | OK |
| `emi_content`, `exam_content`, `placement_content` | `emi`, `exam`, `placement` | HTML textareas | Conditional EMI, exam, and placement sections | OK |
| `faculty_intro` | `faculty_intro` | Scalar editor | Faculty section introduction | OK |
| `facts[].fact_title`, `facts[].fact_description` | `facts` repeater | JSON repeater editor | Fact cards | OK |
| `accreditations[].body_name`, `.body_descriptor`, `.body_detail` | `accreditations` repeater | JSON repeater editor | Accreditation strip and cards | OK |
| `programs_table[].program_name`, `.program_fee`, `.program_eligibility` | Program-card fallback when workspace courses do not exist | JSON repeater editor | Programs grid | OK |
| `faculty_members[].member_name`, `.member_program`, `.member_designation`, `.member_qualification` | `faculty_members` repeater | JSON repeater editor | Faculty cards | OK |
| `reviews[].review_text`, `.reviewer_name`, `.reviewer_label` | Reviewer name and role retained separately, then formatted | JSON repeater editor | Testimonials | OK |
| `faqs[].question`, `.answer` | FAQ normalization | JSON repeater editor | FAQ accordion | OK |
| `seo_title`, `meta_description` | Renderer SEO context | SEO inputs | `<title>`, description, OG/Twitter metadata | OK |
| `programs_intro` | `programs_intro` | Scalar editor | Programs section introduction | OK |

### Course (41/41 fields)

| Micro App field(s) | Backend / API mapping | Editor | Template / rendered output | Status |
|---|---|---|---|---|
| `_meta.document_title`, `_meta.page_type`, `_meta.generated_by` | Transformer selection plus preserved tracking object | JSON object editor | Tracking only | OK |
| `program_name` | `hero.title`, page name and slug source | Program Name | Hero, breadcrumbs, schemas, listings | OK |
| `university_name`, `linked_university` | Name is rendered; relationship reuses selected workspace or a valid linked slug | Relationship fields | University labels/provider schema; link itself is not printed | OK — Relationship |
| `hero_description`, `duration`, `mode` | Hero description/pills/stats | Scalar inputs | Hero and stats | OK |
| `naac_grade`, `ugc_status` | Accreditation context | Scalar inputs | Badge, stats, accreditation cards | OK |
| `total_fee`, `num_specializations`, `starting_fee` | Fee/stats/listing context; total fee can infer a one-row fee plan | Scalar inputs | Stats, fee/sticky sections and listings | OK |
| `about_heading`, `highlights_heading`, `accreditations_heading`, `specializations_heading`, `fee_heading`, `eligibility_heading`, `admission_heading`, `syllabus_heading`, `placement_heading`, `jobs_heading`, `faqs_heading` | `context.headings.*` | Individual heading inputs | Corresponding section H2 | OK |
| `about_content` | `about`; hero description is a safe fallback | HTML textarea | About section | OK |
| `specializations_intro` | `specializations.intro` | Scalar editor | Specializations section even before child pages exist | OK |
| `eligibility_content`, `eligibility_summary` | Full content plus summary; summary can safely supply missing content | HTML/scalar editors | Eligibility section and listings | OK |
| `admission_steps`, `admission_fee_note` | Parsed steps plus note | HTML/scalar editors | Admission section | OK |
| `syllabus_content` | Semester parser with raw-HTML fallback | HTML textarea | Syllabus grid or original content | OK |
| `placement_content`, `certificate_description`, `validity` | `placement.content`, `.certificate`, `.validity` | HTML/scalar editors | Placement/certificate section | OK |
| `emi_amount` | Fee note and sticky bar | Scalar editor | Fee/sticky content | OK |
| `highlights[].highlight_title`, `.highlight_description` | Highlight normalization | JSON repeater editor | Highlight cards | OK |
| `fee_plans[].plan_name`, `.plan_amount`, `.plan_total` | Fee row normalization | JSON repeater editor | Fee table | OK |
| `job_profiles[].job_title`, `.avg_salary` | Job normalization | JSON repeater editor | Job cards | OK |
| `reviews[].review_text`, `.reviewer_name`, `.reviewer_label` | Name/role-preserving review normalization | JSON repeater editor | Reviews | OK |
| `faqs[].question`, `.answer` | FAQ normalization and JSON-LD source | JSON repeater editor | FAQ accordion and FAQ schema | OK |
| `seo_title`, `meta_description` | Renderer SEO context | SEO inputs | Title, description, OG/Twitter metadata | OK |

### Specialization (39/39 fields)

| Micro App field(s) | Backend / API mapping | Editor | Template / rendered output | Status |
|---|---|---|---|---|
| `_meta.document_title`, `_meta.page_type`, `_meta.generated_by` | Transformer selection plus preserved tracking object | JSON object editor | Tracking only | OK |
| `spec_name` | Clean-name guard, `hero.title`, page slug source | Specialization Name | Hero, breadcrumbs, schemas, listings | OK |
| `university_name`, `linked_university` | Name is rendered; workspace relationship is reused/inferred | Relationship fields | University labels/provider schema | OK — Relationship |
| `linked_course` | Exact existing slug/dict slug is reused; otherwise heuristic/editor assignment supplies `parent_slug` | Field plus dedicated parent-course panel | Parent breadcrumb, siblings and course association | OK — Relationship |
| `duration`, `mode`, `naac_grade`, `ugc_status`, `total_fee` | Hero/stats/fee context | Scalar inputs | Hero, stats, fee and sticky content | OK |
| `about_heading`, `highlights_heading`, `eligibility_heading`, `fee_heading`, `other_specs_heading`, `syllabus_heading`, `exam_heading`, `admission_heading`, `placement_heading`, `jobs_heading`, `certificate_heading`, `faqs_heading` | `context.headings.*` | Individual heading inputs | Corresponding section/subsection headings | OK |
| `about_content` | `about` | HTML textarea | About section | OK |
| `eligibility_content`, `eligibility_summary` | Full content plus summary fallback | HTML/scalar editors | Eligibility section | OK |
| `syllabus_content` | Semester parser with raw-HTML fallback | HTML textarea | Syllabus grid or original content | OK |
| `exam_content` | `exam` | HTML textarea | Exam section | OK |
| `admission_steps`, `admission_fee_note` | Parsed steps plus note | HTML/scalar editors | Admission section | OK |
| `placement_content`, `certificate_description` | Placement/certificate context | HTML textareas | Placement and certificate content | OK |
| `emi_amount` | Fee note/sticky bar | Scalar editor | Fee and sticky content | OK |
| `highlights[].highlight_title`, `.highlight_description` | Highlight normalization | JSON repeater editor | Highlight cards | OK |
| `other_specs[].other_spec_name`, `.other_spec_fee` | Raw fallback when workspace siblings do not exist; workspace siblings take precedence | JSON repeater editor | Other-specializations table | OK |
| `job_profiles[].job_title`, `.avg_salary` | Job normalization | JSON repeater editor | Job cards | OK |
| `reviews[].review_text`, `.reviewer_name`, `.reviewer_label` | Name/role-preserving normalization | JSON repeater editor | Reviews | OK |
| `faqs[].question`, `.answer` | FAQ normalization and JSON-LD source | JSON repeater editor | FAQ accordion and FAQ schema | OK |
| `seo_title`, `meta_description` | Renderer SEO context | SEO inputs | Title, description, OG/Twitter metadata | OK |

## 3. Proven Issues and Fixes

| Issue | Root cause | Fix | Proof |
|---|---|---|---|
| University `ugc_approved` disappeared on a fresh preview | Transformer requested only `ugc_status` before knowledge storage existed | University now resolves the contract field first; aliases normalize centrally | Exact university payload renders `UGC-DEB Approved` |
| KV aliases could create competing fields | Adapter did not canonicalize `ugc_approved → ugc_status` or `mode_of_learning → mode` for course/spec | Canonical page-type alias mapping removes the alias key | Assertions confirm one canonical key and no duplicate |
| `_meta.page_type` was ignored by pasted JSON | UI/backend only checked a top-level `page_type` | Both now consume `_meta.page_type` while preserving `_meta` | All three exact envelopes select the correct transformer |
| Heading fields were stored but ignored | Templates hardcoded section titles | Transformers expose `headings`; templates use them with backward-compatible defaults | Custom headings from all three examples appear in HTML |
| Repeaters were hidden in the editor | Schema omitted them and object/array values were skipped | Complete field schema plus JSON textarea editing | UI contract check reports 39/39, 41/41 and 39/39 fields |
| `faculty_members` was never rendered | No transformer/template mapping | Added faculty context and conditional faculty cards | Exact faculty member appears in university output |
| `reviewer_name` was lost | Review formatter treated `reviewer_label` as the name | Name and label are retained as name/role | Rahul Verma, Vikram Sen and Priya Sharma survive build output |
| `other_spec_fee` was dropped | Renderer read only the legacy `fee` key | Added documented `other_spec_fee` mapping | Digital Marketing and its formatted fee render |
| Simple syllabus HTML produced an empty section | Semester parser required headings/list items | Templates fall back to original `syllabus_content` | Course and specialization examples render their prose syllabus |
| Clean specialization names could be erased | Parent token stripping removed legitimate words shared with the parent title | Skip prefix stripping when the name has no course/program prefix | `Banking & Insurance` saves and publishes unchanged |
| Missing optional arrays produced invented demo content | Renderer supplied fake jobs, reviews, FAQs, syllabus, fee plans and related lists | Removed demo fallbacks; sections now hide when optional data is absent | Minimal-payload assertion contains none of the former demo values |
| Publish errors were generic/one-at-a-time | Image-only validation raised a single string | Backend returns one `Missing required fields` object with exact field names; UI formats it | Missing specialization relation/image returns `linked_course`, `hero_image_url` |

## 4. Required, Inferred, and Optional Data

### Required content

- University: `university_name`
- Course: `program_name`, `university_name`
- Specialization: `spec_name`, `university_name`, and a resolved parent course
- Blog compatibility path: `title`, `content_html`
- All publishable content pages: `university_slug` and `hero_image_url`

`page_type` and `slug` are operationally required, but should not normally be requested because they are derived from `_meta`/field shape and the page name.

### User-required only when inference fails

- `hero_image_url`: not present in the Micro App contract and cannot be derived safely.
- Specialization parent course: requested only when `linked_course`, an existing relationship, and slug heuristics cannot resolve it.
- Workspace branding/domain settings: outside page content and cannot be derived from the publisher payload.

The course certificate image remains optional because the template already supports a placeholder and the Micro App contract does not provide it.

### Automatically inferred/reused

- `page_type` from `_meta.page_type`, then field shape.
- `slug` from `university_name`, `program_name`, `spec_name`, or title.
- `university_slug` from the selected workspace, valid `linked_university.slug`, or university name.
- Missing page `university_name` from the selected workspace in the editor/compiler.
- Canonical aliases: `ugc_approved/ugc_status` and `mode_of_learning/mode` according to page type.
- Course `program_name` from legacy `course_name`.
- Course/specialization `eligibility_content` from `eligibility_summary` when full content is absent.
- Course `about_content` from `hero_description` when absent.
- A single fee row from `total_fee` when `fee_plans` is absent.
- Specialization parent from an exact linked course or workspace heuristic before asking the user.

### Optional

Every remaining publisher field is optional. Missing headings use the existing template heading; missing content/repeaters hide their section; missing SEO overrides use existing renderer fallbacks where available. Optional fields do not block publishing.

## 5. Verification

- Exact schema storage: university **39/39**, course **41/41**, specialization **39/39** fields retained.
- Exact schema rendering: all three page types rendered without missing-template or missing-key errors.
- Repeater checks: facts, accreditations, programs, faculty, highlights, fee plans, other specs, jobs, reviews, and FAQs reached built HTML.
- Isolated publish test: **6 pages compiled, 0 failed; 6 routes built, 0 failed** (three content pages plus three system listings).
- Existing NMIMS workspace: **25 pages compiled, 0 failed; 25 routes built, 0 failed**.
- Frontend schema coverage: **39/39 university, 41/41 course, 39/39 specialization** fields.
- Frontend ESLint: passed.
- Frontend production build: passed.
- Python syntax/import checks: passed.

## 6. Final Verdict

The backend is fully compatible with the documented Micro App schema. No documented field is dropped from persistence or hidden from the editor. Fields intended for presentation now affect rendered output; relationship and tracking fields are preserved and used operationally without being printed as page copy.

If a future Micro App version emits opaque numeric relationship IDs rather than `null`, a slug, or an object containing `slug`, that identifier format will need a documented lookup source. The current contract does not define such an ID format, so no speculative resolver was introduced.
