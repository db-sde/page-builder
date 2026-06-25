from transformers.base import BaseTransformer
import re

class SpecializationTransformer(BaseTransformer):
    def transform(self) -> dict:
        raw = self.raw
        siblings = raw.get("_workspace_sibling_specs") or []

        parent_course = raw.get("_workspace_parent") or {}
        parent_data = parent_course.get("data") or parent_course.get("raw") or {}
        parent_program_name = None
        if parent_data:
            parent_program_name = (
                parent_data.get("program_name") or
                parent_data.get("course_name") or
                parent_data.get("title")
            )
        if not parent_program_name:
            parent_program_name = (
                raw.get("program_name") or
                raw.get("course_name") or
                f"{raw.get('university_name') or 'University'} Online MBA"
            )


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

            # --- SEO ---
            "seo_title": raw.get("seo_title", ""),
            "meta_description": raw.get("meta_description", ""),

            # --- Site-wide ---
            "site": self.site,

            # --- Hero ---
            "hero": {
                "title": raw.get("spec_name", ""),
                "university": raw.get("university_name", ""),
                "description": raw.get("hero_description", ""),
                "pills": self.build_pills([
                    (raw.get("duration"), None),
                    (raw.get("mode"), None),
                    ("No Entrance Exam" if raw.get("spec_name") else None, None),
                ]),
                "badge": "Most Popular Specialization" if raw.get("spec_name") else None,
                "cta_primary": {"label": "Download Brochure", "href": "/contact"},
                "cta_secondary": {"label": "Enquire Now", "href": "/contact"},
                "stat_card": {
                    "value": self.format_fee(raw.get("total_fee")),
                    "label": "Total program fee"
                } if raw.get("total_fee") else None
            },

            # --- Breadcrumbs ---
            "breadcrumbs": self.build_breadcrumbs(
                [{"label": "Home", "href": "/"}] +
                ([{"label": raw.get("university_name"), "href": f"/{self.university_slug}"}] if raw.get("university_name") else []) +
                ([{"label": parent_program_name, "href": f"/{self.parent_slug}"}] if self.parent_slug else []) +
                ([{"label": raw.get("spec_name"), "href": None}] if raw.get("spec_name") else [])
            ),

            "parent_program_name": parent_program_name,
            "parent_course_name": parent_program_name,

            # --- Stats strip ---
            "stats": self.build_stats([
                (raw.get("duration"), "Duration"),
                (raw.get("mode"), "Mode"),
                (raw.get("naac_grade") and f"NAAC {raw.get('naac_grade')}", "Accreditation"),
                (raw.get("ugc_status"), "Approval"),
                (self.format_fee(raw.get("total_fee", "")), "Total Fee"),
            ]),

            # --- Sidebar rail ---
            "rail": self.build_rail([
                ("about", "About", raw.get("about_content")),
                ("highlights", "Highlights", raw.get("highlights")),
                ("eligibility", "Eligibility", raw.get("eligibility_content")),
                ("fees", "Fee Structure", raw.get("fee_plans")),
                ("other-specs", "Other Specializations", siblings),
                ("syllabus", "Syllabus", raw.get("syllabus_content")),
                ("exams", "Exam Process", raw.get("exam_content")),
                ("admission", "Admission", raw.get("admission_steps")),
                ("placement", "Placements", raw.get("placement_content")),
                ("jobs", "Job Profiles", raw.get("job_profiles")),
                ("reviews", "Reviews", raw.get("reviews")),
                ("faq", "FAQs", raw.get("faqs")),
            ]),

            # --- Sections (None = hide the section) ---
            "about": self.section_or_none("about_content"),
            "highlights": raw.get("highlights") or None,
            "eligibility": self.section_or_none("eligibility_content"),
            "syllabus": self.section_or_none("syllabus_content"),
            "exam": self.section_or_none("exam_content"),
            "admission": {
                "steps": self.section_or_none("admission_steps"),
                "fee_note": self.clean_str(raw.get("admission_fee_note")),
            } if raw.get("admission_steps") else None,
            "placement": self.section_or_none("placement_content"),
            "certificate": self.section_or_none("certificate_description"),

            # --- Fees ---
            "fees": {
                "plans": raw.get("fee_plans") or [],
                "note": self.build_fee_note(raw.get("emi_amount")),
            } if (raw.get("fee_plans") or self.clean_str(raw.get("emi_amount"))) else None,

            # --- Sticky bar ---
            "sticky_bar": {
                "fee": self.format_fee(raw.get("total_fee")),
                "emi": raw.get("emi_amount"),
            } if (raw.get("total_fee") or raw.get("emi_amount")) else None,

            # --- Sibling specializations ---
            "other_specs": [
                {
                    "name": s["data"].get("spec_name", ""),
                    "fee": self.format_fee(s["data"].get("total_fee", "")),
                    "href": f"/{s['slug']}"
                }
                for s in siblings
            ] or None,

            # --- Job profiles ---
            "jobs": raw.get("job_profiles") or None,

            # --- Reviews ---
            "reviews": self.build_reviews(raw.get("reviews", [])) or None,

            # --- FAQs ---
            "faqs": raw.get("faqs") or None,
        }
