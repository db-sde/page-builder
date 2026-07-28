from transformers.specialization import SpecializationTransformer
from transformers.course import CourseTransformer
from transformers.university import UniversityTransformer
from transformers.blog import BlogTransformer
from transformers.programs_listing import ProgramsListingTransformer
from transformers.specializations_listing import SpecializationsListingTransformer
from transformers.blog_listing import BlogListingTransformer
from transformers.contact import ContactTransformer

TRANSFORMER_MAP = {
    "specialization": SpecializationTransformer,
    "course": CourseTransformer,
    "university": UniversityTransformer,
    "blog": BlogTransformer,
    "programs_listing": ProgramsListingTransformer,
    "specializations_listing": SpecializationsListingTransformer,
    "blog_listing": BlogListingTransformer,
    "contact": ContactTransformer,
}

import re

def normalize_value(val):
    """
    Recursively normalize string values like NA, N/A, n/a, na, Not Available,
    Not Applicable, hyphens/dashes, null, NULL, None, and NONE to None.
    """
    if isinstance(val, dict):
        return {k: normalize_value(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [normalize_value(item) for item in val]
    elif isinstance(val, str):
        s = val.strip()
        if s.lower() in ("na", "n/a", "null", "none", "not available", "not applicable"):
            return None
        if re.match(r'^[-—]+$', s):
            return None
        return val
    return val

def get_transformer(resolved: dict):
    # Apply recursive normalization before any transformer runs
    normalized_resolved = normalize_value(resolved)
    page_type = normalized_resolved["page_type"]
    cls = TRANSFORMER_MAP.get(page_type)
    if not cls:
        raise ValueError(f"No transformer for page_type: {page_type}")
    return cls(normalized_resolved)
