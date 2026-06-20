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
                "fee": data.get("total_fee") or data.get("starting_fee") or "",
                "duration": data.get("duration") or "2 Years",
                "eligibility": data.get("eligibility_summary") or "Bachelor's degree",
                "description": data.get("hero_description") or "",
                "naac": data.get("naac_grade") or "",
                "mode": data.get("mode") or "100% Online",
            })

        return {
            "seo_title": f"{uni_name} Online Programs",
            "meta_description": f"Explore all online degree programs offered by {uni_name}. UGC-entitled, fully online courses.",
            "university_name": uni_name,
            "programs": programs,
        }
