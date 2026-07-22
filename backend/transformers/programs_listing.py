from core.utils import build_public_route, format_fee as clean_fee

class ProgramsListingTransformer:
    """
    Transformer for the auto-generated Programs Listing page.
    Reads `_workspace_courses` injected by the compiler.
    """
    def __init__(self, resolved: dict):
        self.raw = resolved.get("raw") or {}
        self.university_slug = resolved.get("university_slug", "")

    def transform(self) -> dict:
        raw = self.raw
        uni_name = raw.get("university_name") or self.university_slug.replace("-", " ").title()

        courses = raw.get("_workspace_courses") or []
        programs = []
        for c in courses:
            data = c.get("data", {}) if isinstance(c, dict) else {}
            slug = c.get("slug", "") if isinstance(c, dict) else ""
            programs.append({
                "name": data.get("program_name") or data.get("course_name") or slug.replace("-", " ").title(),
                "slug": slug,
                "href": build_public_route("course", slug, self.university_slug),
                "fee": clean_fee(data.get("total_fee") or data.get("starting_fee") or ""),
                "duration": data.get("duration") or "2 Years",
                "eligibility": data.get("eligibility_summary") or "Bachelor's degree",
                "description": data.get("hero_description") or "",
                "naac": data.get("naac_grade") or "",
                "mode": data.get("mode") or "100% Online",
            })

        return {
            "seo_title": f"{uni_name} Online Programs",
            "meta_description": f"Compare all online degree programs, eligibility, duration, fees and specializations offered by {uni_name} to choose the flexible course for your goals.",
            "university_name": uni_name,
            "programs": programs,
        }
