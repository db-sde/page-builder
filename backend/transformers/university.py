from transformers.base import BaseTransformer

class UniversityTransformer(BaseTransformer):
    def transform(self) -> dict:
        raw = self.raw

        workspace_courses = raw.get("_workspace_courses")
        my_courses = workspace_courses if isinstance(workspace_courses, list) else []

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
        ugc = self.resolve("ugc_approved") or self.resolve("ugc_status")
        nirf = self.resolve("nirf_rank")
        uni_name = self.resolve("university_name", "")
        uni_full_name = self.resolve("university_full_name", "")
        mode_of_learning = self.resolve("mode_of_learning")
        established_year = self.resolve("established_year")

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
        facts = [
            item for item in self.resolve_list("facts")
            if isinstance(item, dict)
            and (self.clean_str(item.get("fact_title")) or self.clean_str(item.get("fact_description")))
        ]

        # Publisher payloads currently exist in two compatible shapes. The
        # template consumes the body_* context contract, so normalize at the
        # transformer boundary and discard entries with no visible identity.
        accreditations = []
        for item in self.resolve_list("accreditations"):
            if not isinstance(item, dict):
                continue
            body_name = self.clean_str(item.get("body_name") or item.get("name"))
            if not body_name:
                continue
            if item.get("body_name"):
                body_descriptor = self.clean_str(item.get("body_descriptor")) or ""
                body_detail = self.clean_str(item.get("body_detail")) or ""
            else:
                body_descriptor = ""
                body_detail = self.clean_str(item.get("description")) or ""
            accreditations.append({
                "body_name": body_name,
                "body_descriptor": body_descriptor,
                "body_detail": body_detail,
            })

        admission_steps = self.resolve("admission_steps")
        emi_content = self.resolve("emi_content")
        exam_content = self.resolve("exam_content")
        placement_content = self.resolve("placement_content")
        reviews = [
            item for item in self.resolve_list("reviews")
            if isinstance(item, dict) and self.clean_str(item.get("review_text") or item.get("q"))
        ]
        faqs = [
            item for item in self.resolve_list("faqs")
            if isinstance(item, dict)
            and self.clean_str(item.get("question") or item.get("q"))
            and self.clean_str(item.get("answer") or item.get("a"))
        ]
        faculty_members = [
            item for item in self.resolve_list("faculty_members")
            if isinstance(item, dict) and self.clean_str(item.get("member_name"))
        ]

        hero_image_alt = self.resolve("hero_image_alt", "")
        if not hero_image_alt:
            online_uni_name = uni_name if "online" in uni_name.lower() else f"{uni_name} Online"
            hero_image_alt = f"{online_uni_name} Degree Programs Hero Image"

        return {
            "hero_image_url": self.resolve("hero_image_url"),
            "hero_image_alt": hero_image_alt,
            "og_image_url": self.resolve("og_image_url") or self.resolve("hero_image_url"),
            "naac_grade": naac,
            "ugc_approved": ugc,
            "established_year": established_year,
            "headings": {
                "about": raw.get("about_heading") or f"About {uni_name}",
                "why_choose": raw.get("why_choose_heading") or f"Why Choose {uni_name}?",
                "facts": raw.get("facts_heading") or "Quick Facts",
                "accreditations": raw.get("accreditations_heading") or "Accreditations & Rankings",
                "programs": raw.get("programs_heading") or "Explore Our Online Programs",
                "admission": raw.get("admission_heading") or "Admission Process",
                "emi": raw.get("emi_heading") or "Financial Assistance & EMI Options",
                "exam": raw.get("exam_heading") or "Examination Process",
                "faculty": raw.get("faculty_heading") or "Faculty Members",
                "placement": raw.get("placement_heading") or "Placement & Career Services",
                "reviews": raw.get("reviews_heading") or "Student Testimonials",
                "faqs": raw.get("faqs_heading") or "Frequently Asked Questions",
            },

            # --- SEO ---
            "seo_title": raw.get("seo_title", ""),
            "meta_description": raw.get("meta_description", ""),

            # --- Site-wide ---
            "site": self.site,

            # --- Hero ---
            "hero": {
                "title": uni_name,
                "full_name": uni_full_name,
                "description": raw.get("hero_description") or about_content,
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
            ]),

            # --- Sidebar rail ---
            "rail": self.build_rail([
                ("about", "About", about_content),
                ("why-choose", "Why Choose", why_choose_content),
                ("facts", "Quick Facts", facts),
                ("accreditations", "Accreditations", accreditations),
                ("programs", "Programs & Fees", my_courses),
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
            "faculty_intro": self.resolve("faculty_intro"),
            "faculty_members": faculty_members or None,
            "programs_intro": self.resolve("programs_intro"),
            "admission_fee_note": self.clean_str(raw.get("admission_fee_note")),

            # Programs are generated exclusively from published course pages.
            "programs": {
                "intro": raw.get("programs_intro", ""),
                "courses": [
                    {
                        "name": c["data"].get("program_name", ""),
                        "fee": c["data"].get("starting_fee", ""),
                        "eligibility": c["data"].get("eligibility_summary", ""),
                        "duration": c["data"].get("duration", ""),
                        "href": self.public_route("course", c["slug"])
                    }
                    for c in my_courses
                ]
            } if my_courses else None,

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
