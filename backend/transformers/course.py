from transformers.base import BaseTransformer

class CourseTransformer(BaseTransformer):
    def transform(self) -> dict:
        raw = self.raw
        # Fetch all specializations that belong to this course
        my_specs = []

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

        # ── Fallback: program_name preferred over course_name ───────────────────────
        # Pipeline sometimes outputs course_name instead of or in addition to
        # program_name. Prefer the longer/more complete value.
        if raw.get("course_name") and not raw.get("program_name"):
            raw["program_name"] = raw["course_name"]
        elif raw.get("course_name") and raw.get("program_name"):
            # Keep the longer one
            if len(raw["course_name"]) > len(raw.get("program_name", "")):
                raw["program_name"] = raw["course_name"]

        # ── Fallback: about_content from hero_description ───────────────────────────
        # If about_content is missing, use hero_description as a minimal about
        # paragraph so the About section renders with something rather than nothing.
        if not raw.get("about_content") and raw.get("hero_description"):
            raw["about_content"] = f"<p>{raw['hero_description']}</p>"

        return {
            "hero_image_url": raw.get("hero_image_url"),
            "hero_image_alt": raw.get("hero_image_alt", ""),
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
                "university": raw.get("university_name", ""),
                "description": raw.get("hero_description", ""),
                "pills": self.build_pills([
                    (raw.get("duration"), None),
                    (raw.get("mode"), None),
                    ("No Entrance Exam" if raw.get("program_name") else None, None),
                ]),
                "badge": (
                    f"{raw.get('naac_grade')} Accredited · {raw.get('ugc_status')}"
                    if raw.get("naac_grade") and raw.get("ugc_status")
                    else (f"NAAC {raw.get('naac_grade')} Accredited" if raw.get("naac_grade") else raw.get("ugc_status"))
                ) or None,
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
                ([{"label": raw.get("university_name"), "href": f"/{self.university_slug}"}] if raw.get("university_name") else []) +
                ([{"label": raw.get("program_name"), "href": None}] if raw.get("program_name") else [])
            ),

            # --- Stats strip ---
            "stats": self.build_stats([
                (raw.get("duration"), "Duration"),
                (raw.get("mode"), "Mode"),
                (raw.get("naac_grade"), "Accreditation"),
                (raw.get("ugc_status"), "Approval"),
                (self.format_fee(raw.get("total_fee", "")), "Total Fee"),
                (str(raw.get("num_specializations", "")), "Specializations"),
            ]),

            # --- Sidebar rail ---
            "rail": self.build_rail([
                ("about", "About", raw.get("about_content")),
                ("highlights", "Highlights", raw.get("highlights")),
                ("accreditations", "Accreditations", raw.get("naac_grade")),
                ("specializations", "Specializations", my_specs or raw.get("num_specializations")),
                ("fees", "Fee Structure", raw.get("fee_plans")),
                ("eligibility", "Eligibility", raw.get("eligibility_content")),
                ("admission", "Admission", raw.get("admission_steps")),
                ("syllabus", "Syllabus", raw.get("syllabus_content")),
                ("placement", "Placements", raw.get("placement_content")),
                ("jobs", "Job Profiles", raw.get("job_profiles")),
                ("reviews", "Reviews", raw.get("reviews")),
                ("faq", "FAQs", raw.get("faqs")),
            ]),

            # --- Sections ---
            "about": self.section_or_none("about_content"),
            "highlights": raw.get("highlights") or None,

            # Accreditations built from flat fields
            "accreditations": [
                {
                    "title": "NAAC " + raw.get("naac_grade", ""),
                    "description": f"{raw.get('university_name', 'The university')} holds NAAC Grade {raw.get('naac_grade', '')} — among India's highest-rated private universities."
                },
                {
                    "title": raw.get("ugc_status", ""),
                    "description": "Offered under UGC (ODL & Online Programmes) Regulations, 2020 — fully valid for jobs and higher studies."
                }
            ] if raw.get("naac_grade") else None,

            # Specializations grid — from DB if available, fallback to count
            "specializations": {
                "intro": raw.get("specializations_intro", "Choose your specialization at the start of year two."),
                "items": [
                    {
                        "name": s["data"].get("spec_name", ""),
                        "description": s["data"].get("hero_description", "")[:80] + "..." if s["data"].get("hero_description") else "",
                        "fee": self.format_fee(s["data"].get("total_fee", "")),
                        "href": f"/{s['slug']}"
                    }
                    for s in my_specs
                ] if my_specs else []
            } if (my_specs or raw.get("num_specializations")) else None,

            "eligibility": self.section_or_none("eligibility_content"),

            # Fees
            "fees": {
                "plans": raw.get("fee_plans") or [],
                "note": self.build_fee_note(raw.get("emi_amount")),
            } if raw.get("fee_plans") else None,

            "admission": {
                "steps": self.section_or_none("admission_steps"),
                "fee_note": raw.get("admission_fee_note", ""),
            } if raw.get("admission_steps") else None,

            # Syllabus — raw HTML, template renders as-is
            "syllabus": self.section_or_none("syllabus_content"),

            "placement": {
                "content": self.section_or_none("placement_content"),
                "certificate": self.section_or_none("certificate_description"),
            } if raw.get("placement_content") else None,

            # Sticky bar
            "sticky_bar": {
                "fee": self.format_fee(raw.get("total_fee")),
                "emi": raw.get("emi_amount"),
            } if (raw.get("total_fee") or raw.get("emi_amount")) else None,

            # Job profiles
            "jobs": raw.get("job_profiles") or None,

            # Reviews
            "reviews": self.build_reviews(raw.get("reviews", [])) or None,

            # FAQs
            "faqs": raw.get("faqs") or None,
        }
