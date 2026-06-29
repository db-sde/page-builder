"""
workspace/compiler.py
──────────────────────
Two-pass workspace compiler.

Pass 1 — Index:
  Scan all source.json files in the workspace.
  Build a global_map:
    {
      "university":               { slug → record },
      "course":                   { slug → record },
      "specialization":           { slug → record },   ← FLAT (no parent nesting)
      "blog":                     { slug → record },
      "programs_listing":         { slug → record },
      "specializations_listing":  { slug → record },
      "blog_listing":             { slug → record },
    }

Pass 2 — Render:
  For each source.json, inject parent/sibling context resolved
  from the global_map, then re-render the Jinja2 template and
  overwrite the .html file.

  System listing pages (programs, specializations, blog) are
  automatically re-rendered with fresh workspace data after
  all user-content pages are processed.

Usage:
  from workspace.compiler import compile_workspace
  result = compile_workspace("nmims")
"""

import json
from pathlib import Path
from datetime import datetime, timezone

from workspace.manager import (
    list_all_source_files,
    read_source,
    resolve_page_dir,
    ensure_metadata,
    _workspace_root,
    _HTML_FILENAME,
    WORKSPACES_ROOT,
    SYSTEM_PAGE_TYPES,
    SYSTEM_PAGE_SLUGS,
)


# ── Pass 1: Build global index ────────────────────────────────────────────────

_ALL_PAGE_TYPES = {
    "university",
    "course",
    "specialization",
    "blog",
    "programs_listing",
    "specializations_listing",
    "blog_listing",
}

def _build_index(university_slug: str) -> dict:
    """
    Scan the workspace and return a dict keyed by page_type.
    Listing pages (programs_listing, specializations_listing, blog_listing)
    are included so the compiler can re-render them in Pass 2.
    """
    index = {pt: {} for pt in _ALL_PAGE_TYPES}

    for src_path in list_all_source_files(university_slug):
        record = read_source(src_path)
        if not record:
            continue

        pt = record.get("page_type")
        slug = record.get("slug")

        if not pt or not slug or pt not in index:
            continue

        index[pt][slug] = record

    return index


# ── Pass 2: Enrich + re-render ────────────────────────────────────────────────

def _build_workspace_course_list(index: dict, university_slug: str) -> list:
    """Return compact course descriptors for injection into other pages."""
    courses = []
    for r in index["course"].values():
        if r.get("university_slug") == university_slug:
            courses.append({
                "slug": r.get("slug"),
                "parent_slug": r.get("parent_slug"),
                "university_slug": r.get("university_slug"),
                "data": r.get("data", {}),
            })
    return courses


def _build_workspace_spec_list(index: dict, university_slug: str) -> list:
    """Return compact spec descriptors for injection into other pages."""
    specs = []
    for r in index["specialization"].values():
        if r.get("university_slug") == university_slug:
            specs.append({
                "slug": r.get("slug"),
                "parent_slug": r.get("parent_slug"),
                "university_slug": r.get("university_slug"),
                "data": r.get("data", {}),
            })
    return specs


def _build_workspace_blog_list(index: dict, university_slug: str) -> list:
    """Return compact blog descriptors for injection into other pages."""
    blogs = []
    for r in index["blog"].values():
        if r.get("university_slug") == university_slug:
            blogs.append({
                "slug": r.get("slug"),
                "university_slug": r.get("university_slug"),
                "data": r.get("data", {}),
            })
    return blogs


def _resolve_university_context(university_slug: str, index: dict) -> dict:
    """
    Resolve display fields for this workspace: prefer the university page's
    own data, then workspace metadata.json, then a title-cased slug.

    Shared by _enrich_resolved and _auto_render_listing_pages — previously
    this same "look up uni_record in the index, else fall back to
    metadata.json, else title-case the slug" block was duplicated almost
    verbatim in both functions.

    Returns: {"name", "full_name", "short_name", "logo"} — only "name" is
    guaranteed to be non-empty.
    """
    result = {"name": None, "full_name": None, "short_name": None, "logo": None}

    if index.get("university"):
        uni_record = index["university"].get(university_slug)
        if not uni_record:
            uni_records = list(index["university"].values())
            if uni_records:
                uni_record = uni_records[0]
        if uni_record:
            uni_data = uni_record.get("data") or {}
            result["name"] = uni_data.get("university_name")
            result["full_name"] = uni_data.get("university_full_name")
            result["short_name"] = uni_data.get("university_short_name")
            result["logo"] = uni_data.get("university_logo")

    if not result["name"]:
        meta = {}
        meta_path = _workspace_root(university_slug) / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
            except Exception:
                pass
        result["name"] = meta.get("university_name") or university_slug.replace("-", " ").title()

    return result


def _enrich_resolved(record: dict, index: dict) -> dict:
    """
    Given a source record, inject parent/sibling/workspace context into `raw`
    so the transformer can use it during rendering.

    Injected keys (inside raw):
      _workspace_courses     : all courses in this workspace (for university + listing pages)
      _workspace_specs       : all specs in this workspace (for listing pages) or
                               child specs for a course page
      _workspace_blogs       : all blogs in this workspace (for listing pages)
      _workspace_parent      : parent course record (for specialization page)
      _workspace_sibling_specs : sibling specs (for specialization page)
    """
    pt = record.get("page_type")
    slug = record.get("slug")
    parent_slug = record.get("parent_slug")
    university_slug = record.get("university_slug", "")
    raw = (record.get("data") or {}).copy()

    # Resolve the shared university display fields (own page data, else
    # workspace metadata.json, else a title-cased slug).
    uni_ctx = _resolve_university_context(university_slug, index)
    uni_name = uni_ctx["name"]
    uni_full_name = uni_ctx["full_name"]
    uni_short_name = uni_ctx["short_name"]
    uni_logo = uni_ctx["logo"]

    # Inject shared branding variables
    raw["university_name"] = uni_name
    if uni_full_name:
        raw["university_full_name"] = uni_full_name
    if uni_short_name:
        raw["university_short_name"] = uni_short_name
    if uni_logo:
        raw["university_logo"] = uni_logo
    raw["university_branding"] = uni_name

    all_courses = _build_workspace_course_list(index, university_slug)
    all_specs = _build_workspace_spec_list(index, university_slug)
    all_blogs = _build_workspace_blog_list(index, university_slug)

    if pt == "university":
        raw["_workspace_courses"] = all_courses
        raw["_workspace_specs"] = all_specs
        raw["_workspace_blogs"] = all_blogs

    elif pt == "course":
        # Inject child specializations (those whose parent_slug == this course slug)
        child_specs = [s for s in all_specs if s.get("parent_slug") == slug]
        raw["_workspace_specs"] = child_specs
        # Also inject all blogs so the course page can show latest blog posts
        raw["_workspace_blogs"] = all_blogs

    elif pt == "specialization":
        # Inject parent course record
        if parent_slug and parent_slug in index["course"]:
            raw["_workspace_parent"] = index["course"][parent_slug]
        # Inject sibling specs
        siblings = [s for s in all_specs if s.get("parent_slug") == parent_slug and s.get("slug") != slug]
        raw["_workspace_sibling_specs"] = siblings

    elif pt == "programs_listing":
        raw["_workspace_courses"] = all_courses
        raw["_workspace_specs"] = all_specs
        raw["_workspace_blogs"] = all_blogs

    elif pt == "specializations_listing":
        raw["_workspace_courses"] = all_courses
        raw["_workspace_specs"] = all_specs

    elif pt == "blog_listing":
        raw["_workspace_blogs"] = all_blogs
        raw["_workspace_courses"] = all_courses

    return {
        **record,
        "raw": raw,
    }


def _render_page(enriched: dict) -> str:
    """Run the transformer + renderer on an enriched record and return HTML."""
    from renderer.engine import render_resolved

    resolved = {
        "slug": enriched.get("slug"),
        "page_type": enriched.get("page_type"),
        "university_slug": enriched.get("university_slug"),
        "parent_slug": enriched.get("parent_slug"),
        "raw": enriched.get("raw") or enriched.get("data", {}),
    }

    page_type = enriched.get("page_type")
    standalone = page_type in ("course", "specialization", "blog")
    return render_resolved(resolved, standalone=standalone)


def _auto_render_listing_pages(university_slug: str, index: dict) -> list[dict]:
    """
    Automatically re-render the 3 system listing pages with fresh workspace data.
    Called after all user-content pages have been compiled in Pass 2.
    Returns a list of result dicts: { pt, slug, success, error? }
    """
    from renderer.engine import render_resolved

    uni_name = _resolve_university_context(university_slug, index)["name"]

    all_courses = _build_workspace_course_list(index, university_slug)
    all_specs = _build_workspace_spec_list(index, university_slug)
    all_blogs = _build_workspace_blog_list(index, university_slug)

    results = []
    for pt in SYSTEM_PAGE_TYPES:
        slug = SYSTEM_PAGE_SLUGS[pt]
        raw = {
            "university_name": uni_name,
            "university_slug": university_slug,
            "_workspace_courses": all_courses,
            "_workspace_specs": all_specs,
            "_workspace_blogs": all_blogs,
        }
        resolved = {
            "slug": slug,
            "page_type": pt,
            "university_slug": university_slug,
            "parent_slug": None,
            "raw": raw,
        }
        try:
            html = render_resolved(resolved)
            page_dir = resolve_page_dir(university_slug, pt, slug)
            page_dir.mkdir(parents=True, exist_ok=True)
            html_filename = _HTML_FILENAME.get(pt, f"{pt}.html")
            (page_dir / html_filename).write_text(html, encoding="utf-8")
            results.append({"page_type": pt, "slug": slug, "success": True})
        except Exception as e:
            results.append({"page_type": pt, "slug": slug, "success": False, "error": str(e)})

    return results


# ── Public API ────────────────────────────────────────────────────────────────

def compile_workspace(university_slug: str) -> dict:
    """
    Run a full two-pass compilation for a university workspace.

    Returns:
    {
      "university_slug": str,
      "pages_compiled": int,
      "pages_failed": int,
      "listing_pages": [...],
      "errors": [ { "slug": ..., "error": ... } ],
      "compiled_at": ISO timestamp,
    }
    """
    pages_compiled = 0
    pages_failed = 0
    errors = []

    # Pass 1 — build global index
    index = _build_index(university_slug)

    # Gather all user-content records (skip system listing pages in this pass)
    user_content_types = {"university", "course", "specialization", "blog"}
    all_records = []
    for pt in user_content_types:
        for record in index.get(pt, {}).values():
            all_records.append(record)

    # Pass 2 — enrich + render each user-content page
    for record in all_records:
        pt = record.get("page_type")
        slug = record.get("slug")
        parent_slug = record.get("parent_slug")

        try:
            # Enforce validation of required images during compile
            data = record.get("data", {})
            if pt == "university":
                if not data.get("hero_image_url"):
                    raise ValueError("Missing required Hero Image (hero_image_url)")
            elif pt == "course":
                if not data.get("hero_image_url"):
                    raise ValueError("Missing required Hero Image (hero_image_url)")
                if not data.get("certificate_image_url"):
                    raise ValueError("Missing required Degree Certificate Image (certificate_image_url)")
            elif pt == "specialization":
                if not data.get("hero_image_url"):
                    raise ValueError("Missing required Hero Image (hero_image_url)")
            elif pt == "blog":
                if not data.get("hero_image_url"):
                    raise ValueError("Missing required Article Hero Image (hero_image_url)")

            enriched = _enrich_resolved(record, index)
            html = _render_page(enriched)

            # Overwrite the .html file
            page_dir = resolve_page_dir(university_slug, pt, slug, parent_slug)
            html_filename = _HTML_FILENAME.get(pt, f"{pt}.html")
            (page_dir / html_filename).write_text(html, encoding="utf-8")

            pages_compiled += 1

        except Exception as e:
            pages_failed += 1
            errors.append({"page_type": pt, "slug": slug, "error": str(e)})

    # After user content, auto-render all 3 system listing pages
    listing_results = _auto_render_listing_pages(university_slug, index)
    listing_compiled = sum(1 for r in listing_results if r.get("success"))
    listing_failed = sum(1 for r in listing_results if not r.get("success"))
    pages_compiled += listing_compiled
    pages_failed += listing_failed

    # Update metadata.json with last_compiled_at
    compiled_at = datetime.now(timezone.utc).isoformat()
    ensure_metadata(university_slug, {"last_compiled_at": compiled_at})

    return {
        "university_slug": university_slug,
        "pages_compiled": pages_compiled,
        "pages_failed": pages_failed,
        "listing_pages": listing_results,
        "errors": errors,
        "compiled_at": compiled_at,
    }


def get_workspace_tree(university_slug: str) -> dict:
    """
    Return a nested dict describing the workspace structure.
    Used by the frontend to display the workspace browser.

    Shape:
    {
      "university_slug": str,
      "metadata": { ... },
      "university": { slug, saved_at, has_html } | None,
      "courses": [
        {
          "slug": str,
          "saved_at": str,
          "has_html": bool,
          "specializations": [          ← fetched from flat Specializations/ dir
            { "slug": str, "saved_at": str, "has_html": bool }
          ]
        }
      ],
      "specializations": [              ← ALL flat specializations
        { "slug": str, "parent_slug": str, "saved_at": str, "has_html": bool }
      ],
      "blogs": [ { "slug": str, "saved_at": str, "has_html": bool } ],
      "pages": [                        ← system listing pages
        { "slug": str, "page_type": str, "has_html": bool }
      ],
    }
    """
    root = _workspace_root(university_slug)
    meta_path = root / "metadata.json"
    metadata = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    index = _build_index(university_slug)

    def _entry(record: dict, pt: str) -> dict:
        slug = record.get("slug", "")
        parent_slug = record.get("parent_slug")
        page_dir = resolve_page_dir(university_slug, pt, slug, parent_slug)
        html_filename = _HTML_FILENAME.get(pt, f"{pt}.html")
        has_html = (page_dir / html_filename).exists()
        return {
            "slug": slug,
            "parent_slug": parent_slug,
            "saved_at": record.get("saved_at", ""),
            "has_html": has_html,
        }

    # University node
    uni_records = list(index["university"].values())
    university_node = _entry(uni_records[0], "university") if uni_records else None

    # All flat specializations
    all_specs_flat = [
        _entry(r, "specialization")
        for r in index["specialization"].values()
    ]

    # Courses + nested specializations (looked up from flat list)
    courses = []
    for course_record in index["course"].values():
        course_slug = course_record.get("slug")
        course_entry = _entry(course_record, "course")
        child_specs = [s for s in all_specs_flat if s.get("parent_slug") == course_slug]
        course_entry["specializations"] = child_specs
        courses.append(course_entry)

    # Blogs
    blogs = [_entry(r, "blog") for r in index["blog"].values()]

    # System listing pages
    pages = []
    for pt in SYSTEM_PAGE_TYPES:
        slug = SYSTEM_PAGE_SLUGS[pt]
        page_dir = resolve_page_dir(university_slug, pt, slug)
        html_filename = _HTML_FILENAME.get(pt, f"{pt}.html")
        has_html = (page_dir / html_filename).exists()
        pages.append({
            "slug": slug,
            "page_type": pt,
            "has_html": has_html,
        })

    return {
        "university_slug": university_slug,
        "metadata": metadata,
        "university": university_node,
        "courses": courses,
        "specializations": all_specs_flat,
        "blogs": blogs,
        "pages": pages,
    }
