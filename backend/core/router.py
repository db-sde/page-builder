from transformers.specialization import SpecializationTransformer
from transformers.course import CourseTransformer
from transformers.university import UniversityTransformer
from transformers.blog import BlogTransformer
from transformers.programs_listing import ProgramsListingTransformer
from transformers.specializations_listing import SpecializationsListingTransformer
from transformers.blog_listing import BlogListingTransformer

TRANSFORMER_MAP = {
    "specialization": SpecializationTransformer,
    "course": CourseTransformer,
    "university": UniversityTransformer,
    "blog": BlogTransformer,
    "programs_listing": ProgramsListingTransformer,
    "specializations_listing": SpecializationsListingTransformer,
    "blog_listing": BlogListingTransformer,
}

def get_transformer(resolved: dict):
    page_type = resolved["page_type"]
    cls = TRANSFORMER_MAP.get(page_type)
    if not cls:
        raise ValueError(f"No transformer for page_type: {page_type}")
    return cls(resolved)
