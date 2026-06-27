"""
workspace/builder.py
────────────────────
Pass 4 — Website Export Builder V2.

Turns a compiled university workspace into an optimized, SEO-ready,
fully static production build under `workspaces/<uni>/build/`.
"""

import json
import shutil
import zipfile
import io
import re
import os
from pathlib import Path
from datetime import datetime, timezone
from html import escape as html_escape

from workspace.manager import (
    _workspace_root,
    _HTML_FILENAME,
    WORKSPACES_ROOT,
)
from workspace.compiler import _build_index

# Top-level reserved route segments
_RESERVED_SEGMENTS = {"courses", "specializations", "blogs", "assets"}


# ── Path helpers ──────────────────────────────────────────────────────────────

def _build_root(university_slug: str) -> Path:
    return _workspace_root(university_slug) / "build"


# ── Route map ─────────────────────────────────────────────────────────────────

def _build_route_map(index: dict, university_slug: str) -> tuple[dict, list[dict]]:
    """
    Return (route_map, route_errors).
    """
    errors: list[dict] = []
    route_map: dict[str, str] = {}

    # University homepage
    uni_records = list(index["university"].values())
    if uni_records:
        route_map["homepage"] = "/"

    # Listing pages
    route_map["programs_listing"] = "/courses"
    route_map["specializations_listing"] = "/specializations"
    route_map["blog_listing"] = "/blogs"

    seen_top: dict[str, str] = {}

    for slug, _rec in index["course"].items():
        if not slug:
            continue
        if slug in _RESERVED_SEGMENTS:
            errors.append({
                "route": f"/courses/{slug}",
                "error": f"Course slug '{slug}' collides with a reserved segment",
            })
            continue
        route_map[f"course:{slug}"] = f"/courses/{slug}"

    for slug, _rec in index["specialization"].items():
        if not slug:
            continue
        if slug in _RESERVED_SEGMENTS:
            errors.append({
                "route": f"/specializations/{slug}",
                "error": f"Specialization slug '{slug}' collides with a reserved segment",
            })
            continue
        route_map[f"specialization:{slug}"] = f"/specializations/{slug}"

    for slug, _rec in index["blog"].items():
        if not slug:
            continue
        route_map[f"blog:{slug}"] = f"/blogs/{slug}"

    return route_map, errors


def _rewrite_map_for_routes(route_map: dict) -> dict:
    rewrite: dict[str, str] = {}
    for key, route in route_map.items():
        if key.startswith(("course:", "specialization:", "blog:")):
            slug = key.split(":", 1)[1]
            rewrite[slug] = route
    return rewrite


# ── HTML Minification ─────────────────────────────────────────────────────────

def minify_html(html: str) -> str:
    """Collapses whitespace, removes comments, and preserves scripts/pre."""
    blocks = []
    def save_block(match):
        placeholder = f"<!--__BLOCK_PLACEHOLDER_{len(blocks)}__-->"
        blocks.append(match.group(0))
        return placeholder

    # Temporarily extract tag blocks that should not be touched
    pattern = re.compile(r'<(pre|textarea|script|style)\b[^>]*>.*?</\1>', re.DOTALL | re.IGNORECASE)
    html_placeholder = pattern.sub(save_block, html)

    # Remove regular comments
    html_placeholder = re.sub(r'<!--(?!__BLOCK_PLACEHOLDER_)[\s\S]*?-->', '', html_placeholder)

    # Collapse spacing
    html_placeholder = re.sub(r'\s+', ' ', html_placeholder)
    html_placeholder = re.sub(r'>\s+<', '><', html_placeholder)

    # Re-inject blocks (and compact JSON-LD structure)
    for i, block in enumerate(blocks):
        placeholder = f"<!--__BLOCK_PLACEHOLDER_{i}__-->"
        if 'application/ld+json' in block:
            try:
                json_pat = re.compile(r'(<script\b[^>]*>)([\s\S]*?)(</script>)', re.IGNORECASE)
                m = json_pat.match(block)
                if m:
                    start_tag, json_content, end_tag = m.groups()
                    parsed = json.loads(json_content.strip())
                    compact_json = json.dumps(parsed, separators=(',', ':'))
                    block = f"{start_tag}{compact_json}{end_tag}"
            except Exception:
                pass
        html_placeholder = html_placeholder.replace(placeholder, block)

    return html_placeholder.strip()


# ── SEO Injectors ─────────────────────────────────────────────────────────────

def _inject_canonical(html: str, canonical_url: str) -> str:
    link_tag = f'\n  <link rel="canonical" href="{canonical_url}">'
    if "</head>" in html:
        return html.replace("</head>", f"{link_tag}\n</head>", 1)
    return html


def _inject_og_meta(html: str, record: dict, page_url: str, base_domain: str) -> str:
    data = record.get("data", {}) or {}
    title = record.get("seo_title") or data.get("title") or ""
    desc = record.get("meta_description") or data.get("excerpt") or data.get("description") or ""
    desc = re.sub(r'<[^>]*>', '', desc).strip()[:160]

    img = data.get("og_image_url") or data.get("hero_image_url") or ""
    if img and not img.startswith(("http://", "https://")):
        img = f"{base_domain}/{img.lstrip('/')}"

    meta_tags = []
    meta_tags.append(f'<meta property="og:title" content="{html_escape(title)}">')
    if desc:
        meta_tags.append(f'<meta property="og:description" content="{html_escape(desc)}">')
    if img:
        meta_tags.append(f'<meta property="og:image" content="{html_escape(img)}">')
    meta_tags.append(f'<meta property="og:url" content="{html_escape(page_url)}">')
    meta_tags.append('<meta property="og:type" content="website">')

    meta_tags.append('<meta name="twitter:card" content="summary_large_image">')
    meta_tags.append(f'<meta name="twitter:title" content="{html_escape(title)}">')
    if desc:
        meta_tags.append(f'<meta name="twitter:description" content="{html_escape(desc)}">')
    if img:
        meta_tags.append(f'<meta name="twitter:image" content="{html_escape(img)}">')

    meta_block = "\n  ".join(meta_tags)

    # Clean existing tags to avoid duplicate blocks
    html = re.sub(r'<meta property="og:[^>]+>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<meta name="twitter:[^>]+>', '', html, flags=re.IGNORECASE)

    if "</head>" in html:
        return html.replace("</head>", f"  {meta_block}\n</head>", 1)
    return html


# ── Structured Data ───────────────────────────────────────────────────────────

def _generate_json_ld(page_type: str, record: dict, page_url: str, base_domain: str, university_name: str) -> str:
    data = record.get("data", {}) or {}
    schemas = []

    # Breadcrumb List setup
    breadcrumbs = [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": base_domain}
    ]

    if page_type == "programs_listing":
        breadcrumbs.append({"@type": "ListItem", "position": 2, "name": "Courses", "item": f"{base_domain}/courses/"})
    elif page_type == "specializations_listing":
        breadcrumbs.append({"@type": "ListItem", "position": 2, "name": "Specialisations", "item": f"{base_domain}/specializations/"})
    elif page_type == "blog_listing":
        breadcrumbs.append({"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{base_domain}/blogs/"})
    elif page_type == "course":
        breadcrumbs.append({"@type": "ListItem", "position": 2, "name": "Courses", "item": f"{base_domain}/courses/"})
        course_name = data.get("program_name") or data.get("course_name") or record.get("slug", "").replace("-", " ").title()
        breadcrumbs.append({"@type": "ListItem", "position": 3, "name": course_name, "item": page_url})
    elif page_type == "specialization":
        breadcrumbs.append({"@type": "ListItem", "position": 2, "name": "Specialisations", "item": f"{base_domain}/specializations/"})
        spec_name = data.get("name") or record.get("slug", "").replace("-", " ").title()
        breadcrumbs.append({"@type": "ListItem", "position": 3, "name": spec_name, "item": page_url})
    elif page_type == "blog":
        breadcrumbs.append({"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{base_domain}/blogs/"})
        blog_title = data.get("title") or record.get("slug", "").replace("-", " ").title()
        breadcrumbs.append({"@type": "ListItem", "position": 3, "name": blog_title, "item": page_url})

    schemas.append({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumbs
    })

    if page_type in ("homepage", "university"):
        org_schema = {
            "@context": "https://schema.org",
            "@type": "CollegeOrUniversity",
            "@id": f"{base_domain}/#college",
            "name": university_name,
            "url": base_domain,
            "description": record.get("meta_description") or data.get("description") or "",
        }
        logo = data.get("branding", {}).get("logo") or data.get("hero_image_url")
        if logo:
            if not logo.startswith(("http://", "https://")):
                logo = f"{base_domain}/{logo.lstrip('/')}"
            org_schema["logo"] = logo
            org_schema["image"] = logo
        schemas.append(org_schema)

    elif page_type == "course":
        course_name = data.get("program_name") or data.get("course_name") or record.get("slug", "").replace("-", " ").title()
        desc = record.get("meta_description") or data.get("description") or ""
        desc = re.sub(r'<[^>]*>', '', desc).strip()

        schemas.append({
            "@context": "https://schema.org",
            "@type": "Course",
            "name": course_name,
            "description": desc,
            "provider": {
                "@type": "CollegeOrUniversity",
                "name": university_name,
                "url": base_domain
            }
        })
        schemas.append({
            "@context": "https://schema.org",
            "@type": "EducationalOccupationalProgram",
            "name": course_name,
            "description": desc,
            "provider": {
                "@type": "CollegeOrUniversity",
                "name": university_name,
                "url": base_domain
            }
        })

    elif page_type == "specialization":
        spec_name = data.get("name") or record.get("slug", "").replace("-", " ").title()
        desc = record.get("meta_description") or data.get("description") or ""
        desc = re.sub(r'<[^>]*>', '', desc).strip()

        schemas.append({
            "@context": "https://schema.org",
            "@type": "Course",
            "name": spec_name,
            "description": desc,
            "provider": {
                "@type": "CollegeOrUniversity",
                "name": university_name,
                "url": base_domain
            }
        })

    faqs = data.get("faqs")
    if faqs and isinstance(faqs, list):
        faq_entities = []
        for faq in faqs:
            q = faq.get("q")
            a = faq.get("a")
            if q and a:
                a_clean = re.sub(r'<[^>]*>', '', a).strip()
                faq_entities.append({
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": a_clean
                    }
                })
        if faq_entities:
            schemas.append({
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": faq_entities
            })

    script_tags = []
    for schema in schemas:
        script_tags.append(
            f'<script type="application/ld+json">\n{json.dumps(schema, separators=(",", ":"))}\n</script>'
        )
    return "\n".join(script_tags)


def _inject_json_ld(html: str, json_ld_block: str) -> str:
    if "</head>" in html:
        return html.replace("</head>", f"  {json_ld_block}\n</head>", 1)
    return html


# ── Asset copy & image optimization ──────────────────────────────────────────

def _optimize_and_copy_images(src_dir: Path, dst_dir: Path) -> int:
    if not src_dir.exists() or not src_dir.is_dir():
        return 0
    dst_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    from PIL import Image
    for item in src_dir.rglob("*"):
        if item.is_file():
            rel = item.relative_to(src_dir)
            target_orig = dst_dir / rel
            target_orig.parent.mkdir(parents=True, exist_ok=True)

            if item.suffix.lower() in (".jpg", ".jpeg", ".png"):
                try:
                    target_webp = dst_dir / rel.with_suffix(".webp")
                    with Image.open(item) as img:
                        # Resize if width > 1200
                        w, h = img.size
                        if w > 1200:
                            ratio = 1200.0 / w
                            img = img.resize((1200, int(h * ratio)), Image.Resampling.LANCZOS)

                        # Compress and save original format
                        if item.suffix.lower() in (".jpg", ".jpeg"):
                            img.convert("RGB").save(target_orig, "JPEG", quality=85)
                        elif item.suffix.lower() == ".png":
                            img.save(target_orig, "PNG", optimize=True)
                        else:
                            shutil.copy2(item, target_orig)

                        # Convert and save WebP version
                        img.convert("RGB").save(target_webp, "WEBP", quality=80)
                    count += 1
                except Exception:
                    try:
                        shutil.copy2(item, target_orig)
                        count += 1
                    except Exception:
                        pass
            else:
                try:
                    shutil.copy2(item, target_orig)
                except Exception:
                    pass
    return count


def _copy_dir_contents(src: Path, dst: Path) -> int:
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


# ── Performance Optimizations ─────────────────────────────────────────────────

def _optimize_html_images(html: str, build_dir: Path) -> str:
    from PIL import Image

    img_pattern = re.compile(r'<img\b([^>]*?)>', re.IGNORECASE)
    src_pattern = re.compile(r'src="([^"]+)"', re.IGNORECASE)
    width_pattern = re.compile(r'\bwidth="[^"]+"', re.IGNORECASE)
    height_pattern = re.compile(r'\bheight="[^"]+"', re.IGNORECASE)
    loading_pattern = re.compile(r'\bloading="[^"]+"', re.IGNORECASE)
    fetchpriority_pattern = re.compile(r'\bfetchpriority="[^"]+"', re.IGNORECASE)

    img_matches = list(img_pattern.finditer(html))
    if not img_matches:
        return html

    first_hero_idx = -1
    for i, m in enumerate(img_matches):
        attrs = m.group(1)
        src_m = src_pattern.search(attrs)
        if src_m:
            src = src_m.group(1).lower()
            if "logo" not in src and "favicon" not in src and "icon" not in src:
                first_hero_idx = i
                break

    for match in reversed(img_matches):
        img_tag = match.group(0)
        attrs = match.group(1)

        src_m = src_pattern.search(attrs)
        if not src_m:
            continue

        src = src_m.group(1)
        if src.startswith("/assets/images/"):
            img_path = build_dir / src.lstrip("/")
            if img_path.exists():
                try:
                    with Image.open(img_path) as img:
                        w, h = img.size
                    attrs_clean = width_pattern.sub('', attrs)
                    attrs_clean = height_pattern.sub('', attrs_clean)
                    attrs = f' width="{w}" height="{h}"' + attrs_clean
                except Exception:
                    pass

        idx = img_matches.index(match)
        attrs = loading_pattern.sub('', attrs)
        attrs = fetchpriority_pattern.sub('', attrs)

        if idx == first_hero_idx:
            attrs = ' fetchpriority="high"' + attrs
        elif idx > first_hero_idx or first_hero_idx == -1:
            # Don't lazy load header logos
            src_lower = src.lower()
            if "logo" not in src_lower and "favicon" not in src_lower:
                attrs = ' loading="lazy"' + attrs

        new_tag = f'<img{attrs}>'
        start, end = match.span()
        html = html[:start] + new_tag + html[end:]

    return html


def _optimize_img_tags(html: str) -> str:
    """Wraps matching local images inside a <picture> element with WebP sources."""
    def img_replace(match):
        img_tag = match.group(0)
        src = match.group(1)
        webp_src = src.rsplit('.', 1)[0] + '.webp'
        return f'<picture><source srcset="{webp_src}" type="image/webp">{img_tag}</picture>'

    pattern = re.compile(r'<img\b[^>]*?src="(/assets/images/[^"]+?\.(jpg|jpeg|png))"[^>]*?>', re.IGNORECASE)
    return pattern.sub(img_replace, html)


# ── URL Rewriter ──────────────────────────────────────────────────────────────

def _rewrite_html(
    html: str,
    university_slug: str,
    rewrite_map: dict,
) -> str:
    """Rewrites links to align with production static structure."""
    # Shared links
    html = html.replace(f'href="{university_slug}.dc.html"', 'href="/"')
    html = html.replace('href="programs_listing.html"', 'href="/courses/"')
    html = html.replace('href="specializations_listing.html"', 'href="/specializations/"')
    html = html.replace('href="blog_listing.html"', 'href="/blogs/"')
    html = html.replace(f'href="{university_slug}-blog.dc.html"', 'href="/blogs/"')

    # support.js references mapped to site.js
    html = html.replace('src="./support.js"', 'src="/assets/js/site.js"')
    html = html.replace('src="support.js"', 'src="/assets/js/site.js"')
    html = html.replace('src="/support.js"', 'src="/assets/js/site.js"')

    # Client-side dynamic listing page link replacements
    html = html.replace(
        "p.slug ? p.slug + '.html' : '#'",
        "p.slug ? '/courses/' + p.slug + '/' : '#'",
    )
    html = html.replace(
        "g.course_slug ? g.course_slug + '.html' : '#'",
        "g.course_slug ? '/courses/' + g.course_slug + '/' : '#'",
    )
    html = html.replace(
        "sp.slug ? sp.slug + '.html' : '#'",
        "sp.slug ? '/specializations/' + sp.slug + '/' : '#'",
    )

    # General page mapping replacements
    for slug in sorted(rewrite_map.keys(), key=len, reverse=True):
        route = rewrite_map[slug]
        route_slash = route if route.endswith("/") else f"{route}/"
        html = html.replace(f'href="{slug}.html"', f'href="{route_slash}"')
        html = html.replace(f'href="{slug}.dc.html"', f'href="{route_slash}"')
        html = html.replace(f'"href": "{slug}.html"', f'"href": "{route_slash}"')
        html = html.replace(f'"href":"{slug}.html"', f'"href":"{route_slash}"')

    return html


# ── Server configuration ──────────────────────────────────────────────────────

def _write_netlify_toml(build_dir: Path) -> None:
    content = """[[headers]]
  for = "/"
  [headers.values]
    Cache-Control = "no-cache"

[[headers]]
  for = "/*.html"
  [headers.values]
    Cache-Control = "no-cache"

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public,max-age=31536000,immutable"
"""
    (build_dir / "netlify.toml").write_text(content, encoding="utf-8")


def _write_manifest_json(build_dir: Path, university_name: str) -> None:
    manifest = {
        "short_name": university_name,
        "name": f"{university_name} Online",
        "start_url": "/",
        "background_color": "#F6F4FB",
        "theme_color": "#6B4FC9",
        "display": "standalone"
    }
    (build_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _write_robots_txt(build_dir: Path, base_domain: str) -> None:
    sitemap_url = f"{base_domain}/sitemap.xml" if base_domain else "https://example.com/sitemap.xml"
    content = f"""User-agent: *
Allow: /

Sitemap: {sitemap_url}
"""
    (build_dir / "robots.txt").write_text(content, encoding="utf-8")


def _write_sitemap(
    build_dir: Path,
    route_map: dict,
    index: dict,
    university_slug: str,
    last_compiled_at: str | None,
) -> None:
    meta_path = _workspace_root(university_slug) / "metadata.json"
    base_domain = ""
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            base_domain = (meta.get("site_url") or meta.get("domain") or "").rstrip("/")
        except Exception:
            pass
    if not base_domain:
        base_domain = f"https://{university_slug}.degreebaba.com"

    def _lastmod(record: dict | None) -> str:
        if not record:
            return last_compiled_at or ""
        return record.get("saved_at") or last_compiled_at or ""

    lines: list[str] = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    def _add(route: str, lastmod: str = "", priority: str = ""):
        loc = f"{base_domain}{route}" if base_domain else route
        # Ensure trailing slash
        if loc != "/" and not loc.endswith("/"):
            loc += "/"
        lines.append("  <url>")
        lines.append(f"    <loc>{html_escape(loc)}</loc>")
        if lastmod:
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
            _add(route, priority="0.9")
        elif key in ("specializations_listing", "blog_listing"):
            _add(route, priority="0.8")
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


def _write_routes_json(build_dir: Path, route_map: dict, kind_label: dict) -> None:
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


# ── Validation ────────────────────────────────────────────────────────────────

_IMAGE_FIELD_BY_TYPE = {
    "university": ["hero_image_url"],
    "course": ["hero_image_url", "certificate_image_url"],
    "specialization": ["hero_image_url"],
    "blog": ["hero_image_url"],
}


def _validate_pages(index: dict, university_slug: str) -> list[dict]:
    errors: list[dict] = []
    images_dir = _workspace_root(university_slug) / "Assets" / "images"

    if not index["university"]:
        errors.append({"page_type": "university", "error": "No university page found in workspace"})

    course_slugs = set(index["course"].keys())

    for pt in ("university", "course", "specialization", "blog"):
        for slug, record in index[pt].items():
            data = record.get("data", {}) or {}

            for slot in _IMAGE_FIELD_BY_TYPE.get(pt, []):
                val = data.get(slot)
                if not val:
                    errors.append({
                        "page_type": pt, "slug": slug,
                        "error": f"Missing required image: {slot}",
                    })
                    continue
                if isinstance(val, str) and val.startswith("/assets/images/"):
                    fname = val.rsplit("/", 1)[-1]
                    if not (images_dir / fname).exists():
                        errors.append({
                            "page_type": pt, "slug": slug,
                            "error": f"Referenced image file not found: {fname} ({slot})",
                        })

            if pt == "specialization":
                parent = record.get("parent_slug")
                if parent and parent not in course_slugs:
                    errors.append({
                        "page_type": pt, "slug": slug,
                        "error": f"Dangling parent_slug '{parent}' (no such course)",
                    })

    return errors


# ── Public API V2 ─────────────────────────────────────────────────────────────

def build_website(university_slug: str) -> dict:
    """
    V2 website builder. Transforms pages and assets into optimized static builds.
    """
    university_slug = university_slug.lower().strip()
    ws_root = _workspace_root(university_slug)
    build_dir = _build_root(university_slug)

    errors: list[dict] = []
    pages_compiled = 0
    pages_failed = 0

    index = _build_index(university_slug)
    errors.extend(_validate_pages(index, university_slug))

    # Dynamic domain setup
    base_domain = ""
    meta_path = ws_root / "metadata.json"
    last_compiled_at = None
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            base_domain = (meta.get("site_url") or meta.get("domain") or "").rstrip("/")
            last_compiled_at = meta.get("last_compiled_at")
        except Exception:
            pass
    if not base_domain:
        base_domain = f"https://{university_slug}.degreebaba.com"

    # Resolve University Name
    uni_name = university_slug.replace("-", " ").title()
    if index["university"]:
        rec = next(iter(index["university"].values()))
        uni_name = rec.get("data", {}).get("university_name") or rec.get("data", {}).get("university_full_name") or uni_name

    route_map, route_errors = _build_route_map(index, university_slug)
    errors.extend(route_errors)
    rewrite_map = _rewrite_map_for_routes(route_map)

    # 1. Reset build directory
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    # 2. Optimize and copy Assets (Pre-copy so images can be sized during export)
    images_copied = 0
    downloads_copied = 0

    src_images = ws_root / "Assets" / "images"
    if src_images.exists():
        images_copied = _optimize_and_copy_images(src_images, build_dir / "assets" / "images")

    src_downloads = ws_root / "Assets" / "downloads"
    if src_downloads.exists():
        downloads_copied = _copy_dir_contents(src_downloads, build_dir / "assets" / "downloads")

    # Copy shared stylesheet and script from templates
    backend_dir = Path(__file__).resolve().parent.parent
    src_css = backend_dir / "templates" / "assets" / "css" / "main.css"
    src_js = backend_dir / "templates" / "assets" / "js" / "site.js"

    if src_css.exists():
        dst_css = build_dir / "assets" / "css" / "main.css"
        dst_css.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_css, dst_css)
    if src_js.exists():
        dst_js = build_dir / "assets" / "js" / "site.js"
        dst_js.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_js, dst_js)

    # 3. Export Pages
    export_specs = []

    def _export(html_path: Path, build_rel_dir: str, kind: str, slug: str, record: dict) -> None:
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

            # Inject canonical url
            route = route_map.get(f"{kind}:{slug}") or route_map.get(kind) or f"/{build_rel_dir}"
            route_slash = route if route.endswith("/") else f"{route}/"
            page_url = f"{base_domain}{route_slash}" if base_domain else route_slash
            html = _inject_canonical(html, page_url)

            # Inject structured data
            json_ld_block = _generate_json_ld(kind, record, page_url, base_domain, uni_name)
            html = _inject_json_ld(html, json_ld_block)

            # Inject OG and social tags
            html = _inject_og_meta(html, record, page_url, base_domain)

            # Lazy load below fold images & fetchpriority high on hero
            html = _optimize_html_images(html, build_dir)
            html = _optimize_img_tags(html)

            # Minify HTML
            html = minify_html(html)

            out_dir = build_dir / build_rel_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(html, encoding="utf-8")
            pages_compiled += 1
            export_specs.append((kind, slug, build_rel_dir))
        except Exception as e:
            pages_failed += 1
            errors.append({"page_type": kind, "slug": slug, "error": f"{str(e)}"})

    # Homepage
    if index["university"]:
        rec = next(iter(index["university"].values()))
        uni_html = ws_root / "University" / _HTML_FILENAME["university"]
        _export(uni_html, "", "homepage", rec.get("slug", university_slug), rec)

    # Listings
    _export(ws_root / "Pages" / "programs" / _HTML_FILENAME["programs_listing"], "courses", "programs_listing", "courses", {})
    _export(ws_root / "Pages" / "specializations" / _HTML_FILENAME["specializations_listing"], "specializations", "specializations_listing", "specializations", {})
    _export(ws_root / "Pages" / "blog" / _HTML_FILENAME["blog_listing"], "blogs", "blog_listing", "blogs", {})

    # Courses
    for slug, rec in index["course"].items():
        if slug in _RESERVED_SEGMENTS:
            continue
        html_path = ws_root / "Courses" / slug / _HTML_FILENAME["course"]
        _export(html_path, f"courses/{slug}", "course", slug, rec)

    # Specializations
    for slug, rec in index["specialization"].items():
        if slug in _RESERVED_SEGMENTS:
            continue
        html_path = ws_root / "Specializations" / slug / _HTML_FILENAME["specialization"]
        _export(html_path, f"specializations/{slug}", "specialization", slug, rec)

    # Blogs
    for slug, rec in index["blog"].items():
        html_path = ws_root / "Blogs" / slug / _HTML_FILENAME["blog"]
        _export(html_path, f"blogs/{slug}", "blog", slug, rec)

    # 4. Generate SEO, Netlify config, and manifests
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
    _write_robots_txt(build_dir, base_domain)
    _write_netlify_toml(build_dir)
    _write_manifest_json(build_dir, uni_name)

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

    page_count = 0
    for p in build_dir.rglob("index.html"):
        page_count += 1

    images = build_dir / "assets" / "images"
    images_copied = sum(1 for _ in images.rglob("*") if _.is_file()) if images.exists() else 0

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
                arcname = Path("build") / p.relative_to(build_dir)
                zf.write(p, str(arcname))
    filename = f"{university_slug}-website.zip"
    return buf.getvalue(), filename
