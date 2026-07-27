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
        "defaults": dict(defaults),
    }
