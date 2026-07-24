# systems/publishing.md — Builder & Static Site Export

## Purpose

Convert a fully compiled workspace (all `.html` files in the workspace directories)
into a deployable static site package under `workspaces/<uni>/build/`.

---

## Responsibilities

1. Build a clean route map (slug → URL path), detect collisions
2. Validate required images exist on disk
3. Copy and optimise images (PNG/JPG → WebP, responsive variants)
4. Copy static assets (CSS, fonts, JS)
5. Rewrite internal dynamic link anchors to build-relative routes
6. Apply final HTML additions (`_finalize_html` — e.g., GA tag for nmims-2)
7. Write `routes.json` manifest
8. Write `sitemap.xml`
9. Write `robots.txt`
10. Optionally package build into a ZIP for download

---

## Inputs

- `university_slug` — which workspace to build
- A fully compiled workspace (all `source.json` and `.html` files up-to-date)

---

## Outputs

```
workspaces/<uni>/build/
  ├── index.html                      ← University homepage
  ├── programs/index.html
  ├── specializations/index.html
  ├── blog/index.html
  ├── blog/<slug>/index.html
  ├── <course-slug>/index.html
  ├── <spec-slug>/index.html
  ├── assets/
  │   ├── images/                     ← Original files + WebP variants
  │   │   ├── hero.jpg
  │   │   ├── hero.webp
  │   │   ├── hero-480.webp
  │   │   ├── hero-768.webp
  │   │   └── hero-1200.webp
  │   ├── css/
  │   ├── fonts/
  │   └── js/
  │       └── public-runtime.js
  ├── routes.json
  ├── sitemap.xml
  └── robots.txt
```

---

## Route Map Rules

- University homepage → `/`
- Programs listing → `/programs`
- Specializations listing → `/specializations`
- Blog listing → `/blog`
- Course pages → `/<course-slug>`
- Specialization pages → `/<spec-slug>`
- Blog posts → `/blog/<blog-slug>`

**Reserved segments:** `programs`, `specializations`, `blog` — course and specialization
slugs may not collide with these. The builder detects and reports collisions before building.

---

## Image Optimisation Pipeline

`workspace/image_optimizer.py`:
1. Copies original file to `build/assets/images/`
2. Generates base WebP at original dimensions (quality 82)
3. Generates responsive variants at 480w, 768w, 1200w
4. Skips generating a variant if its width ≥ original width

---

## Validation

`_validate_pages()` runs before any files are written. It checks:

1. A University page exists in the workspace
2. `hero_image_url` exists on disk for: university, course, specialization, blog
3. `certificate_image_url` exists on disk for: course
4. `parent_slug` for each specialization points to an existing course

If validation fails, errors are returned and the build does not proceed.

---

## Thread Safety

`builder.py` uses a `threading.Lock()` (`_build_lock`) around the build function.
Concurrent build requests for the same workspace are serialised.

---

## Important Files

| File | Role |
|---|---|
| `backend/workspace/builder.py` | Main builder logic (~629 lines) |
| `backend/workspace/image_optimizer.py` | WebP conversion and responsive variants |
| `backend/static/assets/` | Source CSS, fonts, JS bundled into build |

---

## API Endpoints

| Endpoint | Action |
|---|---|
| `POST /compile-workspace` | Two-pass compiler — indexes and re-renders all pages |
| `POST /build-website` | Static site exporter |
| `GET /build-status` | Current build status |
| `GET /download-build` | Download build as ZIP |

---

## Known Limitations

- **Full rebuild on every call:** The `build/` directory is wiped and fully rebuilt each time.
  Unchanged pages are still re-rendered. Caching is a future improvement.
- **Google Analytics injection is workspace-specific:** The `_finalize_html()` function
  currently only injects the GA tag for `nmims-2`. If other workspaces need analytics,
  this logic should be generalised (e.g., read GA ID from `metadata.json`).
- **Static assets must exist:** `backend/static/assets/css/`, `fonts/`, `js/` must be
  populated before building. They are checked implicitly — missing assets silently produce
  a build with missing CSS/fonts/JS.
