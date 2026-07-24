# TEMPLATE_AUDIT.md

**Audit date:** 2026-07-24 · Read-only.

Per-template, per-section breakdown of the **data source** behind every rendered block.
Legend for "Source":
- **schema** — the section's own Micro-App field.
- **transformed** — derived in a `transformers/*` class from schema fields.
- **computed** — built in `renderer/engine.py` from workspace/relationship data.
- **hardcoded** — literal string constant in the template.
- **fallback** — engine/transformer substitutes fabricated data when schema value is empty.
- **placeholder** — visible only when an image/value is absent (dev art).

7 templates, no `extends` hierarchy (each self-contained). Section titles are **hardcoded in all 7** (no `*_heading` field is consulted anywhere).

---

## 1. `university.html`

| Section | Source | Notes / problems |
|---|---|---|
| `<title>`/meta/OG | schema (`seo_title`,`meta_description`) | ✅ clean; OG/Twitter/JSON-LD added by engine post-processor |
| Top bar | hardcoded + `site.topbar_text` | ⬜ generic |
| Header/nav/logo | computed (`branding_logo`,`university_letter`,`university_name`) | ✅; letter-badge fallback ok |
| Hero H1/description | transformed (`hero.full_name`/`description`) | ✅ |
| Hero accreditation badge | **hardcoded `NIRF #24`** + schema naac/ugc | 🟥 C6 |
| Hero stats (Est/NAAC/UGC) | schema + **`default('2010')`** + hardcoded "UGC/Approved Degrees" | 🟧 H10, H11 |
| Accreditation strip | **hardcoded** `AIU Member / NIRF #24 / WES Recognised` | 🟥 C7 |
| Programs grid | computed (`programs` from workspace courses) **or fallback** single "Online MBA" card | 🟧 fallback (engine:1067) |
| Programs eyebrow/heading/subtitle | **hardcoded** | 🟧 H14 (ignores `programs_intro`,`programs_heading`) |
| Specializations grid | computed (`specs` from workspace) | ✅ (empty if none) |
| Specializations heading/subtitle | **hardcoded** | 🟧 H14 |
| "Why us" block | **hardcoded prose** + `features` fallback | 🟥/🟧 H9,H5 — **ignores `why_choose_content`** |
| Admission process | computed `admission` (engine steps) **or fallback** | 🟧 H2; heading hardcoded; **ignores `admission_heading`** |
| Fees & financing | **hardcoded copy** + `financing`/`banks` fallback | 🟥/🟧 H6,H7 — **ignores `emi_content`** |
| Recruiters strip | **fallback** hardcoded logos | 🟥 C5 |
| Testimonials | fallback (from fabricated reviews) | 🟥 C1 |
| FAQ | schema/fallback | 🟧 C3 (5 hardcoded if empty) |
| CTA band | hardcoded + `default('₹8,334/month')` | 🟨 M9 |
| Blog preview | computed `posts` **or fallback demo posts** | 🟥 C10 |
| Footer | computed + hardcoded copy; copyright uses `university_name` | ⬜/🟨 |

**Not rendered at all (transformed but dropped):** `about_content`, `why_choose_content`, `emi_content`, `exam_content`, `placement_content`, `facts`, `accreditations`, `admission_fee_note`, `programs_intro`, `faculty_*`.

---

## 2. `course.html`

| Section | Source | Notes / problems |
|---|---|---|
| Head/meta/OG | schema | ✅ |
| Header/footer/sticky bar | computed; **only when `standalone`** | note: compiled workspace pages render header/footer via `standalone`; sticky bar defaults `₹2,00,000`/`₹8,334/mo` (🟨 M10); footer copyright default "NMIMS Online" (🟨 M5) |
| Hero (breadcrumb/title/desc/pills/badge) | transformed | ✅; pills include hardcoded "No Entrance Exam" (course.py:135) |
| Stats strip (6) | transformed (`stats`) | ✅ |
| Sidebar rail | transformed (`rail`) | ✅ (built from present sections) |
| About | schema `about_content` | ✅ but heading "About the {{hero.title}}" hardcoded (ignores `about_heading`) |
| Highlights | schema `highlights` | ✅; heading hardcoded |
| Accreditations | **transformed hardcoded prose** | 🟥 C8 |
| Specializations | computed `specs` + **hardcoded intro para** | 🟧 H8 (ignores `specializations_intro`) |
| CTA band 1 | hardcoded | ⬜ |
| Fees | schema `fee_plans` **or fallback 3 rows** | 🟧 H3 |
| Eligibility | schema `eligibility_content` | ✅ |
| Admission | transformed/engine **fallback** steps | 🟧 H1,H2; ignores `admission_fee_note` |
| Syllabus | schema **or hardcoded curriculum; always shown** | 🟥 C4 / 🟧 H16 |
| Placement & certificate | schema (`placement_content`,`certificate_description`,`certificate_image_url`) | ✅ |
| Jobs | schema **or 6 fabricated** | 🟥 C2 |
| CTA band 2 | hardcoded | ⬜ |
| Reviews | schema **or 3 fabricated named** | 🟥 C1 |
| FAQ | schema **or 5 hardcoded** | 🟥 C3 |

---

## 3. `specialization.html`

| Section | Source | Notes / problems |
|---|---|---|
| Head/meta/OG | schema | ✅ |
| Hero | transformed | H1 = `{{parent_program_name}} in {{hero.title}}` (dynamic ✅); badge default "Most Popular Specialization" (🟧 H12); stat-card default `₹14.2L` (🟥 C11) |
| Stats strip (5) | transformed | ✅ |
| Rail | transformed | ✅ |
| About | schema | ✅; heading hardcoded |
| Highlights | schema | ✅ |
| Eligibility | schema | ✅ |
| Fees | schema **or fallback** | 🟧 H3 |
| CTA band 1 | hardcoded ("Ready to specialise in {{hero.title}}?") | ⬜ |
| Admission | fallback steps | 🟧 H2; ignores `admission_fee_note` |
| Syllabus | schema **or hardcoded; always shown** | 🟥 C4 / 🟧 H16 |
| Other specs (compare) | computed siblings **or hardcoded 7-row** | 🟥 C9; schema `other_specs` only used as deep fallback |
| Exam | schema `exam_content` | ✅ |
| Placement/certificate | schema | ✅ (dynamic heading by presence) |
| Jobs | schema **or fabricated** | 🟥 C2 |
| CTA band 2 | hardcoded | ⬜ |
| Reviews | schema **or fabricated** | 🟥 C1 |
| FAQ | schema **or hardcoded** | 🟥 C3 |
| Footer | computed; email fallback `admissions@{{university_slug}}online.edu` | 🟨 M1 (slug leak) |

---

## 4. `blog.html`
Blog uses the legacy blog parser/transformer (per project scope). Section data comes from the blog transformer. Only hardcoded finding: footer copyright default "© 2026 NMIMS Online" (`blog.html:229`, 🟨 M6). Editor defaults author "Krishna Porwal" (fieldSchema 🟨 M11). Not audited field-by-field against the Micro-App schema (out of scope — blogs are not part of the University/Course/Specialization contract).

---

## 5–7. Listing templates (`programs_listing.html`, `specializations_listing.html`, `blog_listing.html`)

Cleanest of the set — **fully data-driven** from `engine.py`'s `programs_list_json` / `spec_groups_json` / `all_posts_json` (computed from the workspace index; REG-001 fixed the fabricated-cards bug, so empty workspaces render empty states, not fake cards).

| Template | Sources | Problems |
|---|---|---|
| `programs_listing.html` | computed workspace courses; neutral defaults `2 Years`/`100% Online`/`Contact for fee` | ⬜ only neutral placeholders; copyright default `© 2026.` |
| `specializations_listing.html` | computed workspace specs grouped by parent | ⬜ neutral; `Contact for fee` |
| `blog_listing.html` | computed workspace blogs | 🟨 M8 hardcoded EMI line in CTA band; copyright default |

---

## Cross-cutting template problems

1. **Section titles never come from the schema.** All `*_heading` fields ignored; every `<h2>` is a hardcoded English constant.
2. **University page discards most parsed content** (`about`, `why_choose`, `emi`, `exam`, `placement`, `facts`, `accreditations`, `faculty`) in favour of hardcoded marketing blocks + fabricated stat lists.
3. **Fabricated fallbacks defeat `{% if %}` guards.** Because `engine.py` repopulates `jobs/reviews/faqs/fees/syllabus` with fake data, the guards are effectively always true — the "hide empty sections" rule (R1) does not hold for these.
4. **Syllabus sections have no guard at all** — always rendered.
5. **Tenant leaks** (NMIMS copyright defaults, `{{university_slug}}` email) live in shared templates.
6. **No template inheritance** — the same hardcoded header/footer/hero markup is duplicated across university/course/specialization, so any fix must be applied in 3–7 places.
