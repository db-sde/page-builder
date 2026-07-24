# systems/templates.md — HTML Templates

## Purpose

Seven Jinja2 HTML templates — one per page type — define the visual structure of every
compiled page. Templates receive a context dict from the renderer and produce static HTML.

---

## Template Inventory

| Template | Page Type | Size |
|---|---|---|
| `university.html` | University homepage | ~30 KB |
| `course.html` | Course detail page | ~33 KB |
| `specialization.html` | Specialization detail page | ~32 KB |
| `blog.html` | Blog post page | ~16 KB |
| `programs_listing.html` | All courses listing | ~13 KB |
| `specializations_listing.html` | All specializations listing | ~12 KB |
| `blog_listing.html` | Blog directory page | ~13 KB |

All templates are in `backend/templates/`.

---

## Shared Template Elements

Every template includes:
- **Top bar** — `topbar_text` from `site_config` (e.g., "Admissions open · Limited seats")
- **Navigation header** — logo/letter badge, nav links, mobile hamburger menu
- **Sticky bar** — fee, CTA buttons, phone number
- **Footer** — `footer_columns` from `site_config`, copyright
- **WhatsApp float widget**
- **JSON-LD structured data** — injected by the renderer, not the template

---

## Context Variables (Universal)

| Variable | Source |
|---|---|
| `university_name` | Resolver → university page `source.json` → `metadata.json` → slug |
| `university_slug` | From `resolved` dict |
| `university_logo` | Workspace `Assets/images/` — logo filename |
| `branding_logo` | Same as `university_logo` |
| `site` | `get_site_config()` — nav links, footer, contact |
| `seo_title` | ACF field or transformer default |
| `meta_description` | ACF field or transformer default |
| `canonical_url` | Built from `primary_domain` + public route |
| `structured_data` | JSON-LD list, injected by renderer |

---

## Key Template Patterns

### Hidden Sections
If an optional section's data is `None` or empty, the section is hidden with a Jinja2
`{% if %}` check. Never use a placeholder. Example:
```jinja2
{% if about_content %}
<section id="about">{{ about_content|safe }}</section>
{% endif %}
```

### `de` Filter
Use `{{ value|de }}` instead of `{{ value or "" }}` for `None`-safe output.
The `de` filter (default_empty) returns `""` if the value is `None`.

### WebP Images
Templates use `<picture>` elements with `webp_variant` filter for responsive images:
```jinja2
<picture>
  <source srcset="{{ hero_image_url|webp_variant(480) }} 480w,
                  {{ hero_image_url|webp_variant(768) }} 768w"
          type="image/webp">
  <img src="{{ hero_image_url }}" alt="..." loading="lazy">
</picture>
```

### CTA Links
All CTA buttons use `lead_url` (computed in transformers) — a pre-built URL pointing to
`LEAD_BASE_URL/form?d={base64_payload}`. Never hardcode CTA URLs in templates.

### University Logo Badge
When `university_logo` is empty, templates render an auto-generated letter badge:
```jinja2
{% if university_logo %}
  <img src="{{ university_logo }}" alt="{{ university_name }}">
{% else %}
  <div class="logo-badge">{{ university_name[0]|upper }}</div>
{% endif %}
```

---

## Responsive Breakpoints

| Breakpoint | Effect |
|---|---|
| `768px` | Desktop nav hidden → hamburger; grids → 2-col or 1-col; footer stacks |
| `640px` | All card grids → 1-col |

Fluid typography uses `rem` and `vh` units.

---

## Runtime JavaScript

Only `public-runtime.js` is loaded. It handles:
- Mobile hamburger menu toggle
- Accordion expand/collapse (FAQs, syllabus)
- Tab switching (specialization comparison, reviews)
- Sticky bar scroll behaviour

This file is bundled from `backend/static/assets/js/` into `build/assets/js/` by the builder.

---

## Known Limitations

- Templates are purpose-built for Indian ed-tech content. They are not general-purpose.
- Responsive refinement for 768–1024px range is listed as an open task.
- No template inheritance system — each template is self-contained (shares no Jinja2 `extends` hierarchy).
