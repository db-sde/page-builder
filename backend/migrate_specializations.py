import json
import os
import sys
from pathlib import Path

# Add backend directory to path so core.utils and workspace package can be imported
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.append(str(BACKEND_DIR))

from core.utils import normalize_specialization_name
from workspace.compiler import compile_workspace

WORKSPACES_ROOT = BACKEND_DIR / "workspaces"
ARTIFACTS_DIR = Path("/Users/aryankinha/.gemini/antigravity-ide/brain/cf8f40b6-08d4-4316-a07b-52990ae8dc82")

def run_specialization_migration():
    print("Starting Hybrid Specialization Name Normalization Migration Utility...")
    print(f"Workspaces root: {WORKSPACES_ROOT}")
    
    report_rows = []
    workspaces_to_recompile = set()
    
    if not WORKSPACES_ROOT.exists():
        print(f"Error: {WORKSPACES_ROOT} does not exist.")
        return

    # Scan all university workspaces
    for uni_dir in WORKSPACES_ROOT.iterdir():
        if not uni_dir.is_dir() or uni_dir.name.startswith("."):
            continue
        
        uni_slug = uni_dir.name
        specs_dir = uni_dir / "Specializations"
        if not specs_dir.exists():
            continue
            
        for spec_dir in specs_dir.iterdir():
            if not spec_dir.is_dir():
                continue
                
            source_json_path = spec_dir / "source.json"
            if not source_json_path.exists():
                continue
                
            try:
                with open(source_json_path, "r", encoding="utf-8") as f:
                    spec_record = json.load(f)
                
                page_type = spec_record.get("page_type")
                if page_type != "specialization":
                    continue
                    
                parent_slug = spec_record.get("parent_slug")
                data = spec_record.get("data", {})
                
                # Resolve parent program name
                parent_program_name = None
                uni_name = uni_slug.upper()
                
                if parent_slug:
                    # Look up course source.json
                    course_dir = uni_dir / "Courses" / parent_slug
                    course_json_path = course_dir / "source.json"
                    if course_json_path.exists():
                        try:
                            with open(course_json_path, "r", encoding="utf-8") as cf:
                                course_record = json.load(cf)
                            c_raw = course_record.get("data", {})
                            uni_name = c_raw.get("university_name") or uni_name
                            names = [c_raw.get("program_name"), c_raw.get("course_name"), c_raw.get("title")]
                            parent_program_name = " ".join(filter(None, names))
                        except Exception as ce:
                            print(f"  Warning: failed to read parent course data: {ce}")

                
                if not parent_program_name:
                    parent_program_name = parent_slug.replace("-", " ").title() if parent_slug else ""
                
                # Get the old name/title for comparison
                old_name = data.get("spec_name") or ""
                
                # Normalize the fields inside the data dictionary
                changed = False
                for field in ["spec_name", "specialization_name", "title", "course_name", "hero_title", "hero_heading"]:
                    if field in data and isinstance(data[field], str) and data[field].strip():
                        val_old = data[field]
                        val_new = normalize_specialization_name(val_old, parent_program_name, uni_name)
                        if val_old != val_new:
                            data[field] = val_new
                            changed = True
                            
                if "hero" in data and isinstance(data["hero"], dict):
                    if "title" in data["hero"] and isinstance(data["hero"]["title"], str) and data["hero"]["title"].strip():
                        val_old = data["hero"]["title"]
                        val_new = normalize_specialization_name(val_old, parent_program_name, uni_name)
                        if val_old != val_new:
                            data["hero"]["title"] = val_new
                            changed = True
                
                # If changes were made, save them and mark workspace for recompile
                if changed:
                    with open(source_json_path, "w", encoding="utf-8") as f:
                        json.dump(spec_record, f, indent=2, ensure_ascii=False)
                    status = "Normalized"
                    workspaces_to_recompile.add(uni_slug)
                    print(f"  Normalized: {old_name} -> {data.get('spec_name')} (Workspace: {uni_slug})")
                else:
                    status = "Clean (No Change)"
                
                report_rows.append({
                    "workspace": uni_slug,
                    "parent_course": parent_slug or "None",
                    "old_title": old_name,
                    "new_title": data.get("spec_name") or old_name,
                    "status": status
                })
                
            except Exception as e:
                print(f"Error processing {source_json_path}: {e}")
                
    # Recompile modified workspaces
    for uni_slug in workspaces_to_recompile:
        print(f"Recompiling workspace '{uni_slug}'...")
        try:
            compile_workspace(uni_slug)
            print(f"  Workspace '{uni_slug}' successfully recompiled.")
        except Exception as e:
            print(f"  Error recompiling workspace '{uni_slug}': {e}")
            
    # Produce migration report
    markdown_report = "# Migration Report: Specialization Name Normalization\n\n"
    markdown_report += "| Workspace | Parent Course | Old Title | New Title | Status |\n"
    markdown_report += "| --- | --- | --- | --- | --- |\n"
    for row in report_rows:
        markdown_report += f"| {row['workspace']} | {row['parent_course']} | {row['old_title']} | {row['new_title']} | {row['status']} |\n"
        
    print("\n--- Migration Report Summary ---")
    print(markdown_report)
    
    # Save report to artifacts directory
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = ARTIFACTS_DIR / "specialization_normalization_report.md"
    report_file.write_text(markdown_report, encoding="utf-8")
    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    run_specialization_migration()
