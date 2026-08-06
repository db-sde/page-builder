# DegreeBaba Page Builder

An enterprise-grade, multi-tenant content ingestion pipeline, static site compiler, and visual authoring suite for Indian distance-learning and online university portals.

The system ingests Microsoft Word (`.docx`) curriculum documents, extracts structured schema-validated Advanced Custom Fields (ACF) JSON datasets (`source.json`), and compiles high-performance, SEO-optimised static websites ready for global CDN deployment.

---

## Key Features

* **DOCX Ingestion & Micro-Parser Pipeline**: Local Python parsing (`python-docx`) merged with cloud microservice fallback to automatically extract metadata, fee structures, eligibility criteria, FAQs, and image assets from Word documents.
* **Multi-Tenant Workspace Architecture**: Isolated workspace folders (`workspaces/<uni>/`) for each university (e.g., IGNOU, LPU, NMIMS). Content is stored as human-readable `source.json` files on disk (acting as a Git-friendly database).
* **Two-Pass Static Site Compiler**: Pass 1 indexes all workspace entities (universities, courses, specializations, blogs); Pass 2 injects cross-entity relationships, sibling specializations, and navigation context before compiling final static `.html` pages.
* **Visual Authoring & Review Admin UI**: A React 19 + Vite admin interface featuring live preview, field-level completeness validation, sticky quick-jump navigation, and image management.
* **Decoupled Lead Capture**: Static pages seamlessly integrate with a hosted React application (`contact/`) communicating with Supabase Webhook endpoints for CRM lead collection.
* **Automated SEO & Structured Data**: Built-in JSON-LD schema generation (`CollegeOrUniversity`, `Course`, `FAQPage`, `BlogPosting`), canonical URLs, OpenGraph metadata, and automatic `sitemap.xml` / `routes.json` generation.
* **Supabase Storage Sync**: Bidirectional multi-threaded sync helpers (`sync_all_to_supabase.py`, `sync_from_supabase_to_local.py`) for cloud backup and Render environment persistence.

---

## Architecture Overview

```
.docx File Upload
       │
       ▼
Ingestion Layer (parser.py → extractor.py → adapter.py)
       │
       ▼
Source JSON (workspaces/<uni>/<Type>/<slug>/source.json)
       │
       ▼
React Admin UI (Field Ownership & Live Review)
       │
       ▼
Compiler (Pass 1: Build Index  │  Pass 2: Enrich & Re-render)
       │
       ▼
Builder Exporter (workspaces/<uni>/build/)
       │
       ▼
Static Site Export (Deployable to Netlify, Vercel, S3, or Render)
```

---

## Tech Stack

| Component | Technology | Description |
|---|---|---|
| **Backend API** | Python 3.12, FastAPI, Uvicorn | Async REST API & ingestion controllers |
| **Templating** | Jinja2 | 7 responsive HTML templates (`backend/templates/`) |
| **Parsing** | `python-docx`, Pillow (PIL) | Document parsing and WebP image processing |
| **Frontend Admin UI** | React 19, Vite, Vanilla CSS | Workspace browser, content editor & live preview |
| **Lead Capture** | React, Vite | Decoupled form app (`contact/`) |
| **Cloud Storage** | Supabase Storage REST API | Multithreaded workspace cloud persistence |
| **Package Manager** | `uv` (Python), `npm` (Frontend) | Fast dependency management |

---

## Repository Structure

```
acfTOhtml copy/
├── backend/                        # FastAPI backend server
│   ├── core/                       # Canonical field definitions & page blueprints
│   ├── ingestion/                  # DOCX parsing, extraction & schema adapters
│   ├── renderer/                   # Jinja2 engine, custom filters & SEO injection
│   ├── templates/                  # Responsive Jinja2 HTML page templates
│   ├── transformers/               # Page-type specific context transformers
│   ├── workspace/                  # Workspace layout, compiler, builder & Supabase sync
│   ├── workspaces/                 # Disk-based university workspaces (database)
│   ├── tests/                      # PyUnit automated test suite (79 tests)
│   └── scratch/                    # Cloud sync scripts & utilities
├── frontend/                       # React 19 + Vite admin frontend
│   └── src/                        # Screen0–3 editor components, CSS & schemas
├── contact/                        # Hosted lead capture React app
├── doc/                            # System architecture reports & audit documentation
│   ├── REPORT.md                   # Single source of truth system report
│   ├── PLATFORM_AUDIT.md           # Deep-dive architecture audit
│   ├── SCHEMA_COVERAGE_REPORT.md   # Field schema mapping report
│   ├── TEMPLATE_AUDIT.md           # Jinja2 HTML template audit
│   ├── PIPELINE_TRACE.md           # Ingestion pipeline trace logs
│   ├── NMIMS_PRODUCTION_AUDIT.md   # Production workspace validation report
│   └── HARDCODED_CONTENT_AUDIT.md  # Clean content audit
└── README.md                       # Main project documentation
```

---

## Quick Start

### Prerequisites

* Python 3.12+ and [`uv`](https://github.com/astral-sh/uv)
* Node.js 18+ and `npm`

### 1. Backend Setup

```bash
cd backend

# Install dependencies and start FastAPI development server (port 8000)
uv run main.py
```

### 2. Frontend Admin Setup

```bash
cd frontend

# Install dependencies and start Vite dev server (port 5173)
npm install
npm run dev
```

Open `http://localhost:5173` in your browser to access the workspace editor.

### 3. Lead Capture App (Optional)

```bash
cd contact

# Install dependencies and start lead capture app preview
npm install
npm run dev
```

---

## Environment Variables

### `backend/.env`
```env
MICRO_APP_URL=https://micro-app-57l9.onrender.com
LEAD_BASE_URL=https://applicationquery.vercel.app

# Optional Supabase Workspace Storage Persistence
# SUPABASE_URL=https://<project-id>.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
# SUPABASE_WORKSPACE_BUCKET=degreebaba-workspaces
```

### `contact/.env`
```env
VITE_WEBHOOK_URL=https://<project-id>.supabase.co/functions/v1/webhook-inbound
VITE_WEBHOOK_API_KEY=<secret>
```

---

## Important Commands

```bash
# Run Backend Unit Test Suite (79 tests)
cd backend
uv run python -m unittest discover tests/

# Build Frontend Bundle
cd frontend
npm run build

# Sync All Local Workspaces to Supabase Storage
cd backend
uv run python scratch/sync_all_to_supabase.py

# Sync All Supabase Remote Workspaces to Local Disk
cd backend
uv run python scratch/sync_from_supabase_to_local.py

# Export Static Website for a University
POST http://localhost:8000/build-website?university_slug=ignou
```

---

## System Documentation Index

For detailed deep-dives into specific subsystems, refer to the documentation in the [`doc/`](doc/) folder:

* 📖 [**System Architecture Report**](doc/REPORT.md) — Comprehensive single source of truth for the entire platform architecture.
* 🖼️ [**Image Specifications Guide**](doc/IMAGE_SPECIFICATIONS.md) — Complete guide to image sizes, aspect ratios, formats, and rendering safe zones for designers and AI tools.
* 🛠️ [**Platform Audit**](doc/PLATFORM_AUDIT.md) — Architectural patterns, pipeline lifecycle, and performance audits.
* 📋 [**Schema Coverage Report**](doc/SCHEMA_COVERAGE_REPORT.md) — Field definition mappings and post-parser contracts.
* 🎨 [**Template Audit**](doc/TEMPLATE_AUDIT.md) — Jinja2 HTML template structure and responsive design audit.
