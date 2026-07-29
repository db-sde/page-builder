import re
import logging
from typing import Any, Optional, Tuple, List, Dict

logger = logging.getLogger("ingestion.adapter")

def clean_whitespace(val: Any) -> Any:
    if isinstance(val, str):
        return re.sub(r"\s+", " ", val).strip()
    return val

EMPTY_STRINGS = {"", "na", "n/a", "none", "null", "-", "—"}

def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in EMPTY_STRINGS
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False

def merge_micro_and_local(micro: Dict[str, Any], local: Dict[str, Any]) -> Dict[str, Any]:
    """
    Micro-First Merge Logic:
    - If a field is populated in micro, keep it.
    - If it is missing/null/empty in micro, use the local parser's value.
    """
    merged = {}
    all_keys = set(micro.keys()) | set(local.keys())
    for key in all_keys:
        micro_val = micro.get(key)
        local_val = local.get(key)
        if not is_empty(micro_val):
            merged[key] = micro_val
        else:
            merged[key] = local_val
    return merged


def adapt_schema(payload: Dict[str, Any], page_type: str) -> Dict[str, Any]:
    """
    Standardizes field names, performs simple type conversions, and cleans spacing.
    Strictly follows YAGNI - no AI or complex inference, just formats and maps.
    """
    adapted = {}
    for k, v in payload.items():
        adapted[k] = clean_whitespace(v)

    # 1. Page-type specific field name mappings
    if page_type == "course":
        # program_name / course_name normalization
        c_name = adapted.get("course_name")
        p_name = adapted.get("program_name")
        if c_name and not p_name:
            adapted["program_name"] = c_name
        elif c_name and p_name:
            if len(c_name) > len(p_name):
                adapted["program_name"] = c_name
        
        # fee / total_fee mapping
        if "fee" in adapted and "total_fee" not in adapted:
            adapted["total_fee"] = adapted["fee"]

    elif page_type == "specialization":
        # spec_name / specialization_name / title mapping
        s_name = adapted.get("specialization_name") or adapted.get("title")
        if s_name and not adapted.get("spec_name"):
            adapted["spec_name"] = s_name
            
        # fees / total_fee mapping
        if "fees" in adapted and "total_fee" not in adapted:
            adapted["total_fee"] = adapted["fees"]

    elif page_type == "university":
        # university_name / university_full_name mapping
        if adapted.get("university_full_name") and not adapted.get("university_name"):
            adapted["university_name"] = adapted["university_full_name"]

        # `ugc_approved` is the University Blueprint's canonical key. Keep
        # accepting historical parser payloads that used `ugc_status`, but do
        # not let new University records carry two names for the same value.
        if not adapted.get("ugc_approved") and adapted.get("ugc_status"):
            adapted["ugc_approved"] = adapted["ugc_status"]
        adapted.pop("ugc_status", None)

    # 2. Simple Type Conversions (Safe coercion, no guessing)
    # Established Year
    if "established_year" in adapted:
        val = adapted["established_year"]
        if isinstance(val, (int, float)):
            adapted["established_year"] = str(int(val))
        elif isinstance(val, str):
            digits = re.findall(r"\b\d{4}\b", val)
            if digits:
                adapted["established_year"] = digits[0]

    # Number of Programs
    if "num_programs" in adapted:
        val = adapted["num_programs"]
        if isinstance(val, (int, float)):
            adapted["num_programs"] = int(val)
        elif isinstance(val, str):
            digits = re.findall(r"\b\d+\b", val)
            if digits:
                adapted["num_programs"] = int(digits[0])

    # Credits
    if "credits" in adapted:
        val = adapted["credits"]
        if isinstance(val, (int, float)):
            adapted["credits"] = int(val)
        elif isinstance(val, str):
            digits = re.findall(r"\b\d+\b", val)
            if digits:
                adapted["credits"] = int(digits[0])

    return adapted


def validate_schema(payload: Dict[str, Any], page_type: str) -> List[Dict[str, str]]:
    """
    Validates structured fields for data type, length, or paragraph leaks.
    Logs warning messages and returns warning dictionaries.
    """
    warnings = []

    # Helper function to register and log warning
    def add_warning(field: str, expected: str, received: Any):
        rec_type = type(received).__name__
        rec_val = str(received)
        if len(rec_val) > 40:
            rec_val = rec_val[:37] + "..."
            
        # Check if received is a paragraph (has multiple sentences or is long)
        if isinstance(received, str) and (len(received) > 100 or len(re.split(r"\.\s+", received)) > 1):
            rec_type = "Paragraph"

        warning_info = {
            "field": field,
            "expected": expected,
            "received": rec_type,
            "value": rec_val,
            "source": "Micro Parser",
            "action": "Kept Micro Value"
        }
        warnings.append(warning_info)
        
        # Log to terminal in user's requested format
        print(f"\n[VALIDATION WARNING]\nField:\n{field}\n\nExpected:\n{expected}\n\nReceived:\n{rec_type}\n\nSource:\nMicro Parser\n\nAction:\nKept Micro Value\n")

    # Field-specific Validation Rules
    # NAAC Grade
    if "naac_grade" in payload:
        grade = payload["naac_grade"]
        if grade is not None:
            if not isinstance(grade, str):
                add_warning("naac_grade", "Short grade string (e.g. 'A++')", grade)
            elif len(grade) > 10 or len(re.split(r"\.\s+", grade)) > 1:
                add_warning("naac_grade", "Short grade string (e.g. 'A++')", grade)

    # UGC Approved Status
    for ugc_key in ["ugc_approved", "ugc_status"]:
        if ugc_key in payload:
            ugc = payload[ugc_key]
            if ugc is not None:
                if not isinstance(ugc, str):
                    add_warning(ugc_key, "Short approval status string (e.g. 'Entitled')", ugc)
                elif len(ugc) > 60 or len(re.split(r"\.\s+", ugc)) > 1:
                    add_warning(ugc_key, "Short approval status string (e.g. 'Entitled')", ugc)

    # AICTE Status
    if "aicte_status" in payload:
        aicte = payload["aicte_status"]
        if aicte is not None:
            if not isinstance(aicte, (str, bool)):
                add_warning("aicte_status", "Short status string or Boolean", aicte)
            elif isinstance(aicte, str) and (len(aicte) > 60 or len(re.split(r"\.\s+", aicte)) > 1):
                add_warning("aicte_status", "Short status string or Boolean", aicte)

    # NIRF Rank
    for nirf_key in ["nirf_rank", "nirf_rating"]:
        if nirf_key in payload:
            nirf = payload[nirf_key]
            if nirf is not None:
                if not isinstance(nirf, (str, int)):
                    add_warning(nirf_key, "Short rank string or Integer (e.g. 'Rank #24' or 24)", nirf)
                elif isinstance(nirf, str) and (len(nirf) > 60 or len(re.split(r"\.\s+", nirf)) > 1):
                    add_warning(nirf_key, "Short rank string or Integer", nirf)

    # Established Year
    if "established_year" in payload:
        est = payload["established_year"]
        if est is not None:
            if not isinstance(est, (str, int)):
                add_warning("established_year", "4-digit Year (e.g. 1981)", est)
            elif isinstance(est, str) and not re.match(r"^\d{4}$", est.strip()):
                add_warning("established_year", "4-digit Year (e.g. 1981)", est)

    # Number of Programs
    if "num_programs" in payload:
        num = payload["num_programs"]
        if num is not None:
            if not isinstance(num, int):
                add_warning("num_programs", "Integer (e.g. 4)", num)

    # Starting Fee / Total Fee
    for fee_key in ["starting_fee", "total_fee"]:
        if fee_key in payload:
            fee = payload[fee_key]
            if fee is not None:
                if isinstance(fee, str) and (len(fee) > 150 or len(re.split(r"\bfor\b|\bplan\b", fee, re.I)) > 2):
                    add_warning(fee_key, "Short fee amount / format string (e.g. 'INR 1,31,000 /-')", fee)

    # Learning Mode
    for mode_key in ["mode", "mode_of_learning"]:
        if mode_key in payload:
            mode = payload[mode_key]
            if mode is not None:
                if not isinstance(mode, str):
                    add_warning(mode_key, "Short mode string (e.g. 'Online')", mode)
                elif len(mode) > 50 or len(re.split(r"\.\s+", mode)) > 1:
                    add_warning(mode_key, "Short mode string (e.g. 'Online')", mode)

    # Duration
    if "duration" in payload:
        dur = payload["duration"]
        if dur is not None:
            if not isinstance(dur, str):
                add_warning("duration", "Short duration string (e.g. '2 years')", dur)
            elif len(dur) > 50 or len(re.split(r"\.\s+", dur)) > 1:
                add_warning("duration", "Short duration string (e.g. '2 years')", dur)

    # Credits
    if "credits" in payload:
        cred = payload["credits"]
        if cred is not None:
            if not isinstance(cred, int):
                add_warning("credits", "Integer (e.g. 80)", cred)

    return warnings

def adapt_and_validate(payload: Dict[str, Any], page_type: str) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """Runs the adaptation first, then validates the adapted values."""
    adapted = adapt_schema(payload, page_type)
    warnings = validate_schema(adapted, page_type)
    return adapted, warnings
