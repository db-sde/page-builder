# HARDCODED_CONTENT_AUDIT.md

**Audit date:** 2026-07-24 · Read-only. Nothing was changed.

Every hardcoded / fabricated value found, with file:line, categorised by severity.
"Should this be hardcoded?" answers whether the value is legitimately a template constant
(YES — e.g. brand-neutral CTA verbs, layout colours) or is standing in for data that must come
from the schema (NO).

Severity key:
- 🟥 **CRITICAL** — fabricated *facts* presented as real (reviews, salaries, recruiters, rankings, curriculum, accreditations). Can mislead users and pollutes JSON-LD/SEO. Violates `RULES.md` R1.
- 🟧 **HIGH** — hardcoded content that silently overrides or hides schema data. Violates R1/R2.
- 🟨 **MEDIUM** — tenant-specific values or slug/brand leaks in shared paths. Violates R6/R16.
- ⬜ **LOW** — legitimate layout constants, neutral placeholders, and CTA copy.

---

## 🟥 CRITICAL — fabricated facts

| # | File:Line | Value | Should be hardcoded? |
|---|---|---|---|
| C1 | `renderer/engine.py:866-871` | 3 fake student reviews with **real-looking names** ("Sneha Kulkarni", "Rohit Verma", "Deepa Krishnan") shown when `reviews` is empty | **NO** — fabricated testimonials; also feed `testimonials` on the homepage |
| C2 | `renderer/engine.py:836-844` | 6 fake job profiles + salaries ("Marketing Manager ₹12.5 LPA", …) shown when `job_profiles` empty | **NO** |
| C3 | `renderer/engine.py:895-902` | 5 fabricated FAQs (answers assert UGC equivalence, exam weighting, refund policy) when `faqs` empty — **also emitted as `FAQPage` JSON-LD** | **NO** |
| C4 | `renderer/engine.py:908-923` | Full hardcoded 2-year MBA curriculum (subject names) when `syllabus_content` empty; section is unconditionally rendered | **NO** |
| C5 | `renderer/engine.py:1008` | Hardcoded recruiter logos `["Tata","Indiamart","Wockhardt","Zalaris","Milkbasket","Shopx"]` (NMIMS's real recruiters) | **NO** |
| C6 | `templates/university.html:84` | `NIRF #24` hardcoded into the hero accreditation badge regardless of actual rank | **NO** |
| C7 | `templates/university.html:128` | Accreditation strip hardcodes `AIU Member`, `NIRF #24 Management`, `WES Recognised` | **NO** |
| C8 | `templates/course.html:184-193` (transformer `transformers/course.py:184`) | Accreditation card prose: *"among India's highest-rated private universities"*, *"Offered under UGC (ODL & Online Programmes) Regulations, 2020 — fully valid for jobs and higher studies"* | **NO** — invented claims attached to any NAAC/UGC value |
| C9 | `renderer/engine.py:965-973` | Hardcoded 7-row "other specializations" comparison table with fake fees | **NO** |
| C10 | `renderer/engine.py:1156-1160` | Hardcoded demo blog posts (titles, dates) when workspace has no blogs | **NO** (partially guarded — only if no real blogs; still fabricated) |
| C11 | `templates/specialization.html:115-116` | Hero stat-card default `₹14.2L` / "Avg. salary after specialization" | **NO** — fabricated salary |

---

## 🟧 HIGH — hardcoded content overriding / hiding schema

| # | File:Line | Value | Should be hardcoded? |
|---|---|---|---|
| H1 | `transformers/course.py:41-47` | Hardcoded 4-step admission process fallback | **NO** — use schema `admission_steps`, hide if empty |
| H2 | `renderer/engine.py:809-814` | Second hardcoded 4-step admission fallback | **NO** |
| H3 | `renderer/engine.py:794-799` | Hardcoded 3-row fee plan table (`₹50,000/sem`, `₹2,00,000`, …) when `fee_plans` empty | **NO** |
| H4 | `transformers/base.py:123` | EMI note hardcodes *"…lets you start with just ₹50,000."* | **NO** |
| H5 | `renderer/engine.py:998-1003` | Hardcoded `features` list ("120+ Expert Faculty", "₹8,334/month") | **NO** |
| H6 | `renderer/engine.py:1025-1029` | Hardcoded `financing` list ("20% off Defence scholarship", …) | **NO** |
| H7 | `renderer/engine.py:1034` | Hardcoded `banks` list `['HDFC','ICICI','Axis','Citi',…]` | **NO** |
| H8 | `templates/course.html:199` | Hardcoded paragraph "Choose your specialization at the start of year two. Each track replaces semester 3 and 4 electives…" (ignores `specializations_intro`) | **NO** |
| H9 | `templates/university.html:194-196` | Hardcoded "A legacy of excellence, reimagined…" + "Live weekend classes… one of India's most respected management institutions." (replaces `why_choose_content`) | **NO** |
| H10 | `templates/university.html:93` | `established_year | default('2010')` | **NO** — fabricated year |
| H11 | `templates/university.html:97` | Hero third stat hardcodes `UGC / Approved Degrees` | ⚠️ borderline (label ok, but always shown) |
| H12 | `templates/specialization.html:87` | Hero badge default `Most Popular Specialization` | **NO** — unverifiable claim |
| H13 | `transformers/specialization.py:87` | Same badge injected by transformer | **NO** |
| H14 | `templates/university.html:137-138,174-175,214-215,233-234,273` | Hardcoded section eyebrows/headings/subtitles ("Explore Our Online Programs", "A simple step-by-step admission process", "Learn now, pay your way", "Careers, accelerated", …) — ignore all `*_heading` schema fields | **NO** (headings should come from schema or be neutral) |
| H15 | `templates/course.html:120` | "Highest Category Rating" caption under hero stat-card | **NO** |
| H16 | `templates/course.html:274` & `templates/specialization.html:236` | Syllabus `<section>` has no `{% if %}` guard — always renders (real or fabricated C4) | **NO** — must hide when no syllabus |

---

## 🟨 MEDIUM — tenant leaks / brand defaults in shared paths

| # | File:Line | Value | Should be hardcoded? |
|---|---|---|---|
| M1 | `templates/specialization.html:429` | Fallback email `admissions@{{ university_slug }}online.edu` — **leaks internal workspace slug into UI** (violates R6) | **NO** |
| M2 | `renderer/engine.py:502` | `uni_slug = resolved.get("university_slug") or "nmims"` — NMIMS default tenant | **NO** |
| M3 | `renderer/engine.py:1048` | `if uni_slug == "nmims-2" and "emba" in name_lower:` — tenant-specific level logic | **NO** |
| M4 | `workspace/builder.py:231-239` | GA tag + ID `G-B2N0SZPDFD` injected only for `nmims-2` | **NO** — should read `metadata.json["ga_id"]` (already a known task) |
| M5 | `templates/course.html:465` | Footer copyright default `© 2026 NMIMS Online…` | **NO** — should use `university_name` |
| M6 | `templates/blog.html:229` | Footer copyright default `© 2026 NMIMS Online…` | **NO** |
| M7 | `core/site_config.py:11-42` | `SITE_CONFIG` holds NMIMS contact + footer program links (`/nmims-online-mba`, WhatsApp, email, address) | ⚠️ intentional for the `nmims` tenant only (guarded by slug check), but a live tenant-specific block in shared code |
| M8 | `templates/blog_listing.html:124` | "EMI from ₹8,334/month · Scholarships available." | **NO** |
| M9 | `templates/university.html:313` | CTA band EMI `default('₹8,334/month')` | **NO** |
| M10 | `templates/course.html:473` & `specialization.html:449` | Sticky bar `default('₹2,00,000')` / `default('₹8,334/mo')` | **NO** |
| M11 | `frontend/src/fieldSchema.js:76-77` | Blog author default "Krishna Porwal" / role "content writer" (documented editor fallbacks) | **NO** — a real person's name as default |
| M12 | `renderer/engine.py:583-584` | `course_href`/`spec_href` built from synthetic `{uni_slug}-online-mba` / `{uni_slug}-mba-marketing` slugs | ⚠️ MBA/marketing assumption |
| M13 | `transformers/specialization.py:22` | Parent fallback `f"{university_name} Online MBA"` — assumes MBA | **NO** (generic-platform assumption) |

---

## ⬜ LOW — legitimate constants & neutral placeholders

| # | File:Line | Value | Should be hardcoded? |
|---|---|---|---|
| L1 | all templates | Layout colours (`#6B4FC9`, `#FF5C35`, `#F6F4FB`, …), inline styles, fonts | **YES** — design system constants (though a per-tenant theme colour would be more generic) |
| L2 | `transformers/*` & templates | Hero CTA verbs ("Download Brochure", "Enquire Now", "Apply Now", "WhatsApp Us") | **YES** — generic CTA copy |
| L3 | `templates/programs_listing.html:97-101` | Neutral card defaults `2 Years`, `100% Online`, `Contact for fee` | **YES** — brand-neutral placeholders |
| L4 | university/course/spec templates | `[…campus / learner photo — 500×430 —]` placeholder captions when image absent | **YES** — dev placeholder (though builder blocks missing required images) |
| L5 | `*.py` | `mode` default `"100% Online"`, `duration` default `"2 Years"` | ⚠️ acceptable as sane defaults; flagged because they still "invent" content per R1 |
| L6 | `templates/*` | `topbar_text | default('Admissions open · Limited seats')` | **YES** — generic |
| L7 | `renderer/engine.py:1131` | Blog category labels `['All','Career','Admissions','Guide','Finance','Student Life']` | ⚠️ UI filter labels, acceptable |

---

## Rollup

| Severity | Count |
|---|---|
| 🟥 Critical (fabricated facts) | 11 |
| 🟧 High (overrides/hides schema) | 16 |
| 🟨 Medium (tenant/brand/slug leaks) | 13 |
| ⬜ Low (legitimate/neutral) | 7 |

**Most important:** the CRITICAL and HIGH rows mean a page compiled from a *sparse but valid* DOCX still ships fake reviews, fake salaries, fake recruiters, a fake syllabus, invented accreditation claims, and hardcoded FAQs (which also enter `FAQPage` JSON-LD). The pipeline's real behaviour is the opposite of `.agent/PROJECT.md`'s "Data-first, never invented" claim and `RULES.md` R1/R2. This is architecture drift the `.agent` docs did not record — now captured in `.agent/audits/latest.md` and `.agent/memory/regressions.md` (REG-010).
