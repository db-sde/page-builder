# ARCHITECTURE.md — Complete Pipeline

## Overview

The system is a document-to-website pipeline. Raw Microsoft Word documents go in; static,
SEO-optimised HTML pages come out. Everything in between is structured, deterministic, and
runs locally on-disk.

---

## Full Pipeline Diagram

```
Raw .docx file
      │
      │  POST /parse-docx
      ▼
┌─────────────────────────────────┐
│  Ingestion Layer                │
│                                 │
│  parser.py                      │  Extracts raw blocks from DOCX
│    → [{type, text}, ...]        │  (paragraphs, tables, lists, headings)
│                                 │
│  extractor.py                   │  Maps blocks → canonical ACF field names
│    blocks_to_sections()         │  Uses HEADING_ANCHORS fuzzy matching
│    extract_acf()                │
│                                 │
│  External Microservice          │  For complex university/course docs
│    MICRO_APP_URL                │  Forwards raw .docx bytes; returns ACF JSON
│                                 │
│  adapter.py                     │  merge_micro_and_local(): micro wins, local fills gaps
│    adapt_schema()               │  Field name normalisation + type conversions
└─────────────────────────────────┘
      │
      │  Structured ACF JSON dict
      ▼
┌─────────────────────────────────┐
│  main.py: extract_metadata_from_json()   │
│                                 │
│  - Detects page_type (specialization / course / university / blog)  │
│  - Derives slug from title fields if missing                        │
│  - Derives university_slug from university_name if missing          │
│  - Heuristic parent_slug detection (token overlap scoring)          │
│  - Runs normalize_specialization_name() on spec name fields         │
└─────────────────────────────────┘
      │
      │  resolved = {slug, page_type, university_slug, parent_slug, raw}
      ▼
┌─────────────────────────────────┐
│  Transformer Layer              │
│                                 │
│  core/router.py                 │  TRANSFORMER_MAP: page_type → class
│    → get_transformer(resolved)  │  Also runs normalize_value() (strips NA/null)
│                                 │
│  transformers/base.py           │  BaseTransformer ABC
│    resolve() / resolve_list()   │  Page data → knowledge base → system default
│    format_fee()                 │  Delegates to core/utils.format_fee()
│    build_stats(), build_pills() │
│    build_reviews()              │
│                                 │
│  transformers/course.py         │  CourseTransformer
│  transformers/specialization.py │  SpecializationTransformer
│  transformers/university.py     │  UniversityTransformer
│  transformers/blog.py           │  BlogTransformer
│  transformers/programs_listing.py  etc.
│                                 │
│  → transformer.transform()      │  Returns complete context dict for template
└─────────────────────────────────┘
      │
      │  Page context dict
      ▼
┌─────────────────────────────────┐
│  Workspace Layer                │
│                                 │
│  workspace/manager.py           │
│    save_page()                  │  Writes source.json + draft .html to disk
│    resolve_page_dir()           │  Path resolution by page_type
│    ensure_metadata()            │  Creates metadata.json if missing
│    init_system_pages()          │  Creates stub listing pages
│                                 │
│  workspace/knowledge.py         │
│    update_university_knowledge()│  Extracts shared facts → university_knowledge.json
│    resolve_field()              │  Page → knowledge → default lookup chain
└─────────────────────────────────┘
      │
      │  POST /compile-workspace
      ▼
┌─────────────────────────────────┐
│  Compiler (Two-Pass)            │
│                                 │
│  workspace/compiler.py          │
│                                 │
│  Pass 1: _build_index()         │  Scans all source.json in workspace
│    global_map = {               │  Keyed by page_type → {slug → record}
│      "university": {...},       │
│      "course": {...},           │
│      "specialization": {...},   │
│      "blog": {...},             │
│      "programs_listing": {...}, │
│      "specializations_listing": {...},
│      "blog_listing": {...}      │
│    }                            │
│                                 │
│  Pass 2: _enrich_resolved()     │  Per-page context injection:
│    + render_resolved()          │  - course: injects child specializations, blogs
│                                 │  - specialization: injects parent course, sibling specs
│                                 │  - university: injects all courses, specs, blogs
│                                 │  - listing pages: injected with all relevant collections
│                                 │
│  System listing pages compiled  │  programs_listing, specializations_listing, blog_listing
│  last with fresh workspace data │
└─────────────────────────────────┘
      │
      │  POST /build-website
      ▼
┌─────────────────────────────────┐
│  Builder (Static Site Export)   │
│                                 │
│  workspace/builder.py           │
│                                 │
│  1. _build_route_map()          │  Maps slugs → clean URL routes
│                                 │  Collision detection for reserved segments
│  2. _validate_pages()           │  Checks required images exist on disk
│                                 │  Checks parent_slug integrity for specs
│  3. _finalize_html()            │  Adds GA tag (currently only nmims-2)
│  4. image_optimizer.py          │  PNG/JPG → WebP variants (480, 768, 1200px)
│  5. Copy assets                 │  CSS, fonts, JS → build/assets/
│  6. Rewrite internal links      │  Dynamic anchors → build-relative routes
│  7. Write routes.json           │  Route manifest
│  8. Write sitemap.xml           │  All pages listed
│  9. Write robots.txt            │  Points to sitemap
│                                 │
│  Build layout:                  │
│    build/                       │
│    ├── index.html               │  ← University homepage
│    ├── programs/index.html      │  ← Programs listing
│    ├── specializations/index.html
│    ├── blog/index.html          │
│    ├── blog/<slug>/index.html   │
│    ├── <course-slug>/index.html │
│    ├── <spec-slug>/index.html   │
│    ├── assets/                  │
│    │   ├── images/              │  WebP variants
│    │   ├── css/                 │
│    │   ├── fonts/               │
│    │   └── js/public-runtime.js │
│    ├── routes.json              │
│    ├── sitemap.xml              │
│    └── robots.txt               │
└─────────────────────────────────┘
      │
      ▼
  Static website (CDN-deployable)
```

---

## Workspace On-Disk Layout

```
workspaces/
└── <university_slug>/              ← e.g., nmims-2, chandigarh-university
    ├── metadata.json               ← theme colors, branding, contact overrides, build log
    ├── university_knowledge.json   ← shared facts (NAAC, UGC, established year, etc.)
    ├── University/
    │   ├── source.json
    │   └── university.html
    ├── Courses/
    │   └── <course-slug>/
    │       ├── source.json
    │       └── course.html
    ├── Specializations/            ← FLAT — never nested under Courses/
    │   └── <spec-slug>/
    │       ├── source.json
    │       └── specialization.html
    ├── Blogs/
    │   └── <blog-slug>/
    │       ├── source.json
    │       └── blog.html
    ├── Pages/                      ← System-generated listing pages only
    │   ├── programs/
    │   ├── specializations/
    │   └── blog/
    ├── Assets/
    │   ├── images/                 ← Source images (uploaded via Review UI)
    │   └── downloads/              ← Syllabus brochures
    └── build/                      ← Output of build_website(); CDN-deployable
```

---

## Specialization Parent Detection

When a specialization is uploaded without a `parent_slug`:

1. `_heuristic_detect_parent()` in `main.py` tokenises the specialization slug and all course
   slugs in the workspace, then scores by shared token count (position-weighted).
2. If a match scores > 0, it is pre-filled as a suggestion in the Review UI.
3. The administrator can override or confirm the match in the Review screen before saving.
4. At compile time, the compiler uses `parent_slug` to inject the parent course record
   and compute sibling specializations.

---

## Lead Capture Architecture (Decoupled)

```
Static page CTA button
      │ href="{LEAD_BASE_URL}/form?d={base64_payload}"
      ▼
contact/ React App (Vercel)
      │ decode d param → {uni, program, specialization, source, ...}
      │ brand interface with university colors/logo
      │ collect lead (name, email, phone, city)
      ▼
Supabase Edge Function (CRM webhook)
      POST with X-API-Key header
```

The `d` parameter payload is computed at **compile time** and baked into the static HTML.
The contact app reads `document.referrer` on load → saves to `sessionStorage["return_url"]`
→ used for back-navigation after form submission.

---

## Key Module Relationships

```
main.py
  ├── ingestion/parser.py          (DOCX parsing)
  ├── ingestion/extractor.py       (ACF extraction)
  ├── ingestion/adapter.py         (merge + schema)
  ├── core/router.py               (transformer dispatch)
  ├── renderer/engine.py           (Jinja2 render, SEO, JSON-LD)
  ├── workspace/manager.py         (save, list, resolve paths)
  ├── workspace/compiler.py        (two-pass compile)
  ├── workspace/builder.py         (static site export)
  └── workspace/knowledge.py       (shared university facts)

core/router.py
  └── transformers/*.py            (one class per page type)
      └── transformers/base.py     (common helpers)
          ├── core/site_config.py  (nav/footer/contact per tenant)
          └── core/utils.py        (format_fee, normalize_*, build_public_route)

renderer/engine.py
  ├── templates/*.html             (Jinja2 templates)
  └── workspace/knowledge.py       (field resolution)
```
