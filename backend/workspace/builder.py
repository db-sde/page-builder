"""
workspace/builder.py
────────────────────
Pass 4 — Website Export Builder.

Turns a compiled university workspace into a deployable static site
package under `workspaces/<uni>/build/`.

The page compiler (`compile_workspace`, Pass 1–3) is left untouched.
The builder is an opt-in stage that reads the already-compiled
`.html` files from the workspace folders, rewrites their internal
links to build-relative routes, copies assets, and emits a route
manifest + sitemap.

Build layout (target):
  build/
  ├── index.html                      ← University/university.html
  ├── programs/index.html             ← Pages/programs/programs_listing.html
  ├── specializations/index.html      ← Pages/specializations/specializations_listing.html
  ├── blog/index.html                 ← Pages/blog/blog_listing.html
  ├── blog/<slug>/index.html          ← Blogs/<slug>/blog.html
  ├── <course-slug>/index.html        ← Courses/<slug>/course.html
  ├── <spec-slug>/index.html          ← Specializations/<slug>/specialization.html
  ├── assets/
  │   ├── images/…                    ← Assets/images/
  │   ├── downloads/…                 ← Assets/downloads/  (if present)
  │   └── support.js                  ← runtime support script
  ├── routes.json                     ← route manifest
  └── sitemap.xml                     ← sitemap

Usage:
  from workspace.builder import build_website
  result = build_website("nodia")
"""

import json
import shutil
import zipfile
import io
import re
from pathlib import Path
from datetime import datetime, timezone
from html import escape as html_escape

from workspace.manager import (
    _workspace_root,
    _HTML_FILENAME,
    WORKSPACES_ROOT,
)
from workspace.compiler import _build_index


# Top-level reserved route segments — course/specialization slugs may
# not collide with these (they are used by the listing pages).
_RESERVED_SEGMENTS = {"programs", "specializations", "blog"}


# ── Path helpers ──────────────────────────────────────────────────────────────

def _build_root(university_slug: str) -> Path:
    return _workspace_root(university_slug) / "build"


def _build_root_v2(university_slug: str) -> Path:
    return _workspace_root(university_slug) / "build_v2"


def _locate_support_js() -> Path | None:
    """Find support.js using the same search order as main.py /support.js."""
    backend_root = Path(__file__).resolve().parent.parent
    candidates = [
        backend_root / "support.js",
        backend_root.parent / "support.js",
        backend_root.parent / "frontend" / "public" / "support.js",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


# ── Route map ─────────────────────────────────────────────────────────────────

def _build_route_map(index: dict, university_slug: str) -> tuple[dict, list[dict]]:
    """
    Return (route_map, route_errors).

    route_map shape:
      {
        "homepage":          "/",                       # key → route
        "programs_listing":  "/programs",
        "specializations_listing": "/specializations",
        "blog_listing":      "/blog",
        "course:<slug>":     "/<slug>",
        "specialization:<slug>": "/<slug>",
        "blog:<slug>":       "/blog/<slug>",
      }

    Also returns a flat slug → route map for URL rewriting:
      rewrite_map: { "<slug>": "/<route>" } for courses, specs, blogs.
    """
    errors: list[dict] = []
    route_map: dict[str, str] = {}

    # University homepage
    uni_records = list(index["university"].values())
    if uni_records:
        route_map["homepage"] = "/"

    # Listing pages — fixed routes
    route_map["programs_listing"] = "/programs"
    route_map["specializations_listing"] = "/specializations"
    route_map["blog_listing"] = "/blog"

    # Courses + specializations share the top-level namespace.
    # Detect collisions (same slug, or slug colliding with a reserved segment).
    seen_top: dict[str, str] = {}  # segment → page_type that claimed it

    for slug, _rec in index["course"].items():
        if not slug:
            continue
        if slug in _RESERVED_SEGMENTS:
            errors.append({
                "route": f"/{slug}",
                "error": f"Course slug '{slug}' collides with a reserved listing route",
            })
            continue
        if slug in seen_top:
            errors.append({
                "route": f"/{slug}",
                "error": (
                    f"Duplicate route /{slug}: claimed by {seen_top[slug]} "
                    f"and course"
                ),
            })
            continue
        seen_top[slug] = "course"
        route_map[f"course:{slug}"] = f"/{slug}"

    for slug, _rec in index["specialization"].items():
        if not slug:
            continue
        if slug in _RESERVED_SEGMENTS:
            errors.append({
                "route": f"/{slug}",
                "error": f"Specialization slug '{slug}' collides with a reserved listing route",
            })
            continue
        if slug in seen_top:
            errors.append({
                "route": f"/{slug}",
                "error": (
                    f"Duplicate route /{slug}: claimed by {seen_top[slug]} "
                    f"and specialization"
                ),
            })
            continue
        seen_top[slug] = "specialization"
        route_map[f"specialization:{slug}"] = f"/{slug}"

    # Blogs live under /blog/<slug> — never collide with top-level.
    for slug, _rec in index["blog"].items():
        if not slug:
            continue
        route_map[f"blog:{slug}"] = f"/blog/{slug}"

    return route_map, errors


def _rewrite_map_for_routes(route_map: dict) -> dict:
    """
    Build a {slug: route} map covering courses, specializations, blogs.
    Used to rewrite `{slug}.html` / `{slug}.dc.html` references.
    """
    rewrite: dict[str, str] = {}
    for key, route in route_map.items():
        if key.startswith(("course:", "specialization:", "blog:")):
            slug = key.split(":", 1)[1]
            rewrite[slug] = route
    return rewrite


# ── Validation ────────────────────────────────────────────────────────────────

# Which data fields reference image files on disk.
_IMAGE_FIELD_BY_TYPE = {
    "university": ["hero_image_url"],
    "course": ["hero_image_url", "certificate_image_url"],
    "specialization": ["hero_image_url"],
    "blog": ["hero_image_url"],
}


def _validate_pages(index: dict, university_slug: str) -> list[dict]:
    """Return a list of validation errors (empty if everything is OK)."""
    errors: list[dict] = []
    images_dir = _workspace_root(university_slug) / "Assets" / "images"

    # University must exist
    if not index["university"]:
        errors.append({"page_type": "university", "error": "No university page found in workspace"})

    course_slugs = set(index["course"].keys())

    user_types = ("university", "course", "specialization", "blog")
    for pt in user_types:
        for slug, record in index[pt].items():
            data = record.get("data", {}) or {}

            # Required image slots
            for slot in _IMAGE_FIELD_BY_TYPE.get(pt, []):
                val = data.get(slot)
                if not val:
                    errors.append({
                        "page_type": pt, "slug": slug,
                        "error": f"Missing required image: {slot}",
                    })
                    continue
                # If it's a local asset path, verify the file exists on disk
                if isinstance(val, str) and val.startswith("/assets/images/"):
                    fname = val.rsplit("/", 1)[-1]
                    if not (images_dir / fname).exists():
                        errors.append({
                            "page_type": pt, "slug": slug,
                            "error": f"Referenced image file not found: {fname} ({slot})",
                        })

            # Dangling parent_slug for specializations
            if pt == "specialization":
                parent = record.get("parent_slug")
                if parent and parent not in course_slugs:
                    errors.append({
                        "page_type": pt, "slug": slug,
                        "error": f"Dangling parent_slug '{parent}' (no such course)",
                    })

    return errors


# ── URL rewriting ─────────────────────────────────────────────────────────────

def _rewrite_html(
    html: str,
    university_slug: str,
    rewrite_map: dict,
) -> str:
    """
    Rewrite workspace-relative links to build-relative routes.

    Patterns handled:
      • ./support.js                 → /assets/support.js
      • {uni}.dc.html                → /                      (homepage)
      • programs_listing.html        → /programs/
      • specializations_listing.html → /specializations/
      • blog_listing.html            → /blog/
      • {uni}-blog.dc.html           → /blog/                 (blog_href)
      • listing JS: slug + '.html'   → '/' + slug + '/'
      • JSON blob:  "{slug}.html"    → "{route}/"
      • generic:    {slug}.dc.html   → {route}/               (fallback specs)
    """
    # 1. Runtime support script — make it root-absolute so it loads from
    #    /assets/support.js regardless of page depth.
    html = html.replace('src="./support.js"', 'src="/assets/support.js"')

    # 2. Shared navigation hrefs (identical strings across every page).
    html = html.replace(f'href="{university_slug}.dc.html"', 'href="/"')
    html = html.replace('href="programs_listing.html"', 'href="/programs/"')
    html = html.replace('href="specializations_listing.html"', 'href="/specializations/"')
    html = html.replace('href="blog_listing.html"', 'href="/blog/"')
    html = html.replace(f'href="{university_slug}-blog.dc.html"', 'href="/blog/"')

    # 3. Listing templates build card hrefs client-side as `slug + '.html'`.
    #    Rewrite the JS to produce `/' + slug + '/'`.
    html = html.replace(
        "p.slug ? p.slug + '.html' : '#'",
        "p.slug ? '/' + p.slug + '/' : '#'",
    )
    html = html.replace(
        "g.course_slug ? g.course_slug + '.html' : '#'",
        "g.course_slug ? '/' + g.course_slug + '/' : '#'",
    )
    html = html.replace(
        "sp.slug ? sp.slug + '.html' : '#'",
        "sp.slug ? '/' + sp.slug + '/' : '#'",
    )

    # 4. Blog post hrefs are pre-baked into JSON as "href": "{slug}.html".
    #    Also catch any generic {slug}.html / {slug}.dc.html references.
    #    Process longest slugs first so "online-mba" isn't shadowed by a
    #    shorter substring.
    for slug in sorted(rewrite_map.keys(), key=len, reverse=True):
        route = rewrite_map[slug]
        html = html.replace(f'href="{slug}.html"', f'href="{route}/"')
        html = html.replace(f'href="{slug}.dc.html"', f'href="{route}/"')
        html = html.replace(f'"href": "{slug}.html"', f'"href": "{route}/"')
        html = html.replace(f'"href":"{slug}.html"', f'"href":"{route}/"')

    return html


# ── Asset copy ────────────────────────────────────────────────────────────────

def _copy_dir_contents(src: Path, dst: Path) -> int:
    """Copy *contents* of src into dst (merging). Return file count."""
    if not src.exists() or not src.is_dir():
        return 0
    count = 0
    for item in src.rglob("*"):
        if item.is_file():
            rel = item.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            count += 1
    return count


# ── Manifests ─────────────────────────────────────────────────────────────────

def _write_routes_json(build_dir: Path, route_map: dict, kind_label: dict) -> None:
    """Write build/routes.json — { route: page_type_label }."""
    # Order: homepage first, then listings, then courses/specs/blogs sorted.
    ordered: dict[str, str] = {}
    if "homepage" in route_map:
        ordered["/"] = kind_label.get("homepage", "homepage")
    for key in ("programs_listing", "specializations_listing", "blog_listing"):
        if key in route_map:
            ordered[route_map[key]] = kind_label.get(key, key)
    rest = {
        route_map[k]: kind_label.get(k, k)
        for k in route_map
        if k not in ("homepage", "programs_listing", "specializations_listing", "blog_listing")
    }
    for r in sorted(rest.keys()):
        ordered[r] = rest[r]

    (build_dir / "routes.json").write_text(
        json.dumps(ordered, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_sitemap(
    build_dir: Path,
    route_map: dict,
    index: dict,
    university_slug: str,
    last_compiled_at: str | None,
) -> None:
    """Write build/sitemap.xml covering all routes."""
    meta_path = _workspace_root(university_slug) / "metadata.json"
    base_domain = ""
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            base_domain = (meta.get("site_url") or meta.get("domain") or "").rstrip("/")
        except Exception:
            pass

    def _lastmod(record: dict | None) -> str:
        if not record:
            return last_compiled_at or ""
        return record.get("saved_at") or last_compiled_at or ""

    lines: list[str] = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    )

    def _add(route: str, lastmod: str = "", priority: str = ""):
        loc = f"{base_domain}{route}" if base_domain else route
        lines.append("  <url>")
        lines.append(f"    <loc>{html_escape(loc)}</loc>")
        if lastmod:
            # Trim to YYYY-MM-DD for spec compliance
            lines.append(f"    <lastmod>{lastmod[:10]}</lastmod>")
        if priority:
            lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")

    if "homepage" in route_map:
        _add("/", _lastmod(index["university"].get(next(iter(index["university"]), "")) if index["university"] else None), "1.0")
    for key, route in route_map.items():
        if key == "homepage":
            continue
        if key == "programs_listing":
            _add(route, "0.9")
        elif key in ("specializations_listing", "blog_listing"):
            _add(route, "0.8")
        elif key.startswith("course:"):
            slug = key.split(":", 1)[1]
            _add(route, _lastmod(index["course"].get(slug)), "0.7")
        elif key.startswith("specialization:"):
            slug = key.split(":", 1)[1]
            _add(route, _lastmod(index["specialization"].get(slug)), "0.6")
        elif key.startswith("blog:"):
            slug = key.split(":", 1)[1]
            _add(route, _lastmod(index["blog"].get(slug)), "0.5")

    lines.append("</urlset>")
    (build_dir / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")


def _write_robots_txt(
    build_dir: Path,
    university_slug: str,
) -> None:
    """Write build/robots.txt covering indexing rules and pointing to sitemap."""
    meta_path = _workspace_root(university_slug) / "metadata.json"
    base_domain = ""
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            base_domain = (meta.get("site_url") or meta.get("domain") or "").rstrip("/")
        except Exception:
            pass

    sitemap_url = f"{base_domain}/sitemap.xml" if base_domain else "/sitemap.xml"
    content = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {sitemap_url}\n"
    )
    (build_dir / "robots.txt").write_text(content, encoding="utf-8")


# ── Public API ────────────────────────────────────────────────────────────────

def build_website(university_slug: str) -> dict:
    """
    Build a deployable static website package for a university workspace.

    Reads already-compiled .html files from the workspace folders
    (run `compile_workspace` first — this builder does not re-render
    templates), rewrites links, copies assets, and emits routes.json +
    sitemap.xml under workspaces/<uni>/build/.

    Returns a summary dict:
      {
        "university_slug", "build_path", "build_url",
        "pages_compiled", "pages_failed",
        "images_copied", "downloads_copied",
        "routes_generated", "routes": [...],
        "errors": [...],
        "built_at": ISO timestamp,
      }
    """
    university_slug = university_slug.lower().strip()
    ws_root = _workspace_root(university_slug)
    build_dir = _build_root(university_slug)

    errors: list[dict] = []
    pages_compiled = 0
    pages_failed = 0

    # ── Pass A: index + validate ────────────────────────────────────────────
    index = _build_index(university_slug)

    validation_errors = _validate_pages(index, university_slug)
    errors.extend(validation_errors)

    # Read last_compiled_at for sitemap fallback
    last_compiled_at = None
    meta_path = ws_root / "metadata.json"
    if meta_path.exists():
        try:
            last_compiled_at = json.loads(meta_path.read_text(encoding="utf-8")).get("last_compiled_at")
        except Exception:
            pass

    # ── Pass B: route map + collision detection ─────────────────────────────
    route_map, route_errors = _build_route_map(index, university_slug)
    errors.extend(route_errors)
    rewrite_map = _rewrite_map_for_routes(route_map)

    # ── Pass C: reset build dir ─────────────────────────────────────────────
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "assets").mkdir(parents=True, exist_ok=True)

    # ── Pass D: export pages ────────────────────────────────────────────────
    # (page_type_key, source_html_resolver) → (build_subpath)
    export_specs: list[tuple[str, str, str]] = []  # (kind, slug, build_rel_dir)

    def _export(html_path: Path, build_rel_dir: str, kind: str, slug: str) -> None:
        nonlocal pages_compiled, pages_failed
        if not html_path.exists():
            pages_failed += 1
            errors.append({
                "page_type": kind, "slug": slug,
                "error": f"Compiled HTML not found: {html_path}",
            })
            return
        try:
            html = html_path.read_text(encoding="utf-8")
            html = _rewrite_html(html, university_slug, rewrite_map)
            out_dir = build_dir / build_rel_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(html, encoding="utf-8")
            pages_compiled += 1
            export_specs.append((kind, slug, build_rel_dir))
        except Exception as e:  # pragma: no cover - defensive
            pages_failed += 1
            errors.append({"page_type": kind, "slug": slug, "error": str(e)})

    # Homepage
    if index["university"]:
        rec = next(iter(index["university"].values()))
        uni_html = ws_root / "University" / _HTML_FILENAME["university"]
        _export(uni_html, "", "homepage", rec.get("slug", university_slug))

    # Listings
    listing_dirs = {
        "programs_listing": (Path("Pages") / "programs", "programs"),
        "specializations_listing": (Path("Pages") / "specializations", "specializations"),
        "blog_listing": (Path("Pages") / "blog", "blog"),
    }
    for kind, (sub, build_sub) in listing_dirs.items():
        html_path = ws_root / sub / _HTML_FILENAME[kind]
        _export(html_path, build_sub, kind, kind)

    # Courses
    for slug, rec in index["course"].items():
        if slug in _RESERVED_SEGMENTS:
            continue  # already reported as collision
        html_path = ws_root / "Courses" / slug / _HTML_FILENAME["course"]
        _export(html_path, slug, "course", slug)

    # Specializations
    for slug, rec in index["specialization"].items():
        if slug in _RESERVED_SEGMENTS:
            continue
        html_path = ws_root / "Specializations" / slug / _HTML_FILENAME["specialization"]
        _export(html_path, slug, "specialization", slug)

    # Blogs
    for slug, rec in index["blog"].items():
        html_path = ws_root / "Blogs" / slug / _HTML_FILENAME["blog"]
        _export(html_path, f"blog/{slug}", "blog", slug)

    # ── Pass E: copy assets ─────────────────────────────────────────────────
    images_copied = 0
    downloads_copied = 0

    src_images = ws_root / "Assets" / "images"
    if src_images.exists():
        images_copied = _copy_dir_contents(src_images, build_dir / "assets" / "images")

    src_downloads = ws_root / "Assets" / "downloads"
    if src_downloads.exists():
        downloads_copied = _copy_dir_contents(src_downloads, build_dir / "assets" / "downloads")

    # Runtime support script (optional — listing pages are now fully static;
    # detail pages (course, specialization, blog) still use it for DC runtime)
    support_src = _locate_support_js()
    if support_src:
        shutil.copy2(support_src, build_dir / "assets" / "support.js")
    # Note: absence of support.js is no longer a hard error since listing pages
    # are now server-side rendered. Detail pages may degrade gracefully.

    # ── Pass F: manifests ────────────────────────────────────────────────────
    kind_label = {
        "homepage": "homepage",
        "programs_listing": "programs_listing",
        "specializations_listing": "specializations_listing",
        "blog_listing": "blog_listing",
    }
    for key in route_map:
        if key.startswith("course:"):
            kind_label[key] = "course"
        elif key.startswith("specialization:"):
            kind_label[key] = "specialization"
        elif key.startswith("blog:"):
            kind_label[key] = "blog"

    _write_routes_json(build_dir, route_map, kind_label)
    _write_sitemap(build_dir, route_map, index, university_slug, last_compiled_at)
    _write_robots_txt(build_dir, university_slug)

    built_at = datetime.now(timezone.utc).isoformat()

    return {
        "university_slug": university_slug,
        "build_path": str(build_dir),
        "build_url": f"/build-file?university_slug={university_slug}&path=index.html",
        "pages_compiled": pages_compiled,
        "pages_failed": pages_failed,
        "images_copied": images_copied,
        "downloads_copied": downloads_copied,
        "routes_generated": len(route_map),
        "routes": [
            {"route": route, "type": kind_label[k], "slug": k.split(":", 1)[1] if ":" in k else None}
            for k, route in route_map.items()
        ],
        "errors": errors,
        "built_at": built_at,
    }


def build_website_v2(university_slug: str) -> dict:
    """
    Build a deployable static website package for a university workspace using V2 assets.
    """
    university_slug = university_slug.lower().strip()
    ws_root = _workspace_root(university_slug)
    build_dir = _build_root_v2(university_slug)

    errors: list[dict] = []
    pages_compiled = 0
    pages_failed = 0

    # ── Pass A: index + validate ────────────────────────────────────────────
    index = _build_index(university_slug)

    validation_errors = _validate_pages(index, university_slug)
    errors.extend(validation_errors)

    # Read last_compiled_at for sitemap fallback
    last_compiled_at = None
    meta_path = ws_root / "metadata.json"
    if meta_path.exists():
        try:
            last_compiled_at = json.loads(meta_path.read_text(encoding="utf-8")).get("last_compiled_at")
        except Exception:
            pass

    # ── Pass B: route map + collision detection ─────────────────────────────
    route_map, route_errors = _build_route_map(index, university_slug)
    errors.extend(route_errors)
    rewrite_map = _rewrite_map_for_routes(route_map)

    # ── Pass C: reset build dir ─────────────────────────────────────────────
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "assets").mkdir(parents=True, exist_ok=True)

    # ── Pass D: export pages ────────────────────────────────────────────────
    export_specs: list[tuple[str, str, str]] = []  # (kind, slug, build_rel_dir)

    def _export(html_path: Path, build_rel_dir: str, kind: str, slug: str) -> None:
        nonlocal pages_compiled, pages_failed
        if not html_path.exists():
            pages_failed += 1
            errors.append({
                "page_type": kind, "slug": slug,
                "error": f"Compiled HTML not found: {html_path}",
            })
            return
        try:
            html = html_path.read_text(encoding="utf-8")
            html = _rewrite_html(html, university_slug, rewrite_map)
            out_dir = build_dir / build_rel_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(html, encoding="utf-8")
            pages_compiled += 1
            export_specs.append((kind, slug, build_rel_dir))
        except Exception as e:
            pages_failed += 1
            errors.append({"page_type": kind, "slug": slug, "error": str(e)})

    # Homepage
    if index["university"]:
        rec = next(iter(index["university"].values()))
        uni_html = ws_root / "University" / _HTML_FILENAME["university"]
        _export(uni_html, "", "homepage", rec.get("slug", university_slug))

    # Listings
    listing_dirs = {
        "programs_listing": (Path("Pages") / "programs", "programs"),
        "specializations_listing": (Path("Pages") / "specializations", "specializations"),
        "blog_listing": (Path("Pages") / "blog", "blog"),
    }
    for kind, (sub, build_sub) in listing_dirs.items():
        html_path = ws_root / sub / _HTML_FILENAME[kind]
        _export(html_path, build_sub, kind, kind)

    # Courses
    for slug, rec in index["course"].items():
        if slug in _RESERVED_SEGMENTS:
            continue  # already reported as collision
        html_path = ws_root / "Courses" / slug / _HTML_FILENAME["course"]
        _export(html_path, slug, "course", slug)

    # Specializations
    for slug, rec in index["specialization"].items():
        if slug in _RESERVED_SEGMENTS:
            continue
        html_path = ws_root / "Specializations" / slug / _HTML_FILENAME["specialization"]
        _export(html_path, slug, "specialization", slug)

    # Blogs
    for slug, rec in index["blog"].items():
        html_path = ws_root / "Blogs" / slug / _HTML_FILENAME["blog"]
        _export(html_path, f"blog/{slug}", "blog", slug)

    # ── Pass E: copy assets ─────────────────────────────────────────────────
    images_copied = 0
    downloads_copied = 0

    src_images = ws_root / "Assets" / "images"
    if src_images.exists():
        images_copied = _copy_dir_contents(src_images, build_dir / "assets" / "images")

    src_downloads = ws_root / "Assets" / "downloads"
    if src_downloads.exists():
        downloads_copied = _copy_dir_contents(src_downloads, build_dir / "assets" / "downloads")

    # Copy V2 static assets (CSS/JS)
    static_v2_dir = Path(__file__).resolve().parent.parent / "static_v2"
    if static_v2_dir.exists():
        # Copy JS
        js_dst = build_dir / "assets" / "js"
        js_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(static_v2_dir / "assets" / "js" / "public-runtime.js", js_dst / "public-runtime.js")
        
        # Copy CSS
        css_dst = build_dir / "assets" / "css"
        css_dst.mkdir(parents=True, exist_ok=True)
        for css_file in (static_v2_dir / "assets" / "css").glob("*.css"):
            shutil.copy2(css_file, css_dst / css_file.name)

    # ── Pass F: manifests ────────────────────────────────────────────────────
    kind_label = {
        "homepage": "homepage",
        "programs_listing": "programs_listing",
        "specializations_listing": "specializations_listing",
        "blog_listing": "blog_listing",
    }
    for key in route_map:
        if key.startswith("course:"):
            kind_label[key] = "course"
        elif key.startswith("specialization:"):
            kind_label[key] = "specialization"
        elif key.startswith("blog:"):
            kind_label[key] = "blog"

    _write_routes_json(build_dir, route_map, kind_label)
    _write_sitemap(build_dir, route_map, index, university_slug, last_compiled_at)
    _write_robots_txt(build_dir, university_slug)

    built_at = datetime.now(timezone.utc).isoformat()

    return {
        "university_slug": university_slug,
        "build_path": str(build_dir),
        "build_url": f"/build-file?university_slug={university_slug}&path=index.html",
        "pages_compiled": pages_compiled,
        "pages_failed": pages_failed,
        "images_copied": images_copied,
        "downloads_copied": downloads_copied,
        "routes_generated": len(route_map),
        "routes": [
            {"route": route, "type": kind_label[k], "slug": k.split(":", 1)[1] if ":" in k else None}
            for k, route in route_map.items()
        ],
        "errors": errors,
        "built_at": built_at,
    }


def get_build_status(university_slug: str) -> dict:
    """
    Return whether a build exists for a workspace, plus its routes/stats.
    Does NOT rebuild. Used by the frontend to render the Build panel.
    """
    university_slug = university_slug.lower().strip()
    build_dir = _build_root(university_slug)
    if not build_dir.exists():
        return {
            "university_slug": university_slug,
            "exists": False,
            "build_path": str(build_dir),
        }

    routes: dict = {}
    routes_path = build_dir / "routes.json"
    if routes_path.exists():
        try:
            routes = json.loads(routes_path.read_text(encoding="utf-8"))
        except Exception:
            routes = {}

    # Count page index.html files (exclude assets/, routes.json, sitemap.xml)
    page_count = 0
    for p in build_dir.rglob("index.html"):
        page_count += 1

    images = build_dir / "assets" / "images"
    images_copied = sum(1 for _ in images.rglob("*") if _.is_file()) if images.exists() else 0

    # mtime of routes.json as build timestamp proxy
    built_at = None
    if routes_path.exists():
        built_at = datetime.fromtimestamp(
            routes_path.stat().st_mtime, tz=timezone.utc
        ).isoformat()

    return {
        "university_slug": university_slug,
        "exists": True,
        "build_path": str(build_dir),
        "build_url": f"/build-file?university_slug={university_slug}&path=index.html",
        "routes": routes,
        "routes_count": len(routes),
        "pages_compiled": page_count,
        "images_copied": images_copied,
        "built_at": built_at,
    }


def zip_build(university_slug: str) -> tuple[bytes, str]:
    """
    Zip the build/ folder into an in-memory archive, compiling/rebuilding first
    to ensure it contains the absolute latest files, and packaging it inside
    a parent 'build/' folder.
    Returns (zip_bytes, filename).
    """
    university_slug = university_slug.lower().strip()

    # Compile & build the workspace first so the ZIP is always up to date
    from workspace.compiler import compile_workspace
    compile_workspace(university_slug)
    build_website(university_slug)

    build_dir = _build_root(university_slug)
    if not build_dir.exists():
        raise FileNotFoundError(f"No build found for workspace '{university_slug}'")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in build_dir.rglob("*"):
            if p.is_file():
                # Package inside a parent 'build/' directory in the ZIP
                arcname = Path("build") / p.relative_to(build_dir)
                zf.write(p, str(arcname))
    filename = f"{university_slug}-website.zip"
    return buf.getvalue(), filename


def zip_build_v2(university_slug: str) -> tuple[bytes, str]:
    """
    Zip the build_v2/ folder into an in-memory archive, compiling/rebuilding first.
    """
    university_slug = university_slug.lower().strip()

    from workspace.compiler import compile_workspace_v2
    compile_workspace_v2(university_slug)
    build_website_v2(university_slug)

    build_dir = _build_root_v2(university_slug)
    if not build_dir.exists():
        raise FileNotFoundError(f"No V2 build found for workspace '{university_slug}'")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in build_dir.rglob("*"):
            if p.is_file():
                # Package inside a parent 'build/' directory in the ZIP
                arcname = Path("build") / p.relative_to(build_dir)
                zf.write(p, str(arcname))
    filename = f"{university_slug}-website-v2.zip"
    return buf.getvalue(), filename
