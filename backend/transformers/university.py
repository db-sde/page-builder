from transformers.base import BaseTransformer

class UniversityTransformer(BaseTransformer):
    def transform(self) -> dict:
        raw = self.raw

        my_courses = []

        # Workspace-injected lists (added by compiler._enrich_resolved)
        workspace_specs = raw.get("_workspace_specs") or []
        workspace_blogs = raw.get("_workspace_blogs") or []

        # ── Fallback: mode ──────────────────────────────────────────────────────────
        mode_val = self.resolve("mode", "100% Online")
        raw["mode"] = mode_val

        # ── Fallback: fee_plans from total_fee ──────────────────────────────────────
        # If fee_plans array is missing but total_fee string exists, synthesize a
        # single-row fee plan so the fee section renders instead of being hidden.
        total_fee_val = self.resolve("total_fee")
        if not raw.get("fee_plans") and total_fee_val:
            cleaned_fee = self.format_fee(total_fee_val)
            if cleaned_fee:
                raw["fee_plans"] = [
                    {
                        "plan_name": "Full Program",
                        "plan_amount": cleaned_fee,
                        "plan_total": cleaned_fee
                    }
                ]

        naac = self.resolve("naac_grade")
        ugc = self.resolve("ugc_status")
        nirf = self.resolve("nirf_rank")
        uni_name = self.resolve("university_name", "")
        uni_full_name = self.resolve("university_full_name", "")
        mode_of_learning = self.resolve("mode_of_learning")
        established_year = self.resolve("established_year")
        starting_fee = self.resolve("starting_fee")
        num_programs = self.resolve("num_programs")

        # Resolve badge content dynamically
        badge_parts = []
        if naac:
            badge_parts.append(f"NAAC {naac}")
        if ugc:
            badge_parts.append(ugc)
        if nirf:
            badge_parts.append(nirf)
        badge = " · ".join(badge_parts) if (uni_name and badge_parts) else None

        about_content = self.resolve("about_content")
        why_choose_content = self.resolve("why_choose_content")
        facts = self.resolve_list("facts")
        accreditations = self.resolve_list("accreditations")
        programs_table = self.resolve_list("programs_table")
        admission_steps = self.resolve("admission_steps")
        emi_content = self.resolve("emi_content")
        exam_content = self.resolve("exam_content")
        placement_content = self.resolve("placement_content")
        reviews = self.resolve_list("reviews")
        faqs = self.resolve_list("faqs")

        return {
            "hero_image_url": self.resolve("hero_image_url"),
            "hero_image_alt": self.resolve("hero_image_alt", ""),
            "og_image_url": self.resolve("og_image_url") or self.resolve("hero_image_url"),
            "naac_grade": naac,
            "ugc_approved": ugc,

            # --- SEO ---
            "seo_title": raw.get("seo_title", ""),
            "meta_description": raw.get("meta_description", ""),

            # --- Site-wide ---
            "site": self.site,

            # --- Hero ---
            "hero": {
                "title": uni_name,
                "full_name": uni_full_name,
                "description": raw.get("hero_description", ""),
                "pills": self.build_pills([
                    (naac and f"NAAC {naac}", None),
                    (ugc, None),
                    (mode_of_learning, None),
                ]),
                "badge": badge,
                "cta_primary": {"label": "Download Brochure", "href": "/contact"},
                "cta_secondary": {"label": "Enquire Now", "href": "/contact"},
                "stat_card": {
                    "value": naac,
                    "label": "NAAC Accredited"
                } if naac else None
            },

            # --- Breadcrumbs ---
            "breadcrumbs": self.build_breadcrumbs(
                [{"label": "Home", "href": "/"}] +
                ([{"label": uni_name, "href": None}] if uni_name else [])
            ),

            # --- Stats strip ---
            "stats": self.build_stats([
                (established_year, "Est."),
                (naac and f"NAAC {naac}", "Accreditation"),
                (ugc, "UGC Status"),
                (f"{self.format_fee(starting_fee)}/sem" if starting_fee else None, "Starting Fee"),
                (str(num_programs) if num_programs else None, "Programs"),
            ]),

            # --- Sidebar rail ---
            "rail": self.build_rail([
                ("about", "About", about_content),
                ("why-choose", "Why Choose", why_choose_content),
                ("facts", "Quick Facts", facts),
                ("accreditations", "Accreditations", accreditations),
                ("programs", "Programs & Fees", programs_table or my_courses),
                ("admission", "Admission", admission_steps),
                ("emi", "Fees & EMI", emi_content),
                ("exams", "Exam Process", exam_content),
                ("placement", "Placements", placement_content),
                ("reviews", "Reviews", reviews),
                ("faq", "FAQs", faqs),
            ]),

            # --- Sections ---
            "about": about_content,
            "why_choose": why_choose_content,
            "facts": facts or None,
            "accreditations": accreditations or None,

            # Programs table — from DB if courses exist, fallback to raw table
            "programs": {
                "intro": raw.get("programs_intro", ""),
                "table": programs_table,
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
            } if (programs_table or my_courses) else None,

            "admission": {
                "steps": admission_steps,
                "fee_note": self.clean_str(raw.get("admission_fee_note")),
            } if admission_steps else None,

            "emi": emi_content,
            "exam": exam_content,
            "placement": placement_content,

            "reviews": self.build_reviews(reviews) or None,
            "faqs": faqs or None,

            # Workspace-driven dynamic sections
            "_workspace_specs": workspace_specs,
            "_workspace_blogs": workspace_blogs,
        }
