# TODO: add AI gap-fill hook here — if required field is None, call Groq before skipping section

from abc import ABC, abstractmethod
from typing import Any
from core.site_config import get_site_config
from core.utils import build_public_route, format_fee
import re

class BaseTransformer(ABC):
    def __init__(self, resolved: dict):
        self.slug = resolved["slug"]
        self.page_type = resolved["page_type"]
        self.parent_slug = resolved.get("parent_slug")
        self.university_slug = resolved.get("university_slug")
        self.raw = resolved["raw"]          # the ACF data dict
        
        from workspace.knowledge import load_or_create_knowledge
        self.knowledge = load_or_create_knowledge(self.university_slug) if self.university_slug else {}
        
        uni_name_val = self.resolve("university_name")
        self.site = get_site_config(self.university_slug, uni_name_val)

    def resolve(self, field: str, default: Any = None) -> Any:
        from workspace.knowledge import resolve_field
        return resolve_field(self.raw, self.knowledge, field, default)

    def resolve_list(self, field: str, default: Any = None) -> list:
        from workspace.knowledge import resolve_list
        return resolve_list(self.raw, self.knowledge, field, default)

    def format_fee(self, amount_str: str) -> str:
        # Delegates to the single canonical implementation in core/utils.py
        # (previously duplicated verbatim here and as clean_fee in
        # renderer/engine.py).
        return format_fee(amount_str)

    def build_breadcrumbs(self, crumbs: list[dict]) -> list[dict]:
        # Validates and returns the breadcrumbs list; template handles rendering.
        return crumbs

    def public_route(self, page_type: str, slug: str = "") -> str:
        return build_public_route(page_type, slug, self.university_slug)

    def build_pills(self, fields: list[tuple]) -> list[dict]:
        pills = []
        for value, label in fields:
            if value is None or value == "":
                continue
            if label:
                pills.append({"label": f"{label}: {value}"})
            else:
                pills.append({"label": f"{value}"})
        return pills

    def build_stats(self, pairs: list[tuple]) -> list[dict]:
        stats = []
        for value, key in pairs:
            if value is not None and str(value).strip() not in ("", "None"):
                stats.append({"v": value, "k": key})
        return stats

    def build_rail(self, sections: list[tuple]) -> list[dict]:
        rail = []
        for anchor, label, condition in sections:
            if condition:
                rail.append({"href": f"#{anchor}", "label": label})
        return rail

    def build_reviewer(self, reviewer_label: str) -> dict:
        if not reviewer_label:
            return {"name": "", "role": "", "initial": ""}
        if "," in reviewer_label:
            name, role = reviewer_label.split(",", 1)
            name = name.strip()
            role = role.strip()
        else:
            name = reviewer_label.strip()
            role = ""
        initial = name[0].upper() if name else ""
        return {"name": name, "role": role, "initial": initial}

    def build_reviews(self, reviews: list[dict]) -> list[dict]:
        if not reviews or not isinstance(reviews, list):
            return []
        enriched = []
        for item in reviews:
            if not isinstance(item, dict):
                continue
            parsed = self.build_reviewer(item.get("reviewer_label", ""))
            enriched.append({
                "q": item.get("review_text", ""),
                "name": parsed["name"],
                "role": parsed["role"],
                "initial": parsed["initial"]
            })
        return enriched

    def section_or_none(self, key: str) -> str | None:
        val = self.raw.get(key)
        if isinstance(val, str) and val.strip():
            return val
        return None

    def clean_str(self, val) -> str | None:
        if val is None:
            return None
        s = str(val).strip()
        if not s or s.upper() in ("NA", "N/A", "NIL", "-", "--", "NONE", "NULL"):
            return None
        return s

    def clean_emi_amount(self, emi_amount) -> str | None:
        """Keep EMI details only when the value contains actual information."""
        clean = self.clean_str(emi_amount)
        if not clean:
            return None

        # Parser placeholders such as "INR /-" are truthy strings but do not
        # communicate an EMI amount or other financing detail.
        content = re.sub(r"\b(?:inr|rs)\b|[₹/.,\-\s]", "", clean, flags=re.IGNORECASE)
        return clean if content else None

    def build_fee_note(self, emi_amount: str) -> str | None:
        clean = self.clean_emi_amount(emi_amount)
        if not clean:
            return None
        # Strip INR prefix (case-insensitive)
        clean = re.sub(r'^INR\s*', '', clean, flags=re.IGNORECASE).strip()
        # Ensure ₹ prefix
        if not clean.startswith("₹"):
            clean = f"₹{clean}"
        return f"No-cost EMI from approximately {clean}."

    @abstractmethod
    def transform(self) -> dict:
        """Return the complete page context dict for the template."""
        pass
