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

        # ── Fallback: admission_steps ───────────────────────────────────────────────
        admission_steps_val = self.resolve("admission_steps")
        raw["admission_steps"] = admission_steps_val

        spec_desc_map = {
            "marketing": "Brand, digital & consumer strategy",
            "digital marketing": "SEO, SEM, social media & analytics",
            "human resource management": "Talent acquisition & HR analytics",
            "event management": "Event planning, operations & PR",
            "travel & tourism management": "Tourism, hospitality & leisure management",
            "ib (international business)": "Global trade & cross-border strategy",
            "international business": "Global trade & cross-border strategy",
            "business analytics": "Data-driven business decision making",
            "hospital management": "Hospital administration & clinical operations",
            "banking & insurance": "Risk management, commercial banking & underwriting",
            "entrepreneurship": "New venture creation, scaling & strategy",
            "operations management": "Operations, logistics & process design",
            "retail management": "Retail operations & consumer experience",
            "it (information technology)": "Digital transformation, ERP & IT systems",
            "information technology": "Digital transformation, ERP & IT systems",
            "logistics & supply chain management": "Supply chain, lean & procurement",
            "finance": "Corporate finance, banking & investment",
            "disaster management": "Crisis response, mitigation & recovery",
            "airlines & airport management": "Aviation management & airline operations",
            "data science & artificial intelligence": "Big data, machine learning & AI systems",
            "general management": "Leadership, organizational behavior & strategy",
            "fintech": "Financial technology, blockchain & analytics",
            "media management": "Media planning, journalism & entertainment",
            "brand management": "Brand positioning & value creation",
            "healthcare & hospital management": "Hospital administration & healthcare policy"
        }

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
        if not eligibility_content and raw.get("eligibility_summary"):
            eligibility_content = f"<p>{raw['eligibility_summary']}</p>"
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
            "headings": {
                "about": raw.get("about_heading") or f"About the {raw.get('program_name', '')}",
                "highlights": raw.get("highlights_heading") or "Program Highlights",
                "accreditations": raw.get("accreditations_heading") or "Approvals & Accreditations",
                "specializations": raw.get("specializations_heading") or "Specializations",
                "fees": raw.get("fee_heading") or "Fee Structure",
                "eligibility": raw.get("eligibility_heading") or "Eligibility",
                "admission": raw.get("admission_heading") or "Admission Process",
                "syllabus": raw.get("syllabus_heading") or "Syllabus",
                "placement": raw.get("placement_heading") or "Placement & Certificate",
                "jobs": raw.get("jobs_heading") or "Job Profiles After Graduation",
                "faqs": raw.get("faqs_heading") or "Frequently Asked Questions",
            },

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
                (self.format_fee(raw.get("starting_fee")), "Starting Fee"),
                (str(raw.get("num_specializations", "")), "Specializations"),
            ]),

            # --- Sidebar rail ---
            "rail": self.build_rail([
                ("about", "About", about_content_val),
                ("highlights", "Highlights", highlights),
                ("accreditations", "Accreditations", naac or ugc_display),
                ("specializations", "Specializations", my_specs or raw.get("specializations_intro")),
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

            # Accreditations built from flat fields
            "accreditations": [
                card for card in [
                    {
                        "title": "NAAC " + naac,
                        "description": f"{uni_name or 'The university'} holds NAAC Grade {naac} — among India's highest-rated private universities."
                    } if naac else None,
                    {
                        "title": ugc_display,
                        "description": "Offered under UGC (ODL & Online Programmes) Regulations, 2020 — fully valid for jobs and higher studies."
                    } if ugc_display else None
                ] if card is not None
            ] or None,

            # Specializations grid — from DB if available
            "specializations": {
                "intro": raw.get("specializations_intro", ""),
                "items": spec_items
            } if (spec_items or raw.get("specializations_intro")) else None,

            "eligibility": eligibility_content,
            "eligibility_summary": self.clean_str(raw.get("eligibility_summary")),

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
                "validity": self.clean_str(raw.get("validity")),
            } if (placement_content or certificate_description or self.clean_str(raw.get("validity"))) else None,

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
