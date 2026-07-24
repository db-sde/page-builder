# systems/renderer.md — Jinja2 Rendering Engine

## Purpose

Convert a page context dictionary (produced by a transformer) into a complete,
SEO-optimised static HTML page using Jinja2 templates.

---

## Responsibilities

1. Load the correct Jinja2 template for the page type
2. Run the appropriate transformer to produce the context dict
3. Inject SEO metadata (title, description, Open Graph, canonical URL)
4. Build and inject JSON-LD structured data (BreadcrumbList, Course, FAQPage, Organization)
5. Render the template with the context
6. Expose custom Jinja2 filters for safe value handling and image processing

---

## Inputs

- `resolved` dict:
  ```python
  {
    "slug": "nmims-online-mba",
    "page_type": "course",
    "university_slug": "nmims-2",
    "parent_slug": None,
    "raw": { ...ACF data dict... }
  }
  ```
- `standalone` bool — if `True`, inlines critical CSS and omits workspace-relative asset paths

---

## Outputs

- Rendered HTML string (complete page)

---

## Key Entry Point

```python
from renderer.engine import render_resolved
html = render_resolved(resolved, standalone=False)
```

---

## Custom Jinja2 Filters

| Filter | Function | Purpose |
|---|---|---|
| `de` | `default_empty(value)` | Returns `""` if `value is None`; prevents `None` from rendering as "None" |
| `webp_variant` | `webp_variant_filter(url, width)` | Converts image URL to `.webp` variant path |
| `image_width` | `image_width_filter(context, url)` | Returns actual image width in px using Pillow |
| `image_height` | `image_height_filter(context, url)` | Returns actual image height in px using Pillow |

---

## Template Map

```python
TEMPLATE_MAP = {
  "university": "university.html",
  "course": "course.html",
  "specialization": "specialization.html",
  "blog": "blog.html",
  "programs_listing": "programs_listing.html",
  "specializations_listing": "specializations_listing.html",
  "blog_listing": "blog_listing.html",
}
```

---

## SEO and Structured Data

`_build_structured_data(ctx, resolved, raw, primary_domain)` builds JSON-LD graphs:

- **All pages:** `BreadcrumbList`
- **University:** `Organization`
- **Course/Specialization:** `Course` with `Offer` (if price available)
- **Course/Specialization/Blog:** `FAQPage` (if FAQs exist)

The `primary_domain` is read from `LEAD_BASE_URL` or workspace `metadata.json`.
Prices are extracted via `_schema_price()` which reads raw numeric values without inventing them.

---

## Syllabus and Admission HTML Parsers

`SyllabusHTMLParser` and `AdmissionHTMLParser` are Python `HTMLParser` subclasses.
They split HTML blob content (from the ACF syllabus/admission fields) into structured
JSON lists — e.g., semester-by-semester curriculum or step-by-step registration steps.
These structured lists are then passed to the template for clean rendering.

---

## Important Files

| File | Role |
|---|---|
| `backend/renderer/engine.py` | Entire rendering engine (~1380 lines) |
| `backend/templates/*.html` | 7 Jinja2 templates |
| `backend/core/router.py` | Dispatches page_type → transformer |

---

## Known Limitations

- **No caching:** Every `render_resolved()` call re-runs the transformer and re-renders
  the Jinja2 template. A Redis caching TODO exists at the top of `engine.py`.
- **`standalone` mode is partially implemented:** Some asset paths may still be workspace-relative
  in standalone renders. This affects the Preview screen when the admin UI serves the iframe.
- **`image_width` / `image_height` filters read from disk:** If the workspace image does not
  exist (not yet uploaded), these filters return `"0"`. This is safe but may cause `0x0` image
  dimensions in the rendered HTML.
