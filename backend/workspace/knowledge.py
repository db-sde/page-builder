import json
from pathlib import Path
from typing import Any, Optional
from workspace.manager import WORKSPACES_ROOT

# Mapping from incoming page payload fields to paths in university_knowledge.json
FIELD_MAPPING = {
    # identity
    "university_name": ("identity", "university_name"),
    "university_full_name": ("identity", "university_full_name"),
    
    # approvals
    "naac_grade": ("approvals", "naac_grade"),
    "ugc_status": ("approvals", "ugc_status"),
    "ugc_approved": ("approvals", "ugc_status"),
    "aicte_status": ("approvals", "aicte_status"),
    "nirf_rank": ("approvals", "nirf_rank"),
    "nirf_rating": ("approvals", "nirf_rank"),
    
    # hero_stats
    "established_year": ("hero_stats", "established_year"),
    "num_programs": ("hero_stats", "num_programs"),
    "starting_fee": ("hero_stats", "starting_fee"),
    "total_fee": ("hero_stats", "starting_fee"),
    "fee": ("hero_stats", "starting_fee"),
    
    # assets
    "logo": ("assets", "logo"),
    "favicon": ("assets", "favicon"),
    "branding_logo": ("assets", "logo"),
    "branding_favicon": ("assets", "favicon"),
    "hero_image": ("assets", "hero_image"),
    "hero_image_url": ("assets", "hero_image"),
    
    # content
    "why_choose": ("content", "why_choose"),
    "why_choose_content": ("content", "why_choose"),
    "placement": ("content", "placement"),
    "placement_content": ("content", "placement"),
    "exam": ("content", "exam"),
    "exam_content": ("content", "exam"),
    "emi": ("content", "emi"),
    "emi_content": ("content", "emi"),
    "faculty_intro": ("content", "faculty_intro"),
    "admission_steps": ("content", "admission_steps"),
    
    # contact
    "email": ("contact", "email"),
    "address": ("contact", "address"),
    "phone": ("contact", "phone"),
    "whatsapp": ("contact", "whatsapp"),
}


def load_or_create_knowledge(university_slug: str) -> dict:
    """Load the university knowledge JSON file for a workspace or return a default template."""
    uni_slug = university_slug.lower().strip()
    path = WORKSPACES_ROOT / uni_slug / "university_knowledge.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "identity": {
            "slug": uni_slug,
            "university_name": "",
            "university_full_name": ""
        },
        "approvals": {
            "naac_grade": "",
            "ugc_status": "",
            "aicte_status": "",
            "nirf_rank": ""
        },
        "hero_stats": {
            "established_year": "",
            "num_programs": "",
            "starting_fee": ""
        },
        "assets": {
            "logo": "",
            "favicon": "",
            "hero_image": ""
        },
        "content": {
            "why_choose": "",
            "placement": "",
            "exam": "",
            "emi": "",
            "faculty_intro": "",
            "admission_steps": ""
        },
        "shared_lists": {
            "accreditations": [],
            "facts": [],
            "recruiters": [],
            "banks": [],
            "features": []
        },
        "contact": {
            "email": "",
            "address": "",
            "phone": "",
            "whatsapp": ""
        },
        "conflicts": []
    }


def save_knowledge(university_slug: str, data: dict) -> None:
    """Save the university knowledge JSON file for a workspace."""
    uni_slug = university_slug.lower().strip()
    path = WORKSPACES_ROOT / uni_slug / "university_knowledge.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def update_university_knowledge(university_slug: str, page_data: dict, page_type: str) -> None:
    """Extract university-wide fields from a transformed page payload and enrich university_knowledge.json."""
    if not page_data:
        return
        
    knowledge = load_or_create_knowledge(university_slug)
    
    # 1. Update/Extract single-value fields
    for field, path_info in FIELD_MAPPING.items():
        section, subkey = path_info
        val = page_data.get(field)
        if val is None or val == "":
            continue
            
        existing_val = knowledge[section].get(subkey)
        if existing_val is None or existing_val == "":
            knowledge[section][subkey] = str(val)
        elif str(existing_val) == str(val):
            continue
        else:
            # Record conflict
            conflict = {
                "field": f"{section}.{subkey}",
                "existing": str(existing_val),
                "incoming": str(val),
                "source": page_type
            }
            if conflict not in knowledge.setdefault("conflicts", []):
                knowledge["conflicts"].append(conflict)
                
    # 2. Update/Extract shared lists
    list_fields = {
        "accreditations": "accreditations",
        "facts": "facts",
        "recruiters": "recruiters",
        "banks": "banks",
        "features": "features",
    }
    for field, subkey in list_fields.items():
        val = page_data.get(field)
        if not val:
            continue
            
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except Exception:
                val = [val]
        if not isinstance(val, list):
            val = [val]
            
        existing_list = knowledge["shared_lists"].get(subkey) or []
        if not existing_list:
            knowledge["shared_lists"][subkey] = val
        elif existing_list == val:
            continue
        else:
            # Record conflict
            conflict = {
                "field": f"shared_lists.{subkey}",
                "existing": existing_list,
                "incoming": val,
                "source": page_type
            }
            if conflict not in knowledge.setdefault("conflicts", []):
                knowledge["conflicts"].append(conflict)
                
    save_knowledge(university_slug, knowledge)


def resolve_field(page_data: dict, knowledge: dict, field: str, default: Any = None) -> Any:
    """Resolve a field value according to the priority hierarchy: Page -> Knowledge -> System Default."""
    # 1. Page Value
    if page_data and field in page_data:
        val = page_data[field]
        if val is not None and val != "":
            return val
            
    # 2. University Knowledge Lookup
    if field in FIELD_MAPPING:
        section, subkey = FIELD_MAPPING[field]
        if knowledge and section in knowledge and subkey in knowledge[section]:
            val = knowledge[section][subkey]
            if val is not None and val != "":
                return val
                
    # 3. System Default Fallback
    return default


def resolve_list(page_data: dict, knowledge: dict, field: str, default: Any = None) -> list:
    """Resolve a list field: Page List -> Knowledge List -> Default List."""
    # 1. Page List
    if page_data and field in page_data:
        val = page_data[field]
        if val:
            if isinstance(val, str):
                try:
                    val = json.loads(val)
                except Exception:
                    pass
            if isinstance(val, list) and len(val) > 0:
                return val
                
    # 2. Knowledge List
    if knowledge and "shared_lists" in knowledge:
        val = knowledge["shared_lists"].get(field)
        if val and isinstance(val, list) and len(val) > 0:
            return val
            
    return default if default is not None else []
