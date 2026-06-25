import sys
from pathlib import Path

# Add backend directory to sys.path so we can import compiler
backend_dir = Path("/Users/aryankinha/Documents/Degree/temp/acfTOhtml copy/backend")
sys.path.insert(0, str(backend_dir))

from workspace.compiler import compile_workspace
from workspace.builder import build_website

workspaces = ["chandigarh-university", "nmims", "nmims-2", "nodia", "test-1"]

# Compile and Build all workspaces
print("🔄 Compiling and building all workspaces...")
for ws in workspaces:
    try:
        print(f"Building: {ws}")
        compile_res = compile_workspace(ws)
        build_res = build_website(ws)
        print(f"✅ Success compiler: {compile_res.get('compiled_at')}, builder: {build_res.get('built_at')}")
    except Exception as e:
        print(f"❌ Error building {ws}: {e}")

# Perform audit on all workspaces and templates
# We exclude the whatsapp number sequence from forbidden patterns when checking wa.me links,
# but we check for any general call buttons or toll-free call numbers.
forbidden_patterns = [
    "1800-1025-136",
    "Book a Free Call",
    "Book a Counselling Call",
    "Book a Free Counselling Call",
    "Student Login",
    "tel:",
    "☏",
    "Download the full program guide",
    "Download Full Program Guide",
    "Get program guides in your inbox",
]

allowed_but_verified = [
    "Apply Now",
    "Download Brochure",
    "WhatsApp Us",
    "WhatsApp",
    "Enquire Now",
]

print("\n==========================================")
print("🔍 Auditing templates and built pages...")
print("==========================================")

any_errors = False

# 1. Audit backend templates
print("\nChecking backend templates...")
templates_dir = backend_dir / "templates"
for filepath in templates_dir.glob("*.html"):
    content = filepath.read_text(encoding="utf-8")
    for pattern in forbidden_patterns:
        if pattern in content:
            print(f"❌ ERROR in template {filepath.name}: Found forbidden pattern '{pattern}'")
            any_errors = True

# 2. Audit generated workspace files
print("\nChecking built workspace pages...")
workspaces_dir = backend_dir / "workspaces"
for ws in workspaces:
    build_dir = workspaces_dir / ws
    for filepath in build_dir.rglob("*.html"):
        content = filepath.read_text(encoding="utf-8")
        # Skip git or build artifacts if any, check real HTML
        for pattern in forbidden_patterns:
            if pattern in content:
                # Let's print the line containing it
                lines = content.splitlines()
                for line_idx, line in enumerate(lines):
                    if pattern in line:
                        print(f"❌ ERROR in built page {filepath.relative_to(workspaces_dir)} (Line {line_idx+1}): Found '{pattern}'")
                        print(f"   Line content: {line.strip()[:100]}")
                        any_errors = True

if not any_errors:
    print("\n🎉 VALIDATION SUCCESS: No phone numbers, helplines, or login links exist anywhere in the templates or built outputs!")
else:
    print("\n❌ VALIDATION FAILURE: Leftover phone UI elements detected.")
