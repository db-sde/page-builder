import argparse
import json
import os
from pathlib import Path
from ingestion.parser import parse_docx
from ingestion.extractor import extract_acf

def ingest(filepath: str, page_type: str, slug: str, university_slug: str, parent_slug: str = None):
    print(f"Parsing {filepath}...")
    blocks = parse_docx(filepath)
    print(f"  → {len(blocks)} blocks extracted")

    meta = {
        "program_name": slug.replace("-", " ").title() if page_type == "course" else None,
        "spec_name": slug.replace("-", " ").title() if page_type == "specialization" else None,
        "university_name": university_slug.upper() if university_slug else None,
    }
    meta = {k: v for k, v in meta.items() if v is not None}

    print(f"Extracting ACF fields for page_type={page_type}...")
    acf = extract_acf(blocks, page_type, meta)
    print(f"  → {len(acf)} fields extracted")

    if page_type == "specialization":
        parent_program_name = None
        uni_name = university_slug.upper() if university_slug else ""
        if parent_slug and university_slug:
            try:
                from workspace.manager import resolve_page_dir
                course_dir = resolve_page_dir(university_slug, "course", parent_slug)
                course_json_path = course_dir / "source.json"
                if course_json_path.exists():
                    import json
                    course_data = json.loads(course_json_path.read_text(encoding="utf-8"))
                    c_raw = course_data.get("data", {})
                    uni_name = c_raw.get("university_name") or uni_name
                    names = [c_raw.get("program_name"), c_raw.get("course_name"), c_raw.get("title")]
                    parent_program_name = " ".join(filter(None, names))
            except Exception:
                pass

        
        if not parent_program_name:
            parent_program_name = parent_slug.replace("-", " ").title() if parent_slug else ""
            
        from core.utils import normalize_specialization_name
        for field in ["spec_name", "specialization_name", "title", "course_name", "hero_title", "hero_heading"]:
            if field in acf and isinstance(acf[field], str) and acf[field].strip():
                acf[field] = normalize_specialization_name(acf[field], parent_program_name, uni_name)
                
        if "hero" in acf and isinstance(acf["hero"], dict):
            if "title" in acf["hero"] and isinstance(acf["hero"]["title"], str) and acf["hero"]["title"].strip():
                acf["hero"]["title"] = normalize_specialization_name(acf["hero"]["title"], parent_program_name, uni_name)


    record = {
        "slug": slug,
        "page_type": page_type,
        "university_slug": university_slug,
        "data": acf
    }
    if parent_slug:
        record["parent_slug"] = parent_slug

    base_dir = Path(__file__).resolve().parent.parent
    generated_dir = base_dir / "generated" / page_type
    generated_dir.mkdir(parents=True, exist_ok=True)
    json_path = generated_dir / f"{slug}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    print(f"Done. Extracted ACF JSON saved to {json_path}")
    return acf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a docx file into a standalone JSON file")
    parser.add_argument("--file", required=True, help="Path to .docx file")
    parser.add_argument("--type", required=True, choices=["course", "specialization", "university"], help="Page type")
    parser.add_argument("--slug", required=True, help="URL slug for this page")
    parser.add_argument("--university", required=True, help="University slug")
    parser.add_argument("--parent", default=None, help="Parent course slug (for specializations)")
    args = parser.parse_args()

    ingest(args.file, args.type, args.slug, args.university, args.parent)
