"""Editing State — the single payload the editor screen needs (Phase 3).

```
Parser JSON  +  Field Definitions  +  Page Blueprint  ->  Editing State
```

The editor should open on an almost-complete page. Everything the parser could
extract is already filled, derived values are already resolved, explicit
defaults are already applied, and the only things left empty are the fields a
document genuinely cannot supply (uploaded images, and any content the DOCX did
not contain).

The frontend must not recompute any of this: every field already carries
``value / source / required / optional / manual / derived / missing`` and every
section already carries ``renderable / missing fields / completion``.

Read-only: parsed values are never mutated in place. ``apply_auto_population``
returns a new dict.
"""

from typing import Any

from core.field_definitions import build_field_state
from core.page_blueprint import build_page_blueprint
from core.page_requirements import build_page_state


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set)):
        return not value
    return False


def apply_auto_population(page_type: str, values: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Fill explicitly declared defaults for fields the parser did not supply.

    Returns ``(new_values, auto_filled_field_names)``. The input dict is not
    modified. Only defaults declared in ``page_blueprint.EXPLICIT_DEFAULTS`` are
    applied — never editorial content.
    """
    blueprint = build_page_blueprint(page_type)
    if not blueprint:
        return dict(values), []

    populated = dict(values)
    auto_filled: list[str] = []
    for name, default in blueprint["defaults"].items():
        if _is_missing(populated.get(name)) and not _is_missing(default):
            populated[name] = default
            auto_filled.append(name)
    return populated, sorted(auto_filled)


def build_editing_state(
    page_type: str,
    values: dict[str, Any],
    derived_values: dict[str, Any] | None = None,
    *,
    auto_populate: bool = True,
    auto_filled_names: list[str] | None = None,
) -> dict[str, Any]:
    """Build the complete editor payload for a page.

    ``values`` is the parser/ACF dict. ``derived_values`` carries the pipeline's
    resolved ``page_type / slug / university_slug / parent_slug``.

    Returns ``{}`` for unsupported page types.
    """
    blueprint = build_page_blueprint(page_type)
    if not blueprint:
        return {}

    if auto_filled_names is not None:
        # Caller already ran apply_auto_population (e.g. at ingest time) and
        # tells us what it filled, so the editor can still label those fields.
        effective_values, auto_filled = dict(values), sorted(auto_filled_names)
    elif auto_populate:
        effective_values, auto_filled = apply_auto_population(page_type, values)
    else:
        effective_values, auto_filled = dict(values), []

    field_state = build_field_state(page_type, effective_values, derived_values)
    page_state = build_page_state(page_type, field_state)

    blueprint_fields = blueprint["fields"]

    fields: dict[str, dict[str, Any]] = {}
    needs_attention: list[str] = []
    optional_suggestions: list[str] = []
    missing_images: list[str] = []

    for name, entry in field_state.items():
        spec = blueprint_fields.get(name, {})
        usage = page_state["field_usage"].get(name, {})
        field = {
            **entry,
            "image": bool(spec.get("image")),
            "used_by_template": bool(usage.get("used_by_template")),
            "infrastructure": bool(usage.get("infrastructure")),
            "sections": usage.get("sections", []),
            "auto_filled": name in auto_filled,
            "in_schema": name in blueprint_fields,
        }
        for meta_key in ("label", "hint", "dims"):
            if spec.get(meta_key):
                field[meta_key] = spec[meta_key]

        # What the operator must still do, and nothing more.
        if field["missing"] and not field["infrastructure"]:
            if field["required"]:
                needs_attention.append(name)
                if field["image"]:
                    missing_images.append(name)
            elif field["manual"]:
                # Manual-but-optional (e.g. reviews): offered, never warned about.
                optional_suggestions.append(name)

        field["needs_attention"] = name in needs_attention
        fields[name] = field

    sections = []
    for section in page_state["sections"]:
        used = section["fields_used"]
        filled = [n for n in used if n in fields and not fields[n]["missing"]]
        sections.append({
            **section,
            "filled_fields": filled,
            "completion": round(len(filled) / len(used), 2) if used else None,
        })

    total_required = [n for n, f in fields.items() if f["required"] and not f["infrastructure"]]
    complete_required = [n for n in total_required if not fields[n]["missing"]]

    return {
        "page_type": page_type,
        "fields": fields,
        "sections": sections,
        "auto_filled": auto_filled,
        "needs_attention": sorted(needs_attention),
        "optional_suggestions": sorted(optional_suggestions),
        "missing_images": sorted(missing_images),
        # Unused schema fields are preserved and reported, never warned about.
        "unused_schema_fields": page_state["unused_schema_fields"],
        "summary": {
            "required_total": len(total_required),
            "required_complete": len(complete_required),
            "ready": not needs_attention,
            "required_sections_incomplete": page_state["summary"]["required_sections_incomplete"],
            "optional_sections_incomplete": page_state["summary"]["optional_sections_incomplete"],
            "renderable_sections": page_state["summary"]["renderable_sections"],
        },
    }


def validate_required_content(
    page_type: str,
    values: dict[str, Any],
    derived_values: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    """Validate one page using the canonical Blueprint field requirements.

    Returns ``(populated_values, editing_state, missing_fields)`` so preview,
    save, and publish paths can share the same decision without duplicating
    required-field lists. Unsupported legacy page types remain valid.
    """
    populated, auto_filled = apply_auto_population(page_type, values)
    editing_state = build_editing_state(
        page_type,
        populated,
        derived_values,
        auto_populate=False,
        auto_filled_names=auto_filled,
    )
    if not editing_state:
        return populated, editing_state, []

    missing_fields: list[dict[str, str]] = []
    for name in editing_state["needs_attention"]:
        field = editing_state["fields"][name]
        missing_fields.append({
            "field": name,
            "label": field.get("label") or name.replace("_", " ").title(),
        })
    return populated, editing_state, missing_fields
