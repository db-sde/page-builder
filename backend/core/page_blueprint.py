"""Page Blueprint — everything needed to build one page type (Phase 3).

Layer recap:

* ``field_definitions.py``  — *what data exists* (schema + ownership).
* ``page_requirements.py``  — *what the template displays* (sections).
* ``page_blueprint.py``     — the two combined into the single contract the
  editor workflow needs: ordered sections, plus which fields are required,
  optional, manual, derived, image, or carry an explicit default.

This module adds no new schema and no new rules. It reads the two existing
layers and presents them in one shape so the editor and preview do not have to
recombine them (and so the React app stops keeping its own copy of the schema).

Blog is intentionally out of scope — it keeps the legacy blog parser.
"""

from typing import Any

from core.field_definitions import PAGE_FIELD_DEFINITIONS
from core.page_requirements import (
    PAGE_REQUIREMENTS,
    template_field_usage,
)


SUPPORTED_PAGE_TYPES = ("university", "course", "specialization")


# Context intentionally supplied outside page-authored content. Keeping these
# in the Blueprint makes their ownership explicit without exposing them as
# editable fields in the Review screen.
COMMON_EXTERNAL_TEMPLATE_FIELDS: dict[str, str] = {
    "site": "WORKSPACE",
    "branding_logo": "WORKSPACE",
    "branding_favicon": "WORKSPACE",
    "university_letter": "DERIVED",
    "canonical_url": "DERIVED",
    "homepage_href": "DERIVED",
    "programs_listing_href": "DERIVED",
    "specs_listing_href": "DERIVED",
    "blog_listing_href": "DERIVED",
    "contact_href": "DERIVED",
    "lead_url_apply": "DERIVED",
    "lead_url_brochure": "DERIVED",
    "lead_url_enquiry": "DERIVED",
    "lead_url_fees": "DERIVED",
    "lead_url_syllabus": "DERIVED",
    "lead_url_whatsapp": "DERIVED",
    "hero": "DERIVED",
    "stats": "DERIVED",
    "rail": "DERIVED",
    "preview_mode": "SYSTEM",
    "standalone": "SYSTEM",
    "show_contact": "SYSTEM",
    "heroBadge": "SYSTEM",
    "heroChip": "SYSTEM",
    "heroCrumb": "SYSTEM",
    "heroH1": "SYSTEM",
    "heroImg": "SYSTEM",
    "heroImgText": "SYSTEM",
    "heroSecBtn": "SYSTEM",
    "heroStatDivider": "SYSTEM",
    "heroStatLabel": "SYSTEM",
    "heroSub": "SYSTEM",
    "heroWrap": "SYSTEM",
}


# Renderer display models that are not authored independently. They are built
# from canonical page fields or workspace collections before Jinja rendering.
PAGE_EXTERNAL_TEMPLATE_FIELDS: dict[str, dict[str, str]] = {
    "university": {
        "admission": "DERIVED",
        "banks": "WORKSPACE",
        "emi": "DERIVED",
        "features": "WORKSPACE",
        "financing": "WORKSPACE",
        "posts": "WORKSPACE",
        "programs": "WORKSPACE",
        "recruiters": "WORKSPACE",
        "specs": "WORKSPACE",
        "testimonials": "DERIVED",
        "why_choose": "DERIVED",
        "why_choose_name": "DERIVED",
    },
    "course": {
        "about": "DERIVED",
        "accreditations": "DERIVED",
        "admission": "DERIVED",
        "eligibility": "DERIVED",
        "fees": "DERIVED",
        "jobs": "DERIVED",
        "placement": "DERIVED",
        "specs": "WORKSPACE",
        "steps": "DERIVED",
        "sticky_bar": "DERIVED",
        "syllabusTabs": "DERIVED",
        "syllabus_years": "DERIVED",
    },
    "specialization": {
        "about": "DERIVED",
        "admission": "DERIVED",
        "certificate": "DERIVED",
        "eligibility": "DERIVED",
        "exam": "DERIVED",
        "fees": "DERIVED",
        "jobs": "DERIVED",
        "otherSpecs": "DERIVED",
        "parent_course_slug": "DERIVED",
        "parent_program_name": "DERIVED",
        "placement": "DERIVED",
        "steps": "DERIVED",
        "sticky_bar": "DERIVED",
        "syllabusTabs": "DERIVED",
        "syllabus_years": "DERIVED",
    },
}


# Explicit, declared defaults. These mirror the defaults the transformers
# already apply today (``self.resolve("mode", "100% Online")``); declaring them
# here makes them visible to the editor instead of hidden inside the renderer.
# Only genuine formatting/mode defaults belong here — never editorial content.
EXPLICIT_DEFAULTS: dict[str, dict[str, Any]] = {
    "university": {},
    "course": {"mode": "100% Online"},
    "specialization": {"mode": "100% Online"},
}


# Presentation metadata for image fields, so the upload UI can be driven from
# the backend contract rather than a second hardcoded list in the React app.
IMAGE_FIELD_META: dict[str, dict[str, str]] = {
    "hero_image_url": {
        "label": "Hero Image",
        "hint": "Main visual in the hero section",
        "dims": "480 × 420px",
    },
    "certificate_image_url": {
        "label": "Degree Certificate Image",
        "hint": "Sample degree certificate shown in the Placement section",
        "dims": "320 × 240px",
    },
    "og_image_url": {
        "label": "Social Share Image",
        "hint": "Open Graph image; falls back to the hero image when empty",
        "dims": "1200 × 630px",
    },
}


def _is_image_field(name: str) -> bool:
    return name.endswith("_image_url")


def build_page_blueprint(page_type: str) -> dict[str, Any]:
    """Return the complete build contract for one page type.

    Returns ``{}`` for unsupported page types, matching ``build_field_state``
    and ``build_page_state``.
    """
    definitions = PAGE_FIELD_DEFINITIONS.get(page_type)
    sections = PAGE_REQUIREMENTS.get(page_type)
    if not definitions or not sections:
        return {}

    usage = template_field_usage(page_type)
    defaults = EXPLICIT_DEFAULTS.get(page_type, {})

    required_fields: list[str] = []
    optional_fields: list[str] = []
    manual_fields: list[str] = []
    derived_fields: list[str] = []
    image_fields: list[str] = []

    fields: dict[str, dict[str, Any]] = {}
    for name, definition in definitions.items():
        used_by_template = name in usage
        field = {
            "name": name,
            **definition,
            "image": _is_image_field(name),
            "used_by_template": used_by_template,
            "sections": usage.get(name, []),
            "default": defaults.get(name),
        }
        if field["image"]:
            field.update(IMAGE_FIELD_META.get(name, {}))
            image_fields.append(name)
        if definition["derived"]:
            derived_fields.append(name)
        elif definition["manual"]:
            manual_fields.append(name)
        if definition["required"]:
            required_fields.append(name)
        else:
            optional_fields.append(name)
        fields[name] = field

    external_fields: dict[str, dict[str, Any]] = {
        name: {"name": name, "source": source, "sections": []}
        for name, source in {
            **COMMON_EXTERNAL_TEMPLATE_FIELDS,
            **PAGE_EXTERNAL_TEMPLATE_FIELDS.get(page_type, {}),
        }.items()
    }
    for section in sections:
        for name, source in section.get("external_fields", {}).items():
            entry = external_fields.setdefault(
                name, {"name": name, "source": source, "sections": []}
            )
            if section["section"] not in entry["sections"]:
                entry["sections"].append(section["section"])

    return {
        "page_type": page_type,
        # Section order is the template's order — the list is already ordered.
        "sections": [
            {
                "section": s["section"],
                "label": s["label"],
                "order": index,
                "required": s["required"],
                "fields_used": sorted(
                    {
                        n
                        for entry in s["required_fields"]
                        for n in (entry if isinstance(entry, (list, tuple, set)) else [entry])
                    }
                    | set(s["optional_fields"])
                ),
                "required_fields": s["required_fields"],
                "optional_fields": s["optional_fields"],
                "always_rendered": s["always_rendered"],
                "fabricated_when_empty": s["fabricated_when_empty"],
                "data_source": s["data_source"],
                "external_fields": dict(s.get("external_fields", {})),
            }
            for index, s in enumerate(sections)
        ],
        "fields": fields,
        "required_fields": sorted(required_fields),
        "optional_fields": sorted(optional_fields),
        "manual_fields": sorted(manual_fields),
        "derived_fields": sorted(derived_fields),
        "image_fields": sorted(image_fields),
        "template_fields": sorted(usage),
        "external_fields": external_fields,
        "defaults": dict(defaults),
    }
