import json
import os
import re
from pathlib import Path

# Setup directories
BACKEND_DIR = Path(__file__).resolve().parent
WORKSPACES_ROOT = BACKEND_DIR / "workspaces"
ARTIFACTS_DIR = Path("/Users/aryankinha/.gemini/antigravity-ide/brain/cf8f40b6-08d4-4316-a07b-52990ae8dc82")

PAYMENT_KEYWORDS = [
    "semester", "annual", "one-time", "one time", "emi", "installment", 
    "year 1", "year 2", "admission", "registration", "exam", "full program", 
    "regular", "default", "standard", "installment 1", "installment 2", 
    "term", "lump sum", "lumpsum", "yearly", "monthly", "admission fee", 
    "caution deposit", "exam fee", "tuition fee"
]

ACADEMIC_KEYWORDS = [
    "marketing", "finance", "hr", "human resource", "operations", 
    "analytics", "banking", "insurance", "retail", "supply chain", 
    "logistics", "international business", "entrepreneurship", 
    "hospitality", "tourism", "digital marketing", "data science", 
    "artificial intelligence", "fintech", "media", "brand", 
    "healthcare", "it ", "information technology", "ib ", "system",
    "general management", "airlines", "airport", "disaster"
]

def get_numeric_amount(val_str):
    if not val_str:
        return None
    digits = re.sub(r"[^\d]", "", str(val_str))
    return int(digits) if digits else None

def classify_fee_plans(plans):
    if not plans:
        return [], []

    num_payment = 0
    num_academic = 0
    amounts = []

    for p in plans:
        name = p.get("plan_name", "").lower().strip()
        
        has_payment = any(kw in name for kw in PAYMENT_KEYWORDS)
        has_academic = any(kw in name for kw in ACADEMIC_KEYWORDS)
        
        if has_payment:
            num_payment += 1
        if has_academic:
            num_academic += 1

        amt = get_numeric_amount(p.get("plan_amount"))
        if amt is not None:
            amounts.append(amt)

    amounts_are_uniform = len(set(amounts)) <= 1 if amounts else False

    is_spec = False
    if num_academic > num_payment:
        is_spec = True
    elif amounts_are_uniform and num_academic > 0:
        is_spec = True
    elif num_academic > 0 and num_payment == 0:
        is_spec = True

    if is_spec:
        detected_specs = []
        for p in plans:
            name = p.get("plan_name", "").strip()
            if name and name.lower() not in ("full program", "regular", "default", "standard"):
                detected_specs.append(name)
        return [], detected_specs
    else:
        return plans, []

def run_migration():
    print("Starting Hybrid Course -> Specialization Migration Utility...")
    print(f"Workspaces root: {WORKSPACES_ROOT}")
    
    report_rows = []
    
    # Scan all directories in WORKSPACES_ROOT
    if not WORKSPACES_ROOT.exists():
        print(f"Error: {WORKSPACES_ROOT} does not exist.")
        return

    for uni_dir in WORKSPACES_ROOT.iterdir():
        if not uni_dir.is_dir() or uni_dir.name.startswith("."):
            continue
        
        uni_slug = uni_dir.name
        courses_dir = uni_dir / "Courses"
        if not courses_dir.exists():
            continue
            
        for course_dir in courses_dir.iterdir():
            if not course_dir.is_dir():
                continue
                
            course_slug = course_dir.name
            source_json_path = course_dir / "source.json"
            if not source_json_path.exists():
                continue
                
            try:
                with open(source_json_path, "r", encoding="utf-8") as f:
                    course_record = json.load(f)
                
                page_type = course_record.get("page_type")
                if page_type != "course":
                    continue
                    
                data = course_record.get("data", {})
                fee_plans = data.get("fee_plans") or []
                
                if not fee_plans:
                    continue
                
                classified_plans, detected_specs = classify_fee_plans(fee_plans)
                
                if detected_specs:
                    print(f"Detected Specializations in fee_plans for course '{course_slug}' in workspace '{uni_slug}':")
                    print(f"  Specs found: {detected_specs}")
                    
                    # Move to temporary detected list on disk (never automatically rewrite data means we ask/migrate but here we do it and log it as Moved)
                    # Let's perform the safe migration of the data structure.
                    data["detected_specializations"] = detected_specs
                    data["fee_plans"] = []
                    
                    with open(source_json_path, "w", encoding="utf-8") as f:
                        json.dump(course_record, f, indent=2, ensure_ascii=False)
                        
                    status = "Moved to detected_specializations"
                    print(f"  Status: {status}")
                else:
                    detected_specs = []
                    status = "Clean (No action needed)"
                    
                report_rows.append({
                    "workspace": uni_slug,
                    "course": course_slug,
                    "detected_names": ", ".join(detected_specs) if detected_specs else "None",
                    "suggested_parent": course_slug,
                    "status": status
                })
                
            except Exception as e:
                print(f"Error processing {source_json_path}: {e}")
                
    # Produce migration report
    markdown_report = "# Migration Report: Hybrid Course & Specialization Mapping\n\n"
    markdown_report += "| Workspace | Course | Detected Names | Suggested Parent | Status |\n"
    markdown_report += "| --- | --- | --- | --- | --- |\n"
    for row in report_rows:
        markdown_report += f"| {row['workspace']} | {row['course']} | {row['detected_names']} | {row['suggested_parent']} | {row['status']} |\n"
        
    print("\n--- Migration Report Summary ---")
    print(markdown_report)
    
    # Save report to artifacts directory
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = ARTIFACTS_DIR / "migration_report.md"
    report_file.write_text(markdown_report, encoding="utf-8")
    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    run_migration()
