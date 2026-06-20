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
