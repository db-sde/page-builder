# ROADMAP.md — Project Roadmap

Derived from the git log (30 most recent commits), REPORT.md, and codebase inspection.

---

## ✅ Completed

### Core Pipeline
- [x] Local DOCX parser (`parser.py`) — paragraphs, tables, headings, lists, bold
- [x] ACF JSON extractor (`extractor.py`) — fuzzy heading matching via `HEADING_ANCHORS`
- [x] External micro-pipeline integration — forwards raw `.docx` bytes to `MICRO_APP_URL`
- [x] Micro + local merge adapter (`adapter.py`) — micro wins, local fills gaps
- [x] `extract_metadata_from_json()` — auto-detects `page_type`, derives `slug`, `university_slug`
- [x] Recursive `normalize_value()` — strips `NA`, `N/A`, `null`, dashes before transformers run
- [x] All seven transformer classes — course, specialization, university, blog, and three listing types
- [x] `BaseTransformer` with shared helpers — `resolve()`, `build_stats()`, `build_pills()`, `build_reviews()`
- [x] University knowledge base (`knowledge.py`) — shared fields across pages via `university_knowledge.json`
- [x] Field resolution chain — Page → Knowledge → System default

### Workspace System
- [x] Multi-tenant workspace directory structure
- [x] `manager.py` — `save_page()`, `resolve_page_dir()`, `ensure_metadata()`, `init_system_pages()`
- [x] `metadata.json` per workspace — theme colors, branding, contact overrides, build log
- [x] Workspace slug isolation — internal slug never leaks into user-facing content

### Compiler
- [x] Two-pass compiler (`compiler.py`)
- [x] Pass 1: `_build_index()` — scans all `source.json` files into global map
- [x] Pass 2: `_enrich_resolved()` — injects parent/sibling/workspace context
- [x] Auto-rebuild of listing pages after user-content pages are compiled
- [x] `_resolve_university_context()` — canonical, DRY resolution of display name/logo

### Builder / Static Export
- [x] `builder.py` — full static site exporter
- [x] Route map builder with reserved segment collision detection
- [x] Image validation before build (blocks missing hero/certificate images)
- [x] WebP image optimisation with responsive variants (480, 768, 1200px)
- [x] Local font hosting (fonts copied into `build/assets/fonts/`)
- [x] Internal link rewriting to build-relative routes
- [x] `routes.json` manifest
- [x] `sitemap.xml` generation
- [x] `robots.txt` generation (pointing to sitemap)
- [x] ZIP build download endpoint
- [x] Google Analytics tag injection (currently only `nmims-2` workspace)

### Renderer / Templates
- [x] Jinja2 rendering engine (`engine.py`)
- [x] Custom filters: `de` (default_empty), `webp_variant`, `image_width`, `image_height`
- [x] 7 Jinja2 HTML templates (one per page type)
- [x] SEO meta tags + Open Graph tags injected at render time
- [x] JSON-LD structured data (BreadcrumbList, Course, FAQPage, Organization)
- [x] Canonical URL normalisation
- [x] `SyllabusHTMLParser` and `AdmissionHTMLParser` — HTML → structured JSON lists
- [x] `public-runtime.js` — minimal deferred JS for menus/accordions/tabs

### Specialization System
- [x] Flat specialization storage (not nested under courses)
- [x] Heuristic parent course detection via token overlap scoring
- [x] `normalize_specialization_name()` — strips redundant degree/university prefixes
- [x] Dynamic heading pattern: `{parent_program_name} in {specialization_name}`
- [x] Breadcrumb: Home → Parent Course → Specialization
- [x] Sibling specialization comparison table on specialization pages
- [x] Parent slug manual override in Review UI

### Lead Capture
- [x] Decoupled contact app (`contact/`) — independent Vite React app
- [x] URL-safe Base64 encoded `d` payload (baked at compile time)
- [x] Referrer-based back navigation via `sessionStorage["return_url"]`
- [x] Supabase CRM webhook integration
- [x] Context-aware lead forms by `source` field
- [x] Client-side validation (name, email, 10-digit mobile)

### Admin Frontend
- [x] 4-step wizard (Screen 0: Workspace → Screen 1: Upload → Screen 2: Review → Screen 3: Preview)
- [x] `fieldSchema.js` — required/optional field list per page type with impact descriptions
- [x] `FieldHealthPanel.jsx` — visual completeness indicator
- [x] `AddFieldModal.jsx` — add missing fields from the schema
- [x] Workspace create/select/delete
- [x] Page create/edit/delete
- [x] Image upload with Base64 encoding → saves to `Assets/images/`
- [x] Preview in iframe (via `/preview-html` endpoint)
- [x] Download compiled HTML

### Multi-tenant Isolation
- [x] Per-tenant `site_config` — nav, footer, contact info from `metadata.json`
- [x] Generic defaults for all tenants except original `nmims` workspace
- [x] Custom logo/favicon support per workspace
- [x] Automatic letter badge fallback when logo image is absent

---

## 🔄 Current

Based on git log and active terminal processes (`uv run main.py`, `npm run dev`):
- Active development session — backend and frontend both running
- No specific in-progress feature identified from repository state alone

---

## 🔜 Next (from REPORT.md + codebase TODOs)

- [ ] Responsive CSS refinement — minor visual issues on intermediate screen sizes
- [ ] Contact app polish — loading states on form inputs, better validation message design
- [ ] Redis caching for `render_resolved()` — marked with `TODO` comment in `engine.py`
- [ ] AI gap-fill hook in `BaseTransformer` — marked with `TODO` in `transformers/base.py`
  (call Groq when a required field is `None` before skipping the section)
- [ ] Unit tests for ingestion pipeline (parser, extractor, adapter)
- [ ] Unit tests for lead payload decoder
- [ ] Unit tests for workspace compiler

---

## 🔮 Future (from REPORT.md roadmap)

### Short-Term
- Automated integration tests for workspace compiler and builder
- Compiler caching — skip unchanged pages on re-compile

### Medium-Term
- Real-time compilation status tracking in the React admin dashboard
- Direct asset uploads from local devices into the Review screen (currently Base64 over API)

### Long-Term
- Direct publishing to cloud storage (AWS S3, Cloudflare Pages) from build interface
- Global search index across all course pages in static workspace files
