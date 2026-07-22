import re
from core.utils import build_public_route

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
                    "course_href": build_public_route("course", parent, self.university_slug),
                    "specs": [],
                }
            groups_map[parent]["specs"].append({
                "name": data.get("spec_name") or sp_slug.replace("-", " ").title(),
                "slug": sp_slug,
                "href": build_public_route("specialization", sp_slug, self.university_slug),
                "fee": clean_fee(data.get("total_fee") or ""),
                "duration": data.get("duration") or "",
                "description": data.get("hero_description") or "",
            })

        spec_groups = list(groups_map.values())

        flat_specs = []
        for g in spec_groups:
            for sp in g["specs"]:
                flat_specs.append({
                    "name": sp["name"],
                    "slug": sp["slug"],
                    "href": sp["href"],
                    "fee": sp["fee"],
                    "duration": sp["duration"],
                    "description": sp["description"],
                    "course_name": g["course_name"]
                })

        return {
            "seo_title": f"{uni_name} Specializations",
            "meta_description": f"Compare {uni_name} online specializations in marketing, finance, HR, analytics, technology and operations to find the curriculum that matches your career goals.",
            "university_name": uni_name,
            "spec_groups": spec_groups,
            "specs": flat_specs,
        }
