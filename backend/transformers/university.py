from transformers.base import BaseTransformer

class UniversityTransformer(BaseTransformer):
    def transform(self) -> dict:
        raw = self.raw

        my_courses = []

        # Workspace-injected lists (added by compiler._enrich_resolved)
        workspace_specs = raw.get("_workspace_specs") or []
        workspace_blogs = raw.get("_workspace_blogs") or []

        # ── Fallback: mode ──────────────────────────────────────────────────────────
        # Pipeline does not always output 'mode' — default to online since all
        # DegreeBaba courses are online programs.
        if not raw.get("mode"):
            raw["mode"] = "100% Online"

        # ── Fallback: fee_plans from total_fee ──────────────────────────────────────
        # If fee_plans array is missing but total_fee string exists, synthesize a
        # single-row fee plan so the fee section renders instead of being hidden.
        if not raw.get("fee_plans") and raw.get("total_fee"):
            cleaned_fee = self.format_fee(raw.get("total_fee", ""))
            if cleaned_fee:
                raw["fee_plans"] = [
                    {
                        "plan_name": "Full Program",
                        "plan_amount": cleaned_fee,
                        "plan_total": cleaned_fee
                    }
                ]

        return {
            "hero_image_url": raw.get("hero_image_url"),
            "hero_image_alt": raw.get("hero_image_alt", ""),
            "og_image_url": raw.get("og_image_url") or raw.get("hero_image_url"),
            "naac_grade": raw.get("naac_grade"),
            "ugc_approved": raw.get("ugc_approved"),

            # --- SEO ---
            "seo_title": raw.get("seo_title", ""),
            "meta_description": raw.get("meta_description", ""),

            # --- Site-wide ---
            "site": self.site,

            # --- Hero ---
            "hero": {
                "title": raw.get("university_name", ""),
                "full_name": raw.get("university_full_name", ""),
                "description": raw.get("hero_description", ""),
                "pills": self.build_pills([
                    (raw.get("naac_grade") and f"NAAC {raw.get('naac_grade')}", None),
                    (raw.get("ugc_approved"), None),
                    (raw.get("mode_of_learning"), None),
                ]),
                "badge": (
                    f"NAAC {raw.get('naac_grade')} · {raw.get('ugc_approved')} · NIRF #24"
                    if raw.get("university_name") and (raw.get("naac_grade") or raw.get("ugc_approved"))
                    else None
                ),
                "cta_primary": {"label": "Download Brochure", "href": "/contact"},
                "cta_secondary": {"label": "Book a Counselling Call", "href": "/contact"},
                "stat_card": {
                    "value": raw.get("naac_grade"),
                    "label": "NAAC Accredited"
                } if raw.get("naac_grade") else None
            },

            # --- Breadcrumbs ---
            "breadcrumbs": self.build_breadcrumbs(
                [{"label": "Home", "href": "/"}] +
                ([{"label": raw.get("university_name"), "href": None}] if raw.get("university_name") else [])
            ),

            # --- Stats strip ---
            "stats": self.build_stats([
                (raw.get("established_year"), "Est."),
                (raw.get("naac_grade") and f"NAAC {raw.get('naac_grade')}", "Accreditation"),
                (raw.get("ugc_approved"), "UGC Status"),
                (f"{self.format_fee(raw.get('starting_fee'))}/sem" if raw.get("starting_fee") else None, "Starting Fee"),
                (str(raw.get("num_programs")) if raw.get("num_programs") else None, "Programs"),
            ]),

            # --- Sidebar rail ---
            "rail": self.build_rail([
                ("about", "About", raw.get("about_content")),
                ("why-choose", "Why Choose", raw.get("why_choose_content")),
                ("facts", "Quick Facts", raw.get("facts")),
                ("accreditations", "Accreditations", raw.get("accreditations")),
                ("programs", "Programs & Fees", raw.get("programs_table") or my_courses),
                ("admission", "Admission", raw.get("admission_steps")),
                ("emi", "Fees & EMI", raw.get("emi_content")),
                ("exams", "Exam Process", raw.get("exam_content")),
                ("placement", "Placements", raw.get("placement_content")),
                ("reviews", "Reviews", raw.get("reviews")),
                ("faq", "FAQs", raw.get("faqs")),
            ]),

            # --- Sections ---
            "about": self.section_or_none("about_content"),
            "why_choose": self.section_or_none("why_choose_content"),

            "facts": raw.get("facts") or None,

            "accreditations": raw.get("accreditations") or None,

            # Programs table — from DB if courses exist, fallback to raw table
            "programs": {
                "intro": raw.get("programs_intro", ""),
                "table": raw.get("programs_table") or [],
                "courses": [
                    {
                        "name": c["data"].get("program_name", ""),
                        "fee": c["data"].get("starting_fee", ""),
                        "eligibility": c["data"].get("eligibility_summary", ""),
                        "duration": c["data"].get("duration", ""),
                        "href": f"/{c['slug']}"
                    }
                    for c in my_courses
                ]
            } if (raw.get("programs_table") or my_courses) else None,

            "admission": {
                "steps": self.section_or_none("admission_steps"),
                "fee_note": self.clean_str(raw.get("admission_fee_note")),
            } if raw.get("admission_steps") else None,

            "emi": self.section_or_none("emi_content"),
            "exam": self.section_or_none("exam_content"),
            "placement": self.section_or_none("placement_content"),

            "reviews": self.build_reviews(raw.get("reviews", [])) or None,
            "faqs": raw.get("faqs") or None,

            # Workspace-driven dynamic sections
            # These are passed through directly to engine.py so the renderer
            # can build the homepage specializations grid and blog preview cards
            # from real workspace content instead of hardcoded fallbacks.
            "_workspace_specs": workspace_specs,
            "_workspace_blogs": workspace_blogs,
        }
