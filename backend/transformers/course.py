from transformers.base import BaseTransformer

class CourseTransformer(BaseTransformer):
    def transform(self) -> dict:
        raw = self.raw
        # Fetch all specializations that belong to this course
        my_specs = raw.get("_workspace_specs") or []

        # ── Fallback: mode ──────────────────────────────────────────────────────────
        mode_val = self.resolve("mode", "100% Online")
        raw["mode"] = mode_val

        # ── Fallback: fee_plans from total_fee ──────────────────────────────────────
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

        # ── Fallback: program_name preferred over course_name ───────────────────────
        if raw.get("course_name") and not raw.get("program_name"):
            raw["program_name"] = raw["course_name"]
        elif raw.get("course_name") and raw.get("program_name"):
            # Keep the longer one
            if len(raw["course_name"]) > len(raw.get("program_name", "")):
                raw["program_name"] = raw["course_name"]

        # ── Fallback: about_content from hero_description ───────────────────────────
        about_content_val = self.resolve("about_content")
        if not about_content_val and raw.get("hero_description"):
            about_content_val = f"<p>{raw['hero_description']}</p>"
        raw["about_content"] = about_content_val

        # admission_steps comes from the document or the university knowledge
        # base only — never a fabricated set of steps.
        admission_steps_val = self.resolve("admission_steps")
        raw["admission_steps"] = admission_steps_val

        spec_items = []
        if my_specs:
            for s in my_specs:
                spec_items.append({
                    "name": s["data"].get("spec_name", ""),
                    "description": s["data"].get("hero_description", "")[:80] + "..." if s["data"].get("hero_description") else "",
                    "fee": self.format_fee(s["data"].get("total_fee", "")),
                    "href": self.public_route("specialization", s["slug"])
                })

        naac = self.resolve("naac_grade")
        ugc = self.resolve("ugc_status")
        ugc_display = (f"UGC {ugc}" if ugc and "ugc" not in ugc.lower() else ugc) if ugc else None
        uni_name = self.resolve("university_name", "")
        duration = self.resolve("duration")
        mode = self.resolve("mode")
        placement_content = self.resolve("placement_content")
        certificate_description = self.resolve("certificate_description")
        eligibility_content = self.resolve("eligibility_content")
        syllabus_content = self.resolve("syllabus_content")
        emi_amount = self.resolve("emi_amount")
        highlights = self.resolve_list("highlights")
        reviews = self.resolve_list("reviews")
        faqs = self.resolve_list("faqs")

        badge_parts = []
        if naac:
            badge_parts.append(f"NAAC {naac} Accredited")
        if ugc_display:
            badge_parts.append(ugc_display)
        badge = " · ".join(badge_parts) if badge_parts else None

        hero_image_alt = raw.get("hero_image_alt", "")
        if not hero_image_alt:
            c_name = raw.get("program_name") or raw.get("course_name") or ""
            hero_image_alt = f"{c_name} Course Hero Image"

        return {
            "hero_image_url": raw.get("hero_image_url"),
            "hero_image_alt": hero_image_alt,
            "og_image_url": raw.get("og_image_url") or raw.get("hero_image_url"),
            "certificate_image_url": raw.get("certificate_image_url"),

            # --- SEO ---
            "seo_title": raw.get("seo_title", ""),
            "meta_description": raw.get("meta_description", ""),

            # --- Site-wide ---
            "site": self.site,

            # --- Hero ---
            "hero": {
                "title": raw.get("program_name", ""),
                "university": uni_name,
                "description": raw.get("hero_description", ""),
                "pills": self.build_pills([
                    (duration, None),
                    (mode, None),
                    ("No Entrance Exam" if raw.get("program_name") else None, None),
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
                ([{"label": uni_name, "href": self.public_route("university")}] if uni_name else []) +
                ([{"label": raw.get("program_name"), "href": None}] if raw.get("program_name") else [])
            ),

            # --- Stats strip ---
            "stats": self.build_stats([
                (duration, "Duration"),
                (mode, "Mode"),
                (naac and f"NAAC {naac}", "Accreditation"),
                (ugc_display, "Approval"),
                (self.format_fee(total_fee_val), "Total Fee"),
                (str(raw.get("num_specializations", "")), "Specializations"),
            ]),

            # --- Sidebar rail ---
            "rail": self.build_rail([
                ("about", "About", about_content_val),
                ("highlights", "Highlights", highlights),
                ("accreditations", "Accreditations", naac or ugc_display),
                ("specializations", "Specializations", my_specs),
                ("fees", "Fee Structure", raw.get("fee_plans")),
                ("eligibility", "Eligibility", eligibility_content),
                ("admission", "Admission", admission_steps_val),
                ("syllabus", "Syllabus", syllabus_content),
                ("placement", "Placements", placement_content),
                ("jobs", "Job Profiles", raw.get("job_profiles")),
                ("reviews", "Reviews", reviews),
                ("faq", "FAQs", faqs),
            ]),

            # --- Sections ---
            "about": about_content_val,
            "highlights": highlights or None,

            # Accreditations built from flat fields. Titles only — the previous
            # descriptions asserted invented claims about the university.
            "accreditations": [
                card for card in [
                    {"title": "NAAC " + naac, "description": ""} if naac else None,
                    {"title": ugc_display, "description": ""} if ugc_display else None
                ] if card is not None
            ] or None,

            # Specializations grid — from DB if available
            "specializations": {
                "intro": raw.get("specializations_intro", "Choose your specialization at the start of year two."),
                "items": spec_items
            } if spec_items else None,

            "eligibility": eligibility_content,

            # Fees
            "fees": {
                "plans": raw.get("fee_plans") or [],
                "note": self.build_fee_note(emi_amount),
            } if (raw.get("fee_plans") or self.clean_str(emi_amount)) else None,

            "admission": {
                "steps": admission_steps_val,
                "fee_note": self.clean_str(raw.get("admission_fee_note")),
            } if admission_steps_val else None,

            # Syllabus — raw HTML, template renders as-is
            "syllabus": syllabus_content,

            "placement": {
                "content": placement_content,
                "certificate": certificate_description,
            } if (placement_content or certificate_description) else None,

            # Sticky bar
            "sticky_bar": {
                "fee": self.format_fee(total_fee_val),
                "emi": emi_amount,
            } if (total_fee_val or emi_amount) else None,

            # Job profiles
            "jobs": raw.get("job_profiles") or None,

            # Reviews
            "reviews": self.build_reviews(reviews) or None,

            # FAQs
            "faqs": faqs or None,

            # Workspace-driven dynamic sections (forward to engine.py)
            "_workspace_specs": raw.get("_workspace_specs") or [],
            "_workspace_blogs": raw.get("_workspace_blogs") or [],
        }
