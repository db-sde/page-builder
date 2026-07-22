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
  │   ├── css/…                       ← static stylesheets
  │   ├── fonts/…                     ← local web fonts
  │   └── js/public-runtime.js        ← browser interactions
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
from pathlib import Path
from datetime import datetime, timezone
from html import escape as html_escape

from workspace.manager import (
    _workspace_root,
    _HTML_FILENAME,
)
from workspace.compiler import _build_index
from core.utils import build_public_route, build_public_url


# Top-level reserved route segments — course/specialization slugs may
# not collide with these (they are used by the listing pages).
_RESERVED_SEGMENTS = {"programs", "specializations", "blog"}

import threading
_build_lock = threading.Lock()

def with_build_lock(func):
    def wrapper(*args, **kwargs):
        with _build_lock:
            return func(*args, **kwargs)
    return wrapper


# ── Path helpers ──────────────────────────────────────────────────────────────

def _build_root(university_slug: str) -> Path:
    return _workspace_root(university_slug) / "build"


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
        route_slug = build_public_route("course", slug, university_slug).lstrip("/")
        if route_slug in _RESERVED_SEGMENTS:
            errors.append({
                "route": f"/{route_slug}",
                "error": f"Course slug '{route_slug}' collides with a reserved listing route",
            })
            continue
        if route_slug in seen_top:
            errors.append({
                "route": f"/{route_slug}",
                "error": (
                    f"Duplicate route /{route_slug}: claimed by {seen_top[route_slug]} "
                    f"and course"
                ),
            })
            continue
        seen_top[route_slug] = "course"
        # Key uses raw filesystem slug; route uses normalized URL slug
        route_map[f"course:{slug}"] = build_public_route("course", slug, university_slug)

    for slug, _rec in index["specialization"].items():
        if not slug:
            continue
        route_slug = build_public_route("specialization", slug, university_slug).lstrip("/")
        if route_slug in _RESERVED_SEGMENTS:
            errors.append({
                "route": f"/{route_slug}",
                "error": f"Specialization slug '{route_slug}' collides with a reserved listing route",
            })
            continue
        if route_slug in seen_top:
            errors.append({
                "route": f"/{route_slug}",
                "error": (
                    f"Duplicate route /{route_slug}: claimed by {seen_top[route_slug]} "
                    f"and specialization"
                ),
            })
            continue
        seen_top[route_slug] = "specialization"
        route_map[f"specialization:{slug}"] = build_public_route("specialization", slug, university_slug)

    # Blogs live under /blog/<slug> — never collide with top-level.
    for slug, _rec in index["blog"].items():
        if not slug:
            continue
        route_map[f"blog:{slug}"] = build_public_route("blog", slug, university_slug)

    return route_map, errors


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

def _finalize_html(
    html: str,
    university_slug: str,
) -> str:
    """Apply final build-time additions without changing rendered routes."""
    # Insert Google tag (gtag.js) only for nmims-2
    if university_slug == "nmims-2":
        gtag_script = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-B2N0SZPDFD"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-B2N0SZPDFD');
</script>"""
        if "<head>" in html:
            html = html.replace("<head>", f"<head>\n{gtag_script}")
        elif "<HEAD>" in html:
            html = html.replace("<HEAD>", f"<HEAD>\n{gtag_script}")

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
            site_meta = meta.get("site") or {}
            base_domain = (site_meta.get("primary_domain") or meta.get("site_url") or meta.get("domain") or "").rstrip("/")
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
        loc = build_public_url(base_domain, route, is_homepage=(route == "/"))
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
            _add(route, lastmod=last_compiled_at, priority="0.9")
        elif key in ("specializations_listing", "blog_listing"):
            _add(route, lastmod=last_compiled_at, priority="0.8")
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
            site_meta = meta.get("site") or {}
            base_domain = (site_meta.get("primary_domain") or meta.get("site_url") or meta.get("domain") or "").rstrip("/")
        except Exception:
            pass

    sitemap_url = build_public_url(base_domain, "/sitemap.xml")
    content = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {sitemap_url}\n"
    )
    (build_dir / "robots.txt").write_text(content, encoding="utf-8")


# ── Public API ────────────────────────────────────────────────────────────────

@with_build_lock
def build_website(university_slug: str) -> dict:
    """
    Build a deployable static website package for a university workspace using static assets.
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

    # ── Pass C: reset build dir ─────────────────────────────────────────────
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "assets").mkdir(parents=True, exist_ok=True)

    # ── Pass D: export pages ────────────────────────────────────────────────
    export_specs: list[tuple[str, str, str]] = []  # (kind, slug, build_rel_dir)

    def _export(html_path: Path, build_rel_dir: str, kind: str, slug: str, is_listing: bool = False) -> None:
        nonlocal pages_compiled, pages_failed
        if not html_path.exists():
            if not is_listing:
                pages_failed += 1
            errors.append({
                "page_type": kind, "slug": slug,
                "error": f"Compiled HTML not found: {html_path}",
            })
            return
        try:
            html = html_path.read_text(encoding="utf-8")
            html = _finalize_html(html, university_slug)
            out_dir = build_dir / build_rel_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(html, encoding="utf-8")
            if not is_listing:
                pages_compiled += 1
            export_specs.append((kind, slug, build_rel_dir))
        except Exception as e:
            if not is_listing:
                pages_failed += 1
            errors.append({"page_type": kind, "slug": slug, "error": str(e)})

    # Homepage
    if index["university"]:
        rec = next(iter(index["university"].values()))
        uni_html = ws_root / "University" / _HTML_FILENAME["university"]
        _export(uni_html, "", "homepage", rec.get("slug", university_slug))

    # Listings (system listing shells, not counted in user page totals)
    listing_dirs = {
        "programs_listing": (Path("Pages") / "programs", "programs"),
        "specializations_listing": (Path("Pages") / "specializations", "specializations"),
        "blog_listing": (Path("Pages") / "blog", "blog"),
    }
    for kind, (sub, build_sub) in listing_dirs.items():
        html_path = ws_root / sub / _HTML_FILENAME[kind]
        _export(html_path, build_sub, kind, kind, is_listing=True)

    # Courses
    for slug, rec in index["course"].items():
        if slug in _RESERVED_SEGMENTS:
            continue  # already reported as collision
        # Use normalized route slug as the output directory (strips workspace numeric suffix)
        route_key = f"course:{slug}"
        build_rel_dir = route_map.get(route_key, f"/{slug}").lstrip("/")
        html_path = ws_root / "Courses" / slug / _HTML_FILENAME["course"]
        _export(html_path, build_rel_dir, "course", slug)

    # Specializations
    for slug, rec in index["specialization"].items():
        if slug in _RESERVED_SEGMENTS:
            continue
        route_key = f"specialization:{slug}"
        build_rel_dir = route_map.get(route_key, f"/{slug}").lstrip("/")
        html_path = ws_root / "Specializations" / slug / _HTML_FILENAME["specialization"]
        _export(html_path, build_rel_dir, "specialization", slug)

    # Blogs
    for slug, rec in index["blog"].items():
        html_path = ws_root / "Blogs" / slug / _HTML_FILENAME["blog"]
        _export(html_path, f"blog/{slug}", "blog", slug)

    # ── Pass E: copy assets ─────────────────────────────────────────────────
    images_copied = 0
    downloads_copied = 0

    src_images = ws_root / "Assets" / "images"
    if src_images.exists():
        from workspace.image_optimizer import optimize_images_pipeline
        opt_stats = optimize_images_pipeline(src_images, build_dir / "assets" / "images")
        images_copied = len(opt_stats)

    src_downloads = ws_root / "Assets" / "downloads"
    if src_downloads.exists():
        downloads_copied = _copy_dir_contents(src_downloads, build_dir / "assets" / "downloads")

    # Copy static assets (CSS/JS/Fonts)
    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists():
        # Copy JS
        js_dst = build_dir / "assets" / "js"
        js_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(static_dir / "assets" / "js" / "public-runtime.js", js_dst / "public-runtime.js")
        
        # Copy CSS
        css_dst = build_dir / "assets" / "css"
        css_dst.mkdir(parents=True, exist_ok=True)
        for css_file in (static_dir / "assets" / "css").glob("*.css"):
            shutil.copy2(css_file, css_dst / css_file.name)

        # Copy Fonts (WOFF2 + fonts.css) for local hosting
        fonts_src = static_dir / "assets" / "fonts"
        if fonts_src.exists():
            fonts_dst = build_dir / "assets" / "fonts"
            fonts_dst.mkdir(parents=True, exist_ok=True)
            for font_file in fonts_src.iterdir():
                if font_file.is_file():
                    shutil.copy2(font_file, fonts_dst / font_file.name)

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

    # Count page index.html files (exclude system listing pages: programs/, specializations/, blog/)
    page_count = 0
    listing_rel_paths = {"programs/index.html", "specializations/index.html", "blog/index.html"}
    for p in build_dir.rglob("index.html"):
        rel_path = p.relative_to(build_dir).as_posix()
        if rel_path not in listing_rel_paths:
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
    Zip the build/ folder into an in-memory archive, compiling/rebuilding first.
    """
    university_slug = university_slug.lower().strip()

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
