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
                f"{self.resolve('university_name') or 'University'} Online MBA"
            )

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

        uni_name = self.resolve("university_name", "")
        duration = self.resolve("duration")
        mode = self.resolve("mode")
        naac = self.resolve("naac_grade")
        ugc = self.resolve("ugc_status")
        ugc_display = (f"UGC {ugc}" if ugc and "ugc" not in ugc.lower() else ugc) if ugc else None
        about_content = self.resolve("about_content")
        highlights = self.resolve_list("highlights")
        eligibility_content = self.resolve("eligibility_content")
        syllabus_content = self.resolve("syllabus_content")
        exam_content = self.resolve("exam_content")
        admission_steps = self.resolve("admission_steps")
        placement_content = self.resolve("placement_content")
        certificate_description = self.resolve("certificate_description")
        emi_amount = self.resolve("emi_amount")
        reviews = self.resolve_list("reviews")
        faqs = self.resolve_list("faqs")

        hero_image_alt = raw.get("hero_image_alt", "")
        if not hero_image_alt:
            spec_name = raw.get("spec_name", "")
            hero_image_alt = f"{spec_name} Specialization Hero Image"

        return {
            "hero_image_url": raw.get("hero_image_url"),
            "hero_image_alt": hero_image_alt,
            "og_image_url": raw.get("og_image_url") or raw.get("hero_image_url"),

            # --- SEO ---
            "seo_title": raw.get("seo_title", ""),
            "meta_description": raw.get("meta_description", ""),

            # --- Site-wide ---
            "site": self.site,

            # --- Hero ---
            "hero": {
                "title": raw.get("spec_name", ""),
                "university": uni_name,
                "description": raw.get("hero_description", ""),
                "pills": self.build_pills([
                    (duration, None),
                    (mode, None),
                    ("No Entrance Exam" if raw.get("spec_name") else None, None),
                ]),
                "badge": "Most Popular Specialization" if raw.get("spec_name") else None,
                "cta_primary": {"label": "Download Brochure", "href": "/contact"},
                "cta_secondary": {"label": "Enquire Now", "href": "/contact"},
                "stat_card": {
                    "value": self.format_fee(total_fee_val),
                    "label": "Total program fee"
                } if total_fee_val else None
            },

            # --- Breadcrumbs ---
            "breadcrumbs": self.build_breadcrumbs(
                [{"label": "Home", "href": "/"}] +
                ([{"label": uni_name, "href": f"/{self.university_slug}"}] if uni_name else []) +
                ([{"label": parent_program_name, "href": f"/{self.parent_slug}"}] if self.parent_slug else []) +
                ([{"label": raw.get("spec_name"), "href": None}] if raw.get("spec_name") else [])
            ),

            "parent_program_name": parent_program_name,
            "parent_course_name": parent_program_name,

            # --- Stats strip ---
            "stats": self.build_stats([
                (duration, "Duration"),
                (mode, "Mode"),
                (naac and f"NAAC {naac}", "Accreditation"),
                (ugc_display, "Approval"),
                (self.format_fee(total_fee_val), "Total Fee"),
            ]),

            # --- Sidebar rail ---
            "rail": self.build_rail([
                ("about", "About", about_content),
                ("highlights", "Highlights", highlights),
                ("eligibility", "Eligibility", eligibility_content),
                ("fees", "Fee Structure", raw.get("fee_plans")),
                ("other-specs", "Other Specializations", siblings),
                ("syllabus", "Syllabus", syllabus_content),
                ("exams", "Exam Process", exam_content),
                ("admission", "Admission", admission_steps),
                ("placement", "Placements", placement_content),
                ("jobs", "Job Profiles", raw.get("job_profiles")),
                ("reviews", "Reviews", reviews),
                ("faq", "FAQs", faqs),
            ]),

            # --- Sections (None = hide the section) ---
            "about": about_content,
            "highlights": highlights or None,
            "eligibility": eligibility_content,
            "syllabus": syllabus_content,
            "exam": exam_content,
            "admission": {
                "steps": admission_steps,
                "fee_note": self.clean_str(raw.get("admission_fee_note")),
            } if admission_steps else None,
            "placement": placement_content,
            "certificate": certificate_description,

            # --- Fees ---
            "fees": {
                "plans": raw.get("fee_plans") or [],
                "note": self.build_fee_note(emi_amount),
            } if (raw.get("fee_plans") or self.clean_str(emi_amount)) else None,

            # --- Sticky bar ---
            "sticky_bar": {
                "fee": self.format_fee(total_fee_val),
                "emi": emi_amount,
            } if (total_fee_val or emi_amount) else None,

            # --- Sibling specializations ---
            "other_specs": [
                {
                    "name": s["data"].get("spec_name", ""),
                    "fee": self.format_fee(s["data"].get("total_fee", "")),
                    "href": f"{s['slug']}.html",
                    "slug": s.get("slug")
                }
                for s in siblings
            ] or None,

            # --- Job profiles ---
            "jobs": raw.get("job_profiles") or None,

            # --- Reviews ---
            "reviews": self.build_reviews(reviews) or None,

            # --- FAQs ---
            "faqs": faqs or None,
        }
