"""Template-driven page requirements (Phase 2).

Phase 1 (``field_definitions.py``) answers *"what data exists?"* — the schema of a
parsed page and who owns each field.

This module answers a different question: *"what data does this page's template
actually use?"* The two are deliberately not the same. A field can exist in the
schema (and stay in ``field_state``) while no template section renders it — e.g.
``faculty_members`` on the university page. Such fields must never contribute to
page completion and must never generate warnings.

The requirements below were read directly from the current Jinja2 templates
(``templates/university.html``, ``course.html``, ``specialization.html``) — the
template is the source of truth for *displayed* data. Page-authored fields and
renderer/workspace-owned context are recorded separately so the editor never
offers system data as page content.

Nothing here changes rendering, transformers, templates, or storage. It only
derives read-only section metadata from ``field_state``.
"""

from typing import Any

from core.field_definitions import build_field_state


# Data source for a section's content:
#   "page"      — filled from this page's own parsed fields
#   "workspace" — filled at compile time from other pages (courses/specs/blogs)
#   "shared"    — filled from knowledge base / site config / hardcoded marketing
SOURCE_PAGE = "page"
SOURCE_WORKSPACE = "workspace"
SOURCE_SHARED = "shared"


def _section(
    section_id: str,
    label: str,
    *,
    required: bool = False,
    required_fields: list[Any] | None = None,
    optional_fields: list[str] | None = None,
    always_rendered: bool = False,
    fabricated_when_empty: bool = False,
    data_source: str = SOURCE_PAGE,
    external_fields: dict[str, str] | None = None,
) -> dict[str, Any]:
    """One template section.

    ``required``          — the section is essential to the page (only the hero).
    ``required_fields``   — fields that gate the section. An entry may be a plain
                            field name (must be present) or a list of names meaning
                            "any one of these" (e.g. About renders from
                            ``about_content`` OR ``hero_description``).
    ``optional_fields``   — fields the section renders when present but does not
                            require.
    ``always_rendered``   — the template emits this section even with no data
                            (no ``{% if %}`` guard). Distinguishes a genuinely
                            hidden section from one that shows empty/fallback markup.
    ``fabricated_when_empty`` — the renderer injects hardcoded/fabricated content
                            when the real fields are absent (Phase 3 cleanup target).
    ``data_source``       — where the section's content comes from.
    """
    return {
        "section": section_id,
        "label": label,
        "required": required,
        "required_fields": required_fields or [],
        "optional_fields": optional_fields or [],
        "always_rendered": always_rendered,
        "fabricated_when_empty": fabricated_when_empty,
        "data_source": data_source,
        # Renderer/template context that is intentionally not page-authored.
        "external_fields": external_fields or {},
    }


# ---------------------------------------------------------------------------
# Page requirements — one ordered list of sections per page type.
# Read from the templates; not inferred from the schema.
# ---------------------------------------------------------------------------

PAGE_REQUIREMENTS: dict[str, list[dict[str, Any]]] = {
    "university": [
        _section("seo", "SEO & Meta",
                 optional_fields=["seo_title", "meta_description", "og_image_url"],
                 always_rendered=True),
        _section("hero", "Hero", required=True,
                 required_fields=["university_name", "hero_description"],
                 optional_fields=["university_full_name", "established_year",
                                  "naac_grade", "ugc_approved", "mode_of_learning",
                                  "hero_image_url", "hero_image_alt"],
                 always_rendered=True),
        _section("accreditation_strip", "Accreditation Strip",
                 optional_fields=["naac_grade", "ugc_approved"]),
        _section("programs", "Programs Grid",
                 data_source=SOURCE_WORKSPACE,
                 external_fields={"programs": "WORKSPACE"}),
        _section("specializations", "Specializations Grid",
                 data_source=SOURCE_WORKSPACE,
                 external_fields={"specs": "WORKSPACE"}),
        _section("why_choose", "Why Choose",
                 optional_fields=["why_choose_content", "facts"],
                 external_fields={"features": "WORKSPACE"}),
        _section("admission", "Admission Process",
                 optional_fields=["admission_steps"]),
        _section("fees_financing", "Fees & Financing",
                 optional_fields=["emi_content"],
                 external_fields={"financing": "WORKSPACE", "banks": "WORKSPACE"}),
        _section("recruiters", "Recruiters",
                 data_source=SOURCE_SHARED,
                 external_fields={"recruiters": "WORKSPACE"}),
        _section("testimonials", "Testimonials",
                 optional_fields=["reviews"]),
        _section("faqs", "FAQs",
                 optional_fields=["faqs"]),
        _section("blog_preview", "Blog Preview",
                 data_source=SOURCE_WORKSPACE,
                 external_fields={"posts": "WORKSPACE"}),
    ],
    "course": [
        _section("seo", "SEO & Meta",
                 optional_fields=["seo_title", "meta_description", "og_image_url"],
                 always_rendered=True),
        _section("hero", "Hero", required=True,
                 required_fields=["program_name"],
                 optional_fields=["university_name", "hero_description", "duration", "mode",
                                  "naac_grade", "ugc_status",
                                  "hero_image_url", "hero_image_alt"],
                 always_rendered=True),
        _section("stats", "Stats Strip",
                 optional_fields=["duration", "mode", "naac_grade", "ugc_status",
                                  "total_fee", "num_specializations"],
                 always_rendered=True),
        _section("about", "About",
                 required_fields=[["about_content", "hero_description"]]),
        _section("highlights", "Program Highlights",
                 optional_fields=["highlights"]),
        _section("accreditations", "Approvals & Accreditations",
                 optional_fields=["naac_grade", "ugc_status"]),
        _section("specializations", "Specializations",
                 data_source=SOURCE_WORKSPACE,
                 external_fields={"specs": "WORKSPACE"}),
        _section("fees", "Fee Structure",
                 optional_fields=["fee_plans", "total_fee", "emi_amount"],
                 always_rendered=True),
        _section("eligibility", "Eligibility",
                 optional_fields=["eligibility_content"]),
        _section("admission", "Admission Process",
                 optional_fields=["admission_steps"]),
        _section("syllabus", "Syllabus",
                 optional_fields=["syllabus_content"]),
        _section("placement", "Placement & Certificate",
                 optional_fields=["placement_content", "certificate_description",
                                  "certificate_image_url"]),
        _section("jobs", "Job Profiles",
                 optional_fields=["job_profiles"]),
        _section("reviews", "Student Reviews",
                 optional_fields=["reviews"]),
        _section("faqs", "FAQs",
                 optional_fields=["faqs"]),
    ],
    "specialization": [
        _section("seo", "SEO & Meta",
                 optional_fields=["seo_title", "meta_description", "og_image_url"],
                 always_rendered=True),
        _section("hero", "Hero", required=True,
                 required_fields=["spec_name"],
                 optional_fields=["university_name", "hero_description", "duration", "mode",
                                  "naac_grade", "ugc_status", "total_fee",
                                  "hero_image_url", "hero_image_alt"],
                 always_rendered=True),
        _section("stats", "Stats Strip",
                 optional_fields=["duration", "mode", "naac_grade", "ugc_status",
                                  "total_fee"],
                 always_rendered=True),
        _section("about", "About",
                 required_fields=["about_content"]),
        _section("highlights", "Specialization Highlights",
                 optional_fields=["highlights"]),
        _section("eligibility", "Eligibility",
                 optional_fields=["eligibility_content"]),
        _section("fees", "Fee Structure",
                 optional_fields=["fee_plans", "total_fee", "emi_amount"],
                 always_rendered=True),
        _section("admission", "Admission Process",
                 optional_fields=["admission_steps"]),
        _section("syllabus", "Syllabus",
                 optional_fields=["syllabus_content"]),
        _section("other_specs", "Compare Other Specializations",
                 optional_fields=["other_specs"],
                 data_source=SOURCE_WORKSPACE,
                 external_fields={"otherSpecs": "DERIVED"}),
        _section("exam", "Examination Process",
                 optional_fields=["exam_content"]),
        _section("placement", "Placement & Certificate",
                 optional_fields=["placement_content", "certificate_description"]),
        _section("jobs", "Job Profiles",
                 optional_fields=["job_profiles"]),
        _section("reviews", "Student Reviews",
                 optional_fields=["reviews"]),
        _section("faqs", "FAQs",
                 optional_fields=["faqs"]),
    ],
    "blog": [
        _section("seo", "SEO & Publishing",
                 optional_fields=["seo_title", "meta_description", "og_image_url", "author",
                                  "author_role", "published_date", "category", "tags",
                                  "focus_keyword", "read_time_override"],
                 always_rendered=True),
        _section("hero", "Article Header", required=True,
                 required_fields=["title", "hero_image_url"],
                 optional_fields=["subtitle", "excerpt", "hero_image_alt", "author",
                                  "author_role", "published_date", "category"],
                 always_rendered=True),
        _section("article", "Article", required=True,
                 required_fields=["content_html"],
                 optional_fields=["article_blocks", "word_count"],
                 always_rendered=True,
                 external_fields={"toc": "DERIVED", "read_time": "DERIVED"}),
        _section("faqs", "FAQs", optional_fields=["faqs"]),
        _section("relationships", "Related Content",
                 optional_fields=["primary_course_slug", "primary_specialization_slug",
                                  "related_course_slugs", "related_specialization_slugs",
                                  "related_blog_slugs", "mentioned_university_slugs"],
                 external_fields={"related_courses": "WORKSPACE", "related_specializations": "WORKSPACE",
                                  "related_blogs": "WORKSPACE", "mentioned_universities": "WORKSPACE"}),
        _section("cta", "Call to Action",
                 optional_fields=["cta_title", "cta_description", "cta_label"],
                 external_fields={"blog_cta": "DERIVED"}),
    ],
}


# Fields that are pipeline infrastructure rather than displayable content.
# They are never "unused schema fields" and never warn.
_INFRASTRUCTURE_FIELDS = {"_meta"}


def _fields_in_section(section: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for entry in section["required_fields"]:
        if isinstance(entry, (list, tuple, set)):
            names.update(entry)
        else:
            names.add(entry)
    names.update(section["optional_fields"])
    return names


def template_field_usage(page_type: str) -> dict[str, list[str]]:
    """Map each template-consumed field -> the section ids that use it."""
    usage: dict[str, list[str]] = {}
    for section in PAGE_REQUIREMENTS.get(page_type, []):
        for name in _fields_in_section(section):
            usage.setdefault(name, []).append(section["section"])
    return usage


def _is_missing(field_state: dict[str, Any], name: str) -> bool:
    entry = field_state.get(name)
    if entry is None:
        return True
    return bool(entry.get("missing", True))


def _missing_required(field_state: dict[str, Any], required_fields: list[Any]) -> list[Any]:
    missing: list[Any] = []
    for entry in required_fields:
        if isinstance(entry, (list, tuple, set)):
            # any-of group: satisfied if at least one member is present
            if all(_is_missing(field_state, name) for name in entry):
                missing.append(list(entry))
        elif _is_missing(field_state, name=entry):
            missing.append(entry)
    return missing


def build_page_state(page_type: str, field_state: dict[str, Any]) -> dict[str, Any]:
    """Combine template Page Requirements with per-field ``field_state``.

    Returns section-level render readiness plus a classification of every schema
    field as used / unused by the template. Pure/read-only: it does not mutate
    ``field_state`` and does not touch parsed values.

    Unsupported page types return an empty contract, mirroring
    ``build_field_state``.
    """
    sections_def = PAGE_REQUIREMENTS.get(page_type)
    if not sections_def:
        return {}

    sections: list[dict[str, Any]] = []
    for section in sections_def:
        missing_required = _missing_required(field_state, section["required_fields"])
        missing_optional = [
            name for name in section["optional_fields"]
            if _is_missing(field_state, name)
        ]
        # A section is renderable from real page data when none of its required
        # fields are missing. Workspace/shared sections carry no page-required
        # fields, so their real-data readiness is decided outside this page.
        renderable = not missing_required
        sections.append({
            "section": section["section"],
            "label": section["label"],
            "required": section["required"],
            "fields_used": sorted(_fields_in_section(section)),
            "required_fields": section["required_fields"],
            "optional_fields": section["optional_fields"],
            "renderable": renderable,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "always_rendered": section["always_rendered"],
            "fabricated_when_empty": section["fabricated_when_empty"],
            "data_source": section["data_source"],
        })

    usage = template_field_usage(page_type)
    used = set(usage)

    # Classify every field the schema/parser knows about.
    unused_schema_fields: list[str] = []
    infrastructure_fields: list[str] = []
    field_usage: dict[str, dict[str, Any]] = {}
    for name, entry in field_state.items():
        if name in _INFRASTRUCTURE_FIELDS or entry.get("derived"):
            infrastructure_fields.append(name)
            field_usage[name] = {"used_by_template": False, "infrastructure": True,
                                 "sections": []}
            continue
        is_used = name in used
        field_usage[name] = {
            "used_by_template": is_used,
            "infrastructure": False,
            "sections": usage.get(name, []),
        }
        if not is_used:
            unused_schema_fields.append(name)

    required_sections_incomplete = [
        s["section"] for s in sections if s["required"] and not s["renderable"]
    ]
    optional_sections_incomplete = [
        s["section"] for s in sections
        if not s["required"] and s["required_fields"] and not s["renderable"]
    ]
    fabricated_sections = [
        s["section"] for s in sections if s["fabricated_when_empty"]
    ]

    return {
        "page_type": page_type,
        "sections": sections,
        "unused_schema_fields": sorted(unused_schema_fields),
        "infrastructure_fields": sorted(infrastructure_fields),
        "field_usage": field_usage,
        "summary": {
            "required_sections_incomplete": required_sections_incomplete,
            "optional_sections_incomplete": optional_sections_incomplete,
            "renderable_sections": [s["section"] for s in sections if s["renderable"]],
            "fabricated_sections": fabricated_sections,
        },
    }


def build_page_state_from_values(
    page_type: str,
    values: dict[str, Any],
    derived_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convenience wrapper: build ``field_state`` then the page state."""
    field_state = build_field_state(page_type, values, derived_values)
    return build_page_state(page_type, field_state)
