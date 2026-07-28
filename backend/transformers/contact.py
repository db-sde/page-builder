"""Transformer for the workspace-generated Contact page."""

import json

from core.site_config import get_site_config
from workspace.manager import WORKSPACES_ROOT


class ContactTransformer:
    """Resolve workspace-owned contact details without adding a CRM layer."""

    def __init__(self, resolved: dict):
        self.raw = resolved.get("raw") or {}
        self.university_slug = resolved.get("university_slug", "")

    def transform(self) -> dict:
        university_name = self.raw.get("university_name") or self.university_slug.replace("-", " ").title()
        programs = []
        seen_programs = set()
        for course in self.raw.get("_workspace_courses") or []:
            course_data = course.get("data") or {}
            course_slug = (course.get("slug") or "").strip()
            name = (
                course_data.get("program_name")
                or course_data.get("course_name")
                or course_data.get("title")
                or course_slug.replace("-", " ").title()
            )
            name = str(name).strip()
            if not name or name.casefold() in seen_programs:
                continue
            seen_programs.add(name.casefold())
            programs.append({"name": name, "slug": course_slug})
        programs.sort(key=lambda program: program["name"].casefold())

        metadata = {}
        try:
            metadata = json.loads(
                (WORKSPACES_ROOT / self.university_slug / "metadata.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            pass

        contact = metadata.get("contact") or {}
        site = get_site_config(self.university_slug, university_name)
        return {
            "seo_title": f"Contact {university_name}",
            "meta_description": f"Contact the admissions team at {university_name} for program information and support.",
            "university_name": university_name,
            "site": site,
            "contact_programs": programs,
            "contact_webhook": metadata.get("contact_webhook") or "",
            "contact_phone": contact.get("phone") or "",
            "contact_email": contact.get("email") or site.get("email") or "",
            "contact_address": contact.get("address") or site.get("address") or "",
            "contact_working_hours": contact.get("working_hours") or "",
            "contact_whatsapp": contact.get("whatsapp") or site.get("whatsapp") or "",
        }
