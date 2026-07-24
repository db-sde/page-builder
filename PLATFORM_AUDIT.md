# PLATFORM_AUDIT.md

**Audit date:** 2026-07-24 · Read-only. No code, config, or behaviour changed.
Companion reports: `SCHEMA_COVERAGE_REPORT.md`, `PIPELINE_TRACE.md`, `HARDCODED_CONTENT_AUDIT.md`, `TEMPLATE_AUDIT.md`.

---

## Executive summary

The **plumbing** is genuinely good: a deterministic DOCX→JSON→HTML pipeline, a two-pass compiler that resolves relationships cleanly, canonical URL/route helpers, WebP optimisation, image-validation gating, correct multi-tenant workspace isolation, and solid SEO scaffolding (canonical, OG, sitemap w/ lastmod, robots, JSON-LD).

The **content contract** is broken. The single most important finding of this audit is that the platform does **not** honour its own stated rule "Data-first, never invented." The renderer (`renderer/engine.py`) and the three detail templates inject a large body of **fabricated fallback content** (fake reviews with names, fake job salaries, fake recruiters, a fake syllabus, invented accreditation claims, hardcoded FAQs) whenever schema fields are absent, and the **university template discards most of the parsed university content** in favour of hardcoded marketing copy. The new Micro-App schema's section headings (`*_heading`) and the entire faculty block are **completely unconsumed**.

Verdict: **schema-ready for scalar/identity data; NOT schema-faithful for editorial content.** The gap is not in parsing — the Micro-App emits the data correctly — it is in the transform/render/template layers throwing it away or overriding it.

---

## Architecture — strengths

1. **Clean ingestion contract.** Micro-first merge + local fallback (`adapter.merge_micro_and_local`), typed blocks, fuzzy heading anchors, table recovery (REG-004). Alias/rename logic is centralised.
2. **Two-pass compiler** (ADR-003) correctly decouples indexing from rendering; any upload order works; parent/sibling/workspace relationships are injected at compile time.
3. **Canonical helpers** (`core/utils.build_public_route/url`, `normalize_public_slug`) are the single source of truth for URLs — used by renderer *and* builder. Public slugs strip internal `-N` workspace suffixes.
4. **Multi-tenant isolation** works: `get_site_config` returns NMIMS's block only for `slug=="nmims"`; every other tenant gets neutral defaults + `metadata.json` overrides (REG-006).
5. **Build safety:** `_validate_pages` blocks builds on missing hero/certificate images and broken `parent_slug` (REG-005); `threading.Lock` serialises builds.
6. **SEO scaffolding** is real: canonical/OG/Twitter post-processor, JSON-LD (BreadcrumbList/Organization/Course+Offer/FAQPage), `_schema_price` reads price without inventing, sitemap has per-page `lastmod`, robots points at sitemap.
7. **Knowledge base** (ADR-004) with Page→Knowledge→default resolution and conflict logging is a sound way to share NAAC/UGC/established facts across pages.
8. **Listing pages are correctly data-driven** (REG-001 fixed) — empty workspaces render empty states, not fake cards.

## Architecture — weaknesses

1. **Fabricated content pervades the render layer.** See `HARDCODED_CONTENT_AUDIT.md` (11 critical + 16 high). This is a correctness *and* a legal/SEO risk (fake reviews and FAQs are emitted into structured data).
2. **`renderer/engine.py` is a shadow second transformer.** It rebuilds nearly every collection the per-type transformers already built, then discards the transformer output. Two overlapping transform layers = double the surface for drift, and the fabricated fallbacks live here.
3. **University template ignores parsed content.** `about/why_choose/emi/exam/placement/facts/accreditations/faculty` are transformed then dropped.
4. **Schema headings unused.** Every `*_heading` is dead on arrival; titles are hardcoded.
5. **Faculty is fully unimplemented** despite being in the schema.
6. **Two very large files** (`main.py` ~1774 lines, `engine.py` 1380 lines) mix many concerns; no unit tests anywhere in the ingestion/compile/build path (`test_spec.py` is minimal).
7. **`standalone` mode is inconsistent** — header/footer/sticky bar in course/spec templates are gated on `standalone`, so preview vs. compiled output differ.

---

## Phase 6 — Renderer audit (dead code / debt in `engine.py`)

| Finding | Location | Type |
|---|---|---|
| Redis caching never implemented | `engine.py:11` TODO | debt |
| Fabricated fallback blocks for fees/steps/jobs/reviews/faqs/syllabus/other_specs/features/financing/banks/recruiters/posts | `engine.py:794-1160` | schema workaround / R1 violation |
| Duplicate transform: transformer builds `jobs/reviews/faqs/fees/highlights`, engine rebuilds them | `engine.py:718-1208` | duplicate mapping |
| `course_href`/`spec_href` synthesised as `{uni}-online-mba`/`{uni}-mba-marketing` but only used by the single-card university fallback | `engine.py:583-584,1068` | legacy/near-dead |
| `ctx["ctx_json"]` serialises the whole context to JSON and is injected into templates | `engine.py:1272` | likely legacy debug hook; verify usage |
| `heroCrumb`/`heroChip`/etc. style vars set for all pages, several unused per template | `engine.py:1259-1270` | minor dead mappings |
| `clean_spec_name` (engine) overlaps `normalize_specialization_name` (utils) | `engine.py:444` vs `utils.py:75` | two spec-name cleaners |

## Phase 7 — Editor audit (`fieldSchema.js` + Review UI)

- **Editable:** scalar identity/stat/SEO fields + long-form content HTML + images. These match the schema names (uni uses `ugc_approved`, course/spec use `ugc_status` — consistent with the schema).
- **Missing from the editor (not editable at all):** every repeater — `highlights`, `fee_plans`, `job_profiles`, `reviews`, `faqs`, `facts`, `accreditations`, `programs_table`, `other_specs`, `faculty_members` — plus all `*_heading` fields, `validity`, `certificate_heading`, `faculty_intro`, `programs_intro`, `specializations_intro`, `num_programs`(uni has it)/`num_specializations`(course has it, spec doesn't need). An operator cannot review or correct any list data through the UI; they must trust the parser or edit `source.json` (which R5 forbids).
- **Orphan/at-risk editor fields:** blog `author` default "Krishna Porwal" (a real name) and `tag` "Career" (fieldSchema.js:75-77) — documented fabrications.
- **Consequence:** because repeaters aren't reviewable and the renderer fabricates them when empty, an operator has no way to see that (e.g.) the reviews are fake before publishing.

## Phase 8 — Builder audit

| Aspect | State |
|---|---|
| Route map + reserved-segment collision detection | ✅ |
| Canonical/OG URLs | ✅ via shared helpers |
| Metadata / JSON-LD / breadcrumbs | ✅ (but FAQPage can carry fabricated FAQs) |
| Sitemap | ✅ with per-page `lastmod` (contradicts the stale `seo.md` "no lastmod" note — see doc fixes) |
| robots.txt | ✅ points to sitemap |
| Assets / WebP variants (480/768/1200) | ✅ |
| Image handling / validation gate | ✅ (blocks missing required images) |
| **GA injection** | 🟨 hardcoded to `nmims-2` + hardcoded GA ID `G-B2N0SZPDFD` (`builder.py:231`) — bypasses per-tenant config |
| Does anything bypass the schema? | The builder itself is faithful; the fabrication happens upstream in the renderer, and it bakes into the static HTML the builder ships. |

## Phase 9 — Generic-platform audit (tenant-specific logic in shared code)

| Occurrence | Location |
|---|---|
| `if university_slug == "nmims-2"` GA tag + real GA ID | `builder.py:231` |
| `if uni_slug == "nmims-2" and "emba" in name_lower` | `engine.py:1048` |
| `uni_slug … or "nmims"` default | `engine.py:502` |
| `SITE_CONFIG` = NMIMS contact/footer/links | `core/site_config.py:11` (guarded, but resident in shared module) |
| Footer copyright defaults "© 2026 NMIMS Online" | `course.html:465`, `blog.html:229` |
| Recruiters `Tata/Indiamart/Wockhardt/…` (NMIMS list) as universal fallback | `engine.py:1008` |
| "Online MBA"/"MBA in"/"mba-marketing" assumptions | `engine.py:583-584,811,1068`; `specialization.py:22`; `clean_spec_name` degree list |
| `admissions@{{university_slug}}online.edu` | `specialization.html:429` |

The platform is **structurally** multi-tenant (isolated workspaces, per-tenant config) but **content-wise** still assumes NMIMS + an Online MBA program shape in the fabricated fallbacks and several defaults.

## Phase 10 — Dead code

| Item | Location | Note |
|---|---|---|
| `spec_desc_map` dict (26 entries) | `transformers/course.py:49-75` | **Built but never referenced** — spec cards use `hero_description[:80]`. Pure dead code. |
| `faculty_intro` mapping | `knowledge.py:44` | stored, never read for rendering |
| Redis TODO / AI gap-fill TODO | `engine.py:11`, `base.py:1` | never implemented |
| `ctx_json` full-context dump | `engine.py:1272` | probable legacy debug |
| Repo cruft (not backend) | root `screen0.jsx` (stray copy of `Screen0Workspace.jsx`), `change/` (old HTML/asset snapshot + reports), `ignou/`, `contact/` duplicate assets | outside audit scope; candidates for cleanup |
| `_extract_fee_plans` vs `_classify_fee_table` | `extractor.py` | near-duplicate table readers |

## Phase 11 — Regression risk vs `.agent` rules

| Rule | Status | Evidence |
|---|---|---|
| **R1 — Never fabricate content** | 🟥 **Violated pervasively** | `engine.py` fabricated fallbacks; `course.py`/`spec.py` hardcoded steps/badges/prose |
| **R2 — Templates render only transformed data** | 🟥 **Violated** | templates hardcode headings + marketing prose; engine rebuilds collections |
| R3 — Listing pages system-generated | ✅ | honoured |
| R4 — Generated HTML never hand-edited | ✅ (process rule) | — |
| R5 — `source.json` is source of truth | ⚠️ | repeaters not editable in UI → operators may be pushed to edit `source.json` |
| R6 — Workspace slug never in UI | 🟥 **Violated** | `specialization.html:429` slug-in-email |
| R7 — Specializations flat | ✅ | honoured |
| R8 — Preserve parser contracts | ✅ | block types intact |
| R9 — Lead capture decoupled | ✅ | honoured |
| R11 — YAGNI | ⚠️ | dead `spec_desc_map`, duplicate transform layer, unused style vars |
| R13 — Single canonical shared logic | ⚠️ | two spec-name cleaners; two fee-table readers |
| R16 — No hardcoded tenant contact in shared paths | ⚠️ | guarded but NMIMS block + recruiter list live in shared code |

## Phase 2 — Parser limitations (documented, not fixed)

- External microservice is a hard dependency for university/course/spec; if down, only the partial local extractor runs (no `*_heading`, no faculty, no reliable repeaters).
- Table header detection heuristic; merged/identical headers can still misparse (warnings emitted, REG-004).
- No image, footnote, or endnote extraction from DOCX.
- Local `_extract_reviews` expects quote-prefixed paragraphs; `_extract_faqs` expects strict bold-question/paragraph-answer pairing — brittle to formatting.
- Heuristic parent detection returns a best match even at very low score (may pre-fill wrong parent).

---

## Recommendations (priority-ordered — for a *future* change effort, not this audit)

1. **Stop fabricating content.** Delete the empty-collection fallbacks in `engine.py` (fees/steps/jobs/reviews/faqs/syllabus/other_specs/features/financing/banks/recruiters/posts) and the hardcoded blocks in `course.py`/`specialization.py`; guard the syllabus section with `{% if %}`. Restores R1.
2. **Make the university template render its schema content** (`about/why_choose/emi/exam/placement/facts/accreditations`) instead of hardcoded marketing; add a faculty section for `faculty_members`/`faculty_intro`.
3. **Consume `*_heading` fields** (or fall back to neutral constants) so section titles come from the schema.
4. **Collapse the double transform.** Move the engine's collection-building into the transformers, or make the engine purely presentational. One transform layer.
5. **Fix tenant leaks:** parameterise GA via `metadata.json["ga_id"]`; remove `slug`-in-email; move the NMIMS recruiter list out of the universal fallback.
6. **Expose repeaters in the editor** so operators can review lists (and catch fabrication) before publish.
7. **Remove dead code** (`spec_desc_map`, unused style vars, `ctx_json` if legacy).
8. **Add ingestion + compiler unit tests** (long-standing gap).

None of the above were performed — this document is the audit only.
