# PROJECT.md — DegreeBaba Page Builder

## Purpose

DegreeBaba Page Builder is an internal production tool that ingests university curriculum
documents (Microsoft Word `.docx`) and produces fully compiled, SEO-optimised static HTML
websites for distance and online learning university portals in India.

It is used by the DegreeBaba editorial team to publish landing pages for universities,
courses, specializations, and blogs — without requiring a developer for each page.

---

## Supported Page Types

| Page Type | Stored Under | Template |
|---|---|---|
| `university` | `workspaces/<uni>/University/` | `university.html` |
| `course` | `workspaces/<uni>/Courses/<slug>/` | `course.html` |
| `specialization` | `workspaces/<uni>/Specializations/<slug>/` | `specialization.html` |
| `blog` | `workspaces/<uni>/Blogs/<slug>/` | `blog.html` |
| `programs_listing` | `workspaces/<uni>/Pages/programs/` | `programs_listing.html` |
| `specializations_listing` | `workspaces/<uni>/Pages/specializations/` | `specializations_listing.html` |
| `blog_listing` | `workspaces/<uni>/Pages/blog/` | `blog_listing.html` |

Listing pages (`programs_listing`, `specializations_listing`, `blog_listing`) are **system-generated** —
they are never created from a `.docx` file; they are automatically rebuilt during workspace compilation
using data from all saved course, specialization, and blog pages.

---

## Rendering Philosophy

- **Data-first, never invented.** If a field is missing in `source.json`, the section is hidden.
  The system never falls back to placeholder text or fabricated data.
- **Static by design.** Pages are fully compiled to HTML at save/compile time. Runtime JavaScript
  is minimal (only `public-runtime.js` for menus, accordions, and tabs).
- **Multi-tenant isolation.** Each university has its own workspace directory. No shared mutable state.
- **Compiler is the single render authority.** Every `.html` in the workspace is an output of the
  compiler, never edited directly.

---

## Project Goals

1. Convert raw Word documents into structured, schema-validated JSON.
2. Compile high-quality, SEO-optimised HTML pages from that JSON.
3. Export deployable static websites with correct routing and sitemaps.
4. Capture leads via a decoupled, centrally hosted React application.
5. Support multiple universities (tenants) in isolated workspaces.

---

## Non-Goals

- This is not a real-time CMS. Page updates require re-compilation.
- This is not a general-purpose site generator. Templates are purpose-built for Indian ed-tech content.
- No real-time CRM sync. Leads are sent to Supabase; updates in the CRM do not flow back.
- No AI-generated content. Fields left blank by the DOCX remain blank in the output.

---

## Data Flow

```
Raw .docx
  │
  ├─► Local parser (parser.py)         → block list [{type, text}, ...]
  │
  ├─► External microservice            → ACF JSON dict (for complex academic docs)
  │         (MICRO_APP_URL)
  │
  └─► adapter.py merge_micro_and_local() → merged ACF JSON
         │
         ▼
  extract_metadata_from_json()          → slug, page_type, university_slug, parent_slug, data
         │
         ▼
  Transformer (transformers/<type>.py)  → context dict for template rendering
         │
         ▼
  save_page()                           → workspaces/<uni>/<Type>/<slug>/source.json
                                          workspaces/<uni>/<Type>/<slug>/<type>.html (draft)
         │
         ▼
  compile_workspace()
    ├── Pass 1: _build_index()          → in-memory catalog of all source.json files
    └── Pass 2: _enrich_resolved()      → inject parent/sibling/university context
                + render_resolved()     → overwrite .html files with full context
         │
         ▼
  build_website()                       → workspaces/<uni>/build/
    ├── Copies assets (WebP-optimised images, CSS, fonts, JS)
    ├── Rewrites internal links to build-relative routes
    ├── Writes routes.json
    └── Writes sitemap.xml
         │
         ▼
  Static website ready for CDN deployment
```

---

## University Knowledge Base

Each workspace has an optional `university_knowledge.json` file that stores shared
university-wide facts (NAAC grade, UGC status, established year, contact info, etc.).
When a page's `source.json` does not contain a shared field, the knowledge base is
consulted as a fallback. This prevents repeating the same data in every page's DOCX.

## Lead Capture (Decoupled)

All CTA buttons across all compiled pages link to an external React application
(`LEAD_BASE_URL`). The lead context (university, program, specialization, source)
is encoded as a URL-safe Base64 JSON string in the `d` query parameter.
The lead app decodes this, brands itself accordingly, collects the user's details,
and submits them to the Supabase CRM webhook.
