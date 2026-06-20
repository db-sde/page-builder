"""
workspace/manager.py
────────────────────
Handles the on-disk University Workspace folder structure.

Workspace layout (example — NMIMS):
  workspaces/
  └── nmims/
      ├── metadata.json          ← university-level global config
      ├── University/
      │   ├── source.json        ← transformed ACF JSON (source of truth)
      │   └── university.html    ← rendered page
      ├── Courses/
      │   └── online-mba/
      │       ├── source.json
      │       └── course.html
      ├── Specializations/       ← FLAT (not nested under Courses)
      │   └── mba-marketing/
      │       ├── source.json
      │       └── specialization.html
      ├── Blogs/
      │   └── blog-001/
      │       ├── source.json
      │       └── blog.html
      ├── Pages/                 ← System-generated listing pages
      │   ├── programs/
      │   │   ├── source.json
      │   │   └── programs_listing.html
      │   ├── specializations/
      │   │   ├── source.json
      │   │   └── specializations_listing.html
      │   └── blog/
      │       ├── source.json
      │       └── blog_listing.html
      └── Assets/
          ├── images/
          └── downloads/
"""

import json
from pathlib import Path
from datetime import datetime, timezone

# Root directory for all workspaces — lives alongside main.py
WORKSPACES_ROOT = Path(__file__).resolve().parent.parent / "workspaces"


# ── Path resolution ──────────────────────────────────────────────────────────

def _workspace_root(university_slug: str) -> Path:
    """Return (and create) the root folder for a university workspace."""
    p = WORKSPACES_ROOT / university_slug.lower().strip()
    p.mkdir(parents=True, exist_ok=True)
    return p


def resolve_page_dir(
    university_slug: str,
    page_type: str,
    slug: str,
    parent_slug: str | None = None,
) -> Path:
    """
    Return the directory where this page's files should be stored.

    university            → workspaces/<uni>/University/
    course                → workspaces/<uni>/Courses/<slug>/
    specialization        → workspaces/<uni>/Specializations/<slug>/   ← FLAT
    blog                  → workspaces/<uni>/Blogs/<slug>/
    programs_listing      → workspaces/<uni>/Pages/programs/
    specializations_listing → workspaces/<uni>/Pages/specializations/
    blog_listing          → workspaces/<uni>/Pages/blog/
    """
    root = _workspace_root(university_slug)

    if page_type == "university":
        return root / "University"

    elif page_type == "course":
        return root / "Courses" / slug

    elif page_type == "specialization":
        # FLAT layout — specializations live directly under Specializations/
        return root / "Specializations" / slug

    elif page_type == "blog":
        return root / "Blogs" / slug

    elif page_type == "programs_listing":
        return root / "Pages" / "programs"

    elif page_type == "specializations_listing":
        return root / "Pages" / "specializations"

    elif page_type == "blog_listing":
        return root / "Pages" / "blog"

    else:
        raise ValueError(f"Unknown page_type: {page_type}")


# ── File names per page type ─────────────────────────────────────────────────

_HTML_FILENAME = {
    "university": "university.html",
    "course": "course.html",
    "specialization": "specialization.html",
    "blog": "blog.html",
    "programs_listing": "programs_listing.html",
    "specializations_listing": "specializations_listing.html",
    "blog_listing": "blog_listing.html",
}

# All system-generated listing page types
SYSTEM_PAGE_TYPES = ["programs_listing", "specializations_listing", "blog_listing"]

# Slugs for system pages
SYSTEM_PAGE_SLUGS = {
    "programs_listing": "programs",
    "specializations_listing": "specializations",
    "blog_listing": "blog",
}


# ── metadata.json ────────────────────────────────────────────────────────────

def _default_metadata(university_slug: str) -> dict:
    return {
        "university_slug": university_slug,
        "university_name": university_slug.replace("-", " ").title(),
        "established_year": "",
        "default_theme": {
            "primary_color": "#6B4FC9",
            "secondary_color": "#FF5C35",
            "background_color": "#F6F4FB"
        },
        "global_contact": {
            "phone": "",
            "email": "",
            "address": ""
        },
        "lead_url": "https://apply.degreebaba.com",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_compiled_at": None,
    }


def ensure_metadata(university_slug: str, overrides: dict | None = None) -> dict:
    """
    Read (or create) workspaces/<uni>/metadata.json.
    If `overrides` is provided, deep-merge them into the stored metadata.
    Returns the final metadata dict.
    """
    root = _workspace_root(university_slug)
    meta_path = root / "metadata.json"

    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = _default_metadata(university_slug)

    if overrides:
        for k, v in overrides.items():
            if isinstance(v, dict) and isinstance(meta.get(k), dict):
                meta[k].update(v)
            elif v is not None and v != "":
                meta[k] = v

    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


# ── Asset directory ───────────────────────────────────────────────────────────

def ensure_assets(university_slug: str) -> Path:
    root = _workspace_root(university_slug)
    (root / "Assets" / "images").mkdir(parents=True, exist_ok=True)
    (root / "Assets" / "downloads").mkdir(parents=True, exist_ok=True)
    return root / "Assets"


# ── Save page ─────────────────────────────────────────────────────────────────

def save_page(
    university_slug: str,
    page_type: str,
    slug: str,
    source_json: dict,
    rendered_html: str,
    parent_slug: str | None = None,
) -> dict:
    """
    Write `source.json` and `<page_type>.html` into the correct workspace folder.

    Returns a dict with:
      - workspace_dir: absolute path to the page directory (str)
      - source_json_path: path to source.json (str)
      - html_path: path to page HTML (str)
      - university_slug, page_type, slug
    """
    page_dir = resolve_page_dir(university_slug, page_type, slug, parent_slug)
    page_dir.mkdir(parents=True, exist_ok=True)

    # 1. source.json — persisted ACF data (source of truth)
    source_path = page_dir / "source.json"
    record = {
        "university_slug": university_slug,
        "page_type": page_type,
        "slug": slug,
        "parent_slug": parent_slug,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "data": source_json,
    }
    source_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. <page_type>.html — rendered output
    html_filename = _HTML_FILENAME.get(page_type, f"{page_type}.html")
    html_path = page_dir / html_filename
    html_path.write_text(rendered_html, encoding="utf-8")

    # 3. Ensure root metadata.json exists
    ensure_metadata(university_slug)

    # 4. Ensure Assets/ folders exist
    ensure_assets(university_slug)

    return {
        "workspace_dir": str(page_dir),
        "source_json_path": str(source_path),
        "html_path": str(html_path),
        "university_slug": university_slug,
        "page_type": page_type,
        "slug": slug,
        "parent_slug": parent_slug,
    }


def init_system_pages(university_slug: str) -> list[dict]:
    """
    Create the 3 system-generated listing page stubs in the workspace.
    These are rendered with empty data initially and re-rendered by the compiler
    once content pages are added.

    Returns list of save results.
    """
    # Lazy import to avoid circular deps
    from renderer.engine import render_resolved

    results = []
    meta = ensure_metadata(university_slug)

    for pt in SYSTEM_PAGE_TYPES:
        slug = SYSTEM_PAGE_SLUGS[pt]
        source_data = {
            "university_slug": university_slug,
            "university_name": meta.get("university_name", university_slug.title()),
        }
        resolved = {
            "slug": slug,
            "page_type": pt,
            "university_slug": university_slug,
            "parent_slug": None,
            "raw": {
                **source_data,
                "_workspace_courses": [],
                "_workspace_specs": [],
                "_workspace_blogs": [],
            },
        }
        try:
            html = render_resolved(resolved, standalone=True)
        except Exception:
            html = f"<!-- {pt} stub — will be populated after compilation -->"

        result = save_page(
            university_slug=university_slug,
            page_type=pt,
            slug=slug,
            source_json=source_data,
            rendered_html=html,
            parent_slug=None,
        )
        results.append(result)

    return results


# ── Read / list helpers (used by compiler) ───────────────────────────────────

def list_all_source_files(university_slug: str) -> list[Path]:
    """Recursively scan the workspace and return all source.json paths."""
    root = _workspace_root(university_slug)
    return sorted(root.rglob("source.json"))


def read_source(source_path: Path) -> dict | None:
    """Read and parse a source.json file. Returns None on error."""
    try:
        with open(source_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_workspaces() -> list[str]:
    """Return a list of university slugs that have workspaces on disk."""
    if not WORKSPACES_ROOT.exists():
        return []
    return [d.name for d in WORKSPACES_ROOT.iterdir() if d.is_dir()]
