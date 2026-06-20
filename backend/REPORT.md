# page-engine — Project Report

## What This Project Does
The `page-engine` project is a high-performance content ingestion and static page generation engine. It enables non-technical university administrators to author comprehensive academic program pages, FAQs, student reviews, and program highlights in standard Microsoft Word (`.docx`) files, which are then parsed and processed into an intermediate Advanced Custom Fields (ACF) JSON database. A FastAPI web application reads from this structured data, processes it via dynamic domain-specific transformers, and renders visually stunning, responsive, and SEO-optimized HTML pages using Jinja2 templates styled with cohesive brand-specific colors and micro-interactions.

## Architecture Overview
The system follows a fully stateless, in-memory transformation pipeline. Instead of storing and querying records from a database, the system processes ACF JSON payloads directly through domain-specific transformers, rendering and returning preview HTML dynamically. Finalized HTML pages are persisted to disk under categorized subdirectories ONLY when the user initiates a download.

Below is the data flow representation:

```
+----------------+
|  Source .docx  |
+-------+--------+
        |
        v
+-------+----------------------------+
| Ingestion Parser (parser.py)       | (Parses docx paragraphs & tables into a flat block list)
+-------+----------------------------+
        |
        v
+-------+----------------------------+
| Ingestion Extractor (extractor.py) | (Groups blocks using fuzzy heading anchors into ACF format)
+-------+----------------------------+
        |
        v
+-------+----------------------------+
| Ingestion Entry (ingest.py)        | (Saves output to standalone generated/{type}/{slug}.json)
+-------+----------------------------+

               OR (FastAPI HTTP Flow)

+--------------------+
| Pasted ACF JSON    |
+-------+------------+
        |
        v
+-------+----------------------------+
| FastAPI Server (main.py)           | (Ingests ACF payload, extracts metadata in-memory)
+-------+----------------------------+
        |
        v
+-------+----------------------------+
| router (core/router.py)            | (Instantiates the correct dynamic transformer class)
+-------+----------------------------+
        |
        v
+-------+----------------------------+
| transformers/                      | (Compiles stats, breadcrumbs, and presentation fields)
+-------+----------------------------+
        |
        v
+-------+----------------------------+
| renderer (renderer/engine.py)      | (Jinja2 compiler renders context dynamically)
+-------+----------------------------+
        |
        v
+-------+----------------------------+
| HTML Output & Disk Persistence     | (Writes to backend/generated/{page_type}/{slug}.html)
+------------------------------------+
```

## Components Built

### Router (`core/router.py`)
- **What it does**: Maps incoming resolved page type descriptors to their corresponding transformer classes.
- **How resolution works**:
  - `get_transformer(resolved)`: Selects and instantiates the correct subclass from `TRANSFORMER_MAP` (e.g. `CourseTransformer`, `SpecializationTransformer`) passing the in-memory descriptor.

### Site Config (`core/site_config.py`)
- **What it stores**: Global constant parameters (telephone numbers, WhatsApp api hooks, support email address, physical office address, navigation items, footer columns, and copyright clauses).
- **How it's consumed**: Imported inside `BaseTransformer` (`transformers/base.py`) to compile configuration keys into the base dictionary under the `site` namespace.

### Transformers
Each page class maps raw fields to structural presentation keys:
- **BaseTransformer** (`transformers/base.py`): Abstract base class. Defines shared methods like `format_fee()`, `build_breadcrumbs()`, `build_pills()`, `build_stats()`, `build_rail()`, `build_reviews()`, and `build_fee_note()`.
- **UniversityTransformer** (`transformers/university.py`): Inherits `BaseTransformer`. Transforms NIRF facts, logo badges, custom rankings, admission steps list, tuition fee ranges, and programs table.
- **CourseTransformer** (`transformers/course.py`): Inherits `BaseTransformer`. Transforms courses, syllabus structures, and maps fee plans in-memory.
- **SpecializationTransformer** (`transformers/specialization.py`): Inherits `BaseTransformer`. Computes active navigation rails, maps average recruiter salaries, and builds breadcrumbs.
- **BlogTransformer** (`transformers/blog.py`): Prepares article directory mappings. Separates the list of articles into a single `featured_post` and a list of regular `posts`, forwarding category chip items.
- **ContactTransformer** (`transformers/contact.py`): Maps telephone and email info, office timing states, average queue response times, and selectable programs list.

### Renderer (`renderer/engine.py`)
- **How Jinja2 is configured**: Configured with `FileSystemLoader` referencing `templates/`, autoescape enabled for HTML, and a custom filter `de` (`default_empty`) to safely resolve empty/missing keys as `""` rather than displaying `None`.
- **Template map**: Explicitly links `page_type` strings to HTML template filenames (e.g. `specialization -> specialization.html`).
- **render_resolved function**: Accepts the fully resolved payload dictionary, triggers the appropriate transformer, and compiles the template entirely in-memory.

### Ingestion Pipeline (`ingestion/`)
- **parser.py**: Reads `.docx` files using `docx.Document`. Maps heading styles (Heading 1 to Heading 4) to HTML heading tokens (`h1`-`h4`), runs bold paragraph classification, and processes tables into clean row lists.
- **extractor.py**: Maps heading blocks against fuzzy definitions in `HEADING_ANCHORS` to group document sections, converting tables and text into formatted arrays (FAQs, reviews, programs, or fee structures).
- **ingest.py**: Integrates CLI arguments via `argparse`, parses target documents, formats metadata fields, and writes the output directly to a standalone `{slug}.json` file inside `backend/generated/{page_type}/`.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/preview-html` | Generates HTML preview dynamically and returns it for in-memory client-side rendering |
| POST | `/render-html` | Generates HTML, saves it under `backend/generated/{page_type}/{slug}.html`, and returns the file as a download |
| POST | `/parse-docx` | Uploads and parses a `.docx` file, returning the extracted ACF JSON payload |
| POST | `/save-temp-json` | Saves a temporary debug JSON file to disk for development inspection |

---

## Data Flow Example
When a user clicks **Generate Preview** and then **Download** in the frontend:
1. **Frontend Dispatch**: The React app sends a POST request with the updated ACF JSON state to `/preview-html`.
2. **Stateless Render**: FastAPI routes the payload, extracts metadata in-memory, instantiates the corresponding transformer, executes Jinja2 template rendering, and returns the raw compiled HTML.
3. **Client-Side Iframe & Popup**: The frontend injects the returned HTML into an iframe via the `srcDoc` attribute. If "Open Full Page" is clicked, the in-memory content is opened in a new tab via `window.open().document.write()`.
4. **Finalized Persistence**: When the user clicks the Download button, `/render-html` is called, which compiles the HTML, writes the output file to `backend/generated/{page_type}/{slug}.html` dynamically, and initiates a browser download attachment.

---

## Known Limitations & Future Roadmap
- **No Database Dependency**: The current setup runs completely database-free and stateless.
- **Single Page Scope**: Because there is no central database store, sibling lookups (e.g., listing other specializations of a university) are disabled and default to empty.
- **Redis Cache Layer**: Dynamic rendering is performed on each preview request; a cache layer could be introduced if payload sizes grow massive.
- **Lead persistency**: Form actions on the compiled HTML remain client-side mock-ups.
