"""Canonical field ownership for parsed content pages.

This module describes post-parser ownership only. It does not validate content,
transform renderer context, or decide which fields templates display.
"""

from typing import Any


AUTO = "AUTO"
MANUAL = "MANUAL"
DERIVED = "DERIVED"


def _field(source: str, *, required: bool = False) -> dict[str, Any]:
    return {
        "source": source,
        "required": required,
        "optional": not required,
        "manual": source == MANUAL,
        "derived": source == DERIVED,
    }


PAGE_FIELD_DEFINITIONS: dict[str, dict[str, dict[str, Any]]] = {
    "university": {
        "_meta": _field(AUTO),
        "university_name": _field(AUTO, required=True),
        "university_full_name": _field(AUTO),
        "hero_description": _field(AUTO, required=True),
        "established_year": _field(AUTO),
        "naac_grade": _field(AUTO, required=True),
        "ugc_approved": _field(AUTO, required=True),
        "mode_of_learning": _field(AUTO),
        "starting_fee": _field(AUTO),
        "num_programs": _field(AUTO),
        "about_heading": _field(AUTO),
        "why_choose_heading": _field(AUTO),
        "facts_heading": _field(AUTO),
        "accreditations_heading": _field(AUTO),
        "programs_heading": _field(AUTO),
        "admission_heading": _field(AUTO),
        "emi_heading": _field(AUTO),
        "exam_heading": _field(AUTO),
        "faculty_heading": _field(AUTO),
        "placement_heading": _field(AUTO),
        "reviews_heading": _field(AUTO),
        "faqs_heading": _field(AUTO),
        "about_content": _field(AUTO),
        "why_choose_content": _field(AUTO),
        "admission_steps": _field(AUTO),
        "admission_fee_note": _field(AUTO),
        "emi_content": _field(AUTO),
        "exam_content": _field(AUTO),
        "faculty_intro": _field(AUTO),
        "placement_content": _field(AUTO),
        "facts": _field(AUTO),
        "accreditations": _field(AUTO),
        "programs_table": _field(AUTO),
        "faculty_members": _field(AUTO),
        "reviews": _field(MANUAL),
        "faqs": _field(AUTO),
        "seo_title": _field(AUTO),
        "meta_description": _field(AUTO),
        "programs_intro": _field(AUTO),
        "hero_image_url": _field(MANUAL, required=True),
        "hero_image_alt": _field(MANUAL),
        "page_type": _field(DERIVED, required=True),
        "slug": _field(DERIVED, required=True),
        "university_slug": _field(DERIVED, required=True),
        "parent_slug": _field(DERIVED),
    },
    "course": {
        "_meta": _field(AUTO),
        "program_name": _field(AUTO, required=True),
        "university_name": _field(AUTO, required=True),
        "linked_university": _field(AUTO),
        "hero_description": _field(AUTO, required=True),
        "duration": _field(AUTO, required=True),
        "mode": _field(AUTO),
        "naac_grade": _field(AUTO, required=True),
        "ugc_status": _field(AUTO, required=True),
        "total_fee": _field(AUTO, required=True),
        "num_specializations": _field(AUTO),
        "about_heading": _field(AUTO),
        "highlights_heading": _field(AUTO),
        "accreditations_heading": _field(AUTO),
        "specializations_heading": _field(AUTO),
        "fee_heading": _field(AUTO),
        "eligibility_heading": _field(AUTO),
        "admission_heading": _field(AUTO),
        "syllabus_heading": _field(AUTO),
        "placement_heading": _field(AUTO),
        "jobs_heading": _field(AUTO),
        "faqs_heading": _field(AUTO),
        "about_content": _field(AUTO),
        "specializations_intro": _field(AUTO),
        "eligibility_content": _field(AUTO),
        "admission_steps": _field(AUTO),
        "admission_fee_note": _field(AUTO),
        "syllabus_content": _field(AUTO),
        "placement_content": _field(AUTO),
        "certificate_description": _field(AUTO),
        "validity": _field(AUTO),
        "emi_amount": _field(AUTO),
        "highlights": _field(AUTO),
        "fee_plans": _field(AUTO),
        "job_profiles": _field(AUTO),
        "reviews": _field(MANUAL),
        "faqs": _field(AUTO),
        "seo_title": _field(AUTO),
        "meta_description": _field(AUTO),
        "starting_fee": _field(AUTO),
        "eligibility_summary": _field(AUTO),
        "hero_image_url": _field(MANUAL, required=True),
        "hero_image_alt": _field(MANUAL),
        "certificate_image_url": _field(MANUAL, required=True),
        "page_type": _field(DERIVED, required=True),
        "slug": _field(DERIVED, required=True),
        "university_slug": _field(DERIVED, required=True),
        "parent_slug": _field(DERIVED),
    },
    "specialization": {
        "_meta": _field(AUTO),
        "spec_name": _field(AUTO, required=True),
        "university_name": _field(AUTO, required=True),
        "linked_university": _field(AUTO),
        "linked_course": _field(AUTO),
        "hero_description": _field(AUTO, required=True),
        "duration": _field(AUTO, required=True),
        "mode": _field(AUTO),
        "naac_grade": _field(AUTO, required=True),
        "ugc_status": _field(AUTO, required=True),
        "total_fee": _field(AUTO, required=True),
        "about_heading": _field(AUTO),
        "highlights_heading": _field(AUTO),
        "eligibility_heading": _field(AUTO),
        "fee_heading": _field(AUTO),
        "other_specs_heading": _field(AUTO),
        "syllabus_heading": _field(AUTO),
        "exam_heading": _field(AUTO),
        "admission_heading": _field(AUTO),
        "placement_heading": _field(AUTO),
        "jobs_heading": _field(AUTO),
        "certificate_heading": _field(AUTO),
        "faqs_heading": _field(AUTO),
        "about_content": _field(AUTO),
        "eligibility_content": _field(AUTO),
        "syllabus_content": _field(AUTO),
        "exam_content": _field(AUTO),
        "admission_steps": _field(AUTO),
        "admission_fee_note": _field(AUTO),
        "placement_content": _field(AUTO),
        "certificate_description": _field(AUTO),
        "emi_amount": _field(AUTO),
        "highlights": _field(AUTO),
        "other_specs": _field(AUTO),
        "job_profiles": _field(AUTO),
        "reviews": _field(MANUAL),
        "faqs": _field(AUTO),
        "seo_title": _field(AUTO),
        "meta_description": _field(AUTO),
        "eligibility_summary": _field(AUTO),
        "hero_image_url": _field(MANUAL, required=True),
        "hero_image_alt": _field(MANUAL),
        "page_type": _field(DERIVED, required=True),
        "slug": _field(DERIVED, required=True),
        "university_slug": _field(DERIVED, required=True),
        "parent_slug": _field(DERIVED, required=True),
    },
}


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set)):
        return not value
    return False


def build_field_state(
    page_type: str,
    values: dict[str, Any],
    derived_values: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return page field state without altering the parsed values."""
    definitions = PAGE_FIELD_DEFINITIONS.get(page_type)
    if not definitions:
        return {}

    derived_values = derived_values or {}
    state: dict[str, dict[str, Any]] = {}

    for name, definition in definitions.items():
        value = derived_values.get(name) if definition["derived"] else values.get(name)
        state[name] = {
            "name": name,
            **definition,
            "missing": _is_missing(value),
            "value": value,
        }

    # Adapter/local-fallback additions still came from the parser stage. Keep
    # them visible to the editor even when they are outside the canonical schema.
    for name, value in values.items():
        if name in state:
            continue
        definition = _field(AUTO)
        state[name] = {
            "name": name,
            **definition,
            "missing": _is_missing(value),
            "value": value,
        }

    return state
