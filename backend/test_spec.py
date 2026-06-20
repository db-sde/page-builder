import json
import sys
from pathlib import Path

# Add backend root to path
sys.path.append(str(Path(__file__).resolve().parent))

from renderer.engine import render_resolved

def run_test():
    test_file = Path(__file__).resolve().parent / "generated" / "specialization_test_payload.json"
    if not test_file.exists():
        print(f"Error: {test_file} does not exist.")
        return

    with open(test_file, "r", encoding="utf-8") as f:
        debug_data = json.load(f)

    payload = debug_data["payload"]
    page_type = debug_data["page_type"]

    # Reconstruct the merged payload similar to main.py preview_html flow
    acf_data = payload.copy()
    acf_data["page_type"] = page_type
    acf_data["slug"] = "manipal-online-mba-in-human-resource-management"
    acf_data["university_slug"] = "manipal"
    acf_data["parent_slug"] = "manipal-online-mba"

    # Test case 1: Default payload (fee_plans is null/None)
    resolved_default = {
        "slug": acf_data["slug"],
        "page_type": acf_data["page_type"],
        "university_slug": acf_data["university_slug"],
        "parent_slug": acf_data["parent_slug"],
        "raw": acf_data.copy()
    }

    # Test case 2: String values (as reported in error trace and user input cases)
    acf_data_str_override = acf_data.copy()
    acf_data_str_override["fee_plans"] = "INR 1,75,000/-"
    acf_data_str_override["highlights"] = "Top placement support"
    acf_data_str_override["job_profiles"] = "HR Manager role"
    acf_data_str_override["reviews"] = "Excellent learning platform"
    acf_data_str_override["faqs"] = "UGC approved specialization"
    
    resolved_str_override = {
        "slug": acf_data["slug"],
        "page_type": acf_data["page_type"],
        "university_slug": acf_data["university_slug"],
        "parent_slug": acf_data["parent_slug"],
        "raw": acf_data_str_override
    }

    for name, res in [("Default Payload", resolved_default), ("String Override Payload", resolved_str_override)]:
        try:
            print(f"\n--- Running Test Case: {name} ---")
            html = render_resolved(res)
            print(f"Success! HTML rendered successfully for {name}. Length: {len(html)}")
            
            # Save HTML to generated folder
            suffix = "default" if "Default" in name else "override"
            out_file = Path(__file__).resolve().parent / "generated" / f"specialization_test_{suffix}_output.html"
            with open(out_file, "w", encoding="utf-8") as out:
                out.write(html)
            print(f"Saved output to: {out_file}")
        except Exception as e:
            print(f"Failure in Test Case: {name}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()


