from datetime import datetime, timezone
import json

# Original, NMIMS-specific site configuration. Preserved exactly as it was
# so the original "nmims" workspace keeps its real branding/contact details
# unchanged. Do NOT use this dict directly for other workspaces — call
# get_site_config(university_slug, university_name) instead, which returns
# a neutral default for every other tenant and merges in per-workspace
# overrides from workspaces/<slug>/metadata.json's "contact" section when
# present.
SITE_CONFIG = {
    "topbar_text": "Admissions open for the 2026 batch · Limited seats",
    "whatsapp": "911800102513",
    "email": "admissions@nmimsonline.edu",
    "address": "V. L. Mehta Road, Vile Parle (W), Mumbai 400056",
    "nav_links": [
        {"label": "Home", "href": "/"},
        {"label": "Programs", "href": "/programs"},
        {"label": "Specialisations", "href": "/specialisations"},
        {"label": "Admissions", "href": "/admissions"},
        {"label": "Blog", "href": "/blog"},
        {"label": "Contact", "href": "/contact"}
    ],
    "footer_columns": [
        {
            "heading": "Programs",
            "links": [
                {"label": "Online MBA", "href": "/nmims-online-mba"},
                {"label": "MBA Marketing", "href": "/nmims-mba-marketing"}
            ]
        },
        {
            "heading": "Company",
            "links": [
                {"label": "Home", "href": "/"},
                {"label": "Blog", "href": "/blog"},
                {"label": "Contact", "href": "/contact"}
            ]
        }
    ],
    "copyright": "© 2026 NMIMS Online. All rights reserved."
}


def _generic_site_config(university_slug: str, university_name: str | None) -> dict:
    """
    Neutral, tenant-agnostic defaults used for every workspace except the
    original 'nmims' one. Intentionally leaves whatsapp/email/address blank
    rather than reusing NMIMS's real contact details, since this is a
    shared multi-tenant rendering path — every other university workspace
    was previously inheriting NMIMS's WhatsApp number, email, address and
    footer links by default.
    """
    display_name = university_name or (university_slug or "").replace("-", " ").title() or "this university"
    year = datetime.now(timezone.utc).year
    return {
        "topbar_text": "Admissions open · Limited seats",
        "whatsapp": "",
        "email": "",
        "address": "",
        "nav_links": [
            {"label": "Home", "href": "/"},
            {"label": "Programs", "href": "/programs"},
            {"label": "Specialisations", "href": "/specialisations"},
            {"label": "Admissions", "href": "/admissions"},
            {"label": "Blog", "href": "/blog"},
            {"label": "Contact", "href": "/contact"}
        ],
        "footer_columns": [
            {
                "heading": "Programs",
                "links": [
                    {"label": "Programs", "href": "/programs"},
                    {"label": "Specialisations", "href": "/specialisations"}
                ]
            },
            {
                "heading": "Company",
                "links": [
                    {"label": "Home", "href": "/"},
                    {"label": "Blog", "href": "/blog"},
                    {"label": "Contact", "href": "/contact"}
                ]
            }
        ],
        "copyright": f"© {year} {display_name}. All rights reserved."
    }


def get_site_config(university_slug: str | None, university_name: str | None = None) -> dict:
    """
    Return the topbar/nav/footer/contact config for a given workspace.

    - "nmims" keeps the original hardcoded SITE_CONFIG untouched (no
      behaviour change for the original tenant).
    - Every other workspace gets a neutral, generic default (no NMIMS
      contact info baked in), with any `contact` overrides found in that
      workspace's own metadata.json merged on top — e.g.:
        "contact": {
          "topbar_text": "...",
          "whatsapp": "91...",
          "email": "admissions@example.edu",
          "address": "...",
          "copyright": "© 2026 Example University. All rights reserved."
        }
    """
    slug = (university_slug or "").lower().strip()
    if slug == "nmims":
        return SITE_CONFIG

    config = _generic_site_config(slug, university_name)

    try:
        from workspace.manager import WORKSPACES_ROOT
        meta_path = WORKSPACES_ROOT / slug / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            overrides = meta.get("contact") or {}
            for key in ("topbar_text", "whatsapp", "email", "address", "copyright"):
                if overrides.get(key):
                    config[key] = overrides[key]
    except Exception:
        pass

    return config
