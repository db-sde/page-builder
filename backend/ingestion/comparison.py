import json
import re
from copy import deepcopy
from typing import Any


EMPTY_STRINGS = {"", "na", "n/a", "none", "null", "-", "—"}

COMPARISON_FIELDS = {
    "university": [
        "university_name", "university_full_name", "established_year",
        "naac_grade", "ugc_status", "aicte_status", "nirf_rank",
        "rankings", "approvals", "accreditations", "about_content",
        "why_choose_content", "programs_table", "admission_steps",
        "emi_content", "exam_content", "placement_content", "faqs", "reviews",
    ],
    "course": [
        "program_name", "course_name", "duration", "mode", "eligibility",
        "eligibility_content", "total_fee", "fee", "fee_note", "fee_plans",
        "admission_process", "admission_steps", "syllabus", "syllabus_content",
        "credits", "naac_grade", "ugc_status", "about_content", "highlights",
        "placement_content", "faqs", "reviews", "detected_specializations",
    ],
    "specialization": [
        "spec_name", "specialization_name", "title", "parent", "parent_slug",
        "duration", "eligibility", "eligibility_content", "fees", "total_fee",
        "fee_plans", "about_content", "highlights", "admission_steps",
        "syllabus_content", "placement_content", "certificate_description",
        "job_profiles", "faqs", "reviews",
    ],
    "blog": [
        "title", "author", "author_role", "published_date", "date",
        "reading_time", "read_time", "excerpt", "tag", "content_html",
    ],
}


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in EMPTY_STRINGS
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def normalize_for_compare(value: Any) -> str:
    if is_empty(value):
        return ""
    if isinstance(value, str):
        text = re.sub(r"\s+", " ", value).strip().lower()
        return text
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def build_comparison_report(micro: dict, local: dict, page_type: str) -> dict:
    fields = set(COMPARISON_FIELDS.get(page_type, []))
    fields.update(local.keys())
    fields -= {
        "blocks", "hero_image_url", "hero_image_alt", "certificate_image_url",
        "og_image_url", "featured_image_url",
    }

    rows = []
    totals = {
        "fields_compared": 0,
        "matches": 0,
        "conflicts": 0,
        "missing_micro": 0,
        "missing_local": 0,
    }

    for field in sorted(fields):
        micro_value = micro.get(field)
        local_value = local.get(field)
        micro_empty = is_empty(micro_value)
        local_empty = is_empty(local_value)

        if micro_empty and local_empty:
            continue
        if micro_empty:
            status = "MISSING_MICRO"
            totals["missing_micro"] += 1
        elif local_empty:
            status = "MISSING_LOCAL"
            totals["missing_local"] += 1
        elif normalize_for_compare(micro_value) == normalize_for_compare(local_value):
            status = "MATCH"
            totals["matches"] += 1
        else:
            status = "CONFLICT"
            totals["conflicts"] += 1

        totals["fields_compared"] += 1
        rows.append({
            "field": field,
            "micro": micro_value,
            "local": local_value,
            "status": status,
        })

    return {
        "page_type": page_type,
        "summary": totals,
        "fields": rows,
    }


def merge_with_micro_primary(micro: dict, local: dict, page_type: str) -> tuple[dict, dict]:
    merged = deepcopy(micro)
    report = build_comparison_report(micro, local, page_type)

    for row in report["fields"]:
        if row["status"] == "MISSING_MICRO":
            merged[row["field"]] = row["local"]

    return merged, report
