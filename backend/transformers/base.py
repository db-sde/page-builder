# TODO: add AI gap-fill hook here — if required field is None, call Groq before skipping section

from abc import ABC, abstractmethod
from core.site_config import SITE_CONFIG
import re

class BaseTransformer(ABC):
    def __init__(self, resolved: dict):
        self.slug = resolved["slug"]
        self.page_type = resolved["page_type"]
        self.parent_slug = resolved.get("parent_slug")
        self.university_slug = resolved.get("university_slug")
        self.raw = resolved["raw"]          # the ACF data dict
        self.site = SITE_CONFIG

    def format_fee(self, amount_str: str) -> str:
        if not amount_str:
            return ""
        s = str(amount_str).strip()
        if not s or s.upper() in ("NA", "N/A", "NIL", "FREE", "-", "--"):
            return ""
        # Already formatted correctly
        if s.startswith("₹"):
            return s
        # Strip INR prefix (case-insensitive)
        s = re.sub(r'^INR\s*', '', s, flags=re.IGNORECASE).strip()
        # Strip trailing garbage: /-, /--, /year, /sem etc
        s = re.sub(r'\s*/[-–]+.*$', '', s).strip()
        s = re.sub(r'\s*/\s*(year|sem|semester|month|mo).*$', '', s, flags=re.IGNORECASE).strip()
        # Strip any non-numeric/comma/dot characters remaining at end
        s = re.sub(r'[^0-9,.].*$', '', s).strip()
        if not s:
            return ""
        return f"₹{s}"

    def build_breadcrumbs(self, crumbs: list[dict]) -> list[dict]:
        # Validates and returns the breadcrumbs list; template handles rendering.
        return crumbs

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

    def build_fee_note(self, emi_amount: str) -> str | None:
        if not emi_amount:
            return None
        clean = str(emi_amount).strip()
        if clean.upper() in ("NA", "N/A", "NIL", "-", "--", ""):
            return None
        # Ensure ₹ prefix
        if not clean.startswith("₹"):
            clean = f"₹{clean}"
        return f"No-cost EMI from approximately {clean} · Semester-wise payment lets you start with just ₹50,000."

    @abstractmethod
    def transform(self) -> dict:
        """Return the complete page context dict for the template."""
        pass
