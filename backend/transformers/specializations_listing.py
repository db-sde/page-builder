import re

def clean_fee(amount_str: str) -> str:
    if not amount_str:
        return ""
    s = str(amount_str).strip()
    if not s or s.upper() in ("NA", "N/A", "NIL", "FREE", "-", "--"):
        return ""
    if s.startswith("₹"):
        return s
    s = re.sub(r'^INR\s*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\s*/[-–]+.*$', '', s).strip()
    s = re.sub(r'\s*/\s*(year|sem|semester|month|mo).*$', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'[^0-9,.].*$', '', s).strip()
    if not s:
        return ""
    return f"₹{s}"

class SpecializationsListingTransformer:
    """
    Transformer for the auto-generated Specializations Listing page.
    Reads `_workspace_specs` injected by the compiler.
    Groups specializations by their parent_slug (parent course).
    """
    def __init__(self, resolved: dict):
        self.raw = resolved.get("raw") or {}
        self.university_slug = resolved.get("university_slug", "")

    def transform(self) -> dict:
        raw = self.raw
        uni_name = raw.get("university_name") or self.university_slug.replace("-", " ").title()

        specs = raw.get("_workspace_specs") or []
        courses = raw.get("_workspace_courses") or []

        # Build course name lookup
        course_names = {}
        for c in courses:
            if isinstance(c, dict):
                slug = c.get("slug", "")
                data = c.get("data", {})
                course_names[slug] = data.get("program_name") or data.get("course_name") or slug.replace("-", " ").title()

        # Group specs by parent course
        groups_map: dict[str, dict] = {}
        for sp in specs:
            if not isinstance(sp, dict):
                continue
            data = sp.get("data", {})
            sp_slug = sp.get("slug", "")
            parent = sp.get("parent_slug") or data.get("parent_slug") or "general"

            if parent not in groups_map:
                groups_map[parent] = {
                    "course_name": course_names.get(parent, parent.replace("-", " ").title()),
                    "course_slug": parent,
                    "specs": [],
                }
            groups_map[parent]["specs"].append({
                "name": data.get("spec_name") or sp_slug.replace("-", " ").title(),
                "slug": sp_slug,
                "fee": clean_fee(data.get("total_fee") or ""),
                "duration": data.get("duration") or "2 Years",
                "description": data.get("hero_description") or "",
            })

        spec_groups = list(groups_map.values())

        return {
            "seo_title": f"{uni_name} MBA Specializations",
            "meta_description": f"Browse all MBA specializations available at {uni_name}. Choose from marketing, finance, HR, analytics and more.",
            "university_name": uni_name,
            "spec_groups": spec_groups,
        }
