import sys
from pathlib import Path

# Add backend root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.router import normalize_value, get_transformer
from renderer.engine import render_resolved

def test_normalization():
    test_cases = [
        ("NA", None),
        ("N/A", None),
        ("n/a", None),
        ("Not Available", None),
        ("Not Applicable", None),
        ("-", None),
        ("--", None),
        ("--------------", None),
        ("—", None),  # em-dash
        ("null", None),
        ("NULL", None),
        ("None", None),
        ("NONE", None),
        ("A+", "A+"),
        ("A", "A"),
        ("B++", "B++"),
        ("UGC-approved", "UGC-approved"),
    ]

    print("--- Testing normalize_value function ---")
    all_passed = True
    for input_val, expected in test_cases:
        res = normalize_value(input_val)
        if res == expected:
            print(f"✓ Case {repr(input_val)}: normalized to {repr(res)}")
        else:
            print(f"✗ Case {repr(input_val)}: expected {repr(expected)}, got {repr(res)}")
            all_passed = False

    print("\n--- Testing recursive structures ---")
    nested_data = {
        "naac_grade": "NA",
        "ugc_approved": "N/A",
        "total_fee": "INR 1,65,000",
        "facts": [
            {"title": "Accreditation", "value": "Not Available"},
            {"title": "Approval", "value": "Entitled"}
        ]
    }
    normalized_nested = normalize_value(nested_data)
    expected_nested = {
        "naac_grade": None,
        "ugc_approved": None,
        "total_fee": "INR 1,65,000",
        "facts": [
            {"title": "Accreditation", "value": None},
            {"title": "Approval", "value": "Entitled"}
        ]
    }
    if normalized_nested == expected_nested:
        print("✓ Recursive structure test passed")
    else:
        print("✗ Recursive structure test failed")
        print("Got:", normalized_nested)
        all_passed = False

    # Render tests with naac_grade = "NA", "N/A", "-", null, "A+"
    render_test_cases = [
        {"naac_grade": "NA", "ugc_approved": "Entitled"},
        {"naac_grade": "N/A", "ugc_approved": "Entitled"},
        {"naac_grade": "-", "ugc_approved": "Entitled"},
        {"naac_grade": None, "ugc_approved": "Entitled"},
        {"naac_grade": "A+", "ugc_approved": "Entitled"}
    ]

    print("\n--- Testing Render and Output Safety ---")
    for idx, raw_data in enumerate(render_test_cases):
        resolved = {
            "slug": "test-university",
            "page_type": "university",
            "university_slug": "test-uni",
            "raw": {
                "university_name": "Test University",
                "university_full_name": "Test University Online",
                "hero_description": "A great test university.",
                "established_year": "2020",
                **raw_data
            }
        }
        
        try:
            # This triggers get_transformer which normalizes under the hood
            html = render_resolved(resolved)
            
            # Check if string "NA NAAC" or literal "NA" under NAAC Grade shows in the rendered HTML
            naac_grade_val = raw_data["naac_grade"]
            print(f"Test case with naac_grade={repr(naac_grade_val)}:")
            
            # Since NA, N/A, - are normalized to None, they should not appear in the HTML
            # Check for bad patterns:
            has_placeholder_text = False
            for bad in ["NA NAAC Accredited", "NA Accredited", "N/A Accredited", " - Accredited"]:
                if bad in html:
                    print(f"  ✗ Found placeholder text: {bad}")
                    has_placeholder_text = True
            
            # If naac_grade is normalized to None, then no "NAAC" grade stats/elements should render
            # E.g. "NAAC Grade" stat block is wrapped in `{% if naac_grade %}`
            if naac_grade_val in ("NA", "N/A", "-", None):
                if "NAAC Grade" in html:
                    print("  ✗ 'NAAC Grade' stat block is still rendered in HTML!")
                else:
                    print("  ✓ 'NAAC Grade' stat block is hidden correctly.")
            else:
                if "NAAC Grade" in html:
                    print(f"  ✓ 'NAAC Grade' stats are visible for {naac_grade_val}.")
                else:
                    print(f"  ✗ 'NAAC Grade' is missing even for valid {naac_grade_val}!")
                    
        except Exception as e:
            print(f"  ✗ Error rendering: {str(e)}")
            all_passed = False

    if all_passed:
        print("\nAll normalization audits passed successfully!")
    else:
        print("\nSome audits failed.")

if __name__ == "__main__":
    test_normalization()
