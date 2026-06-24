import sys
import os
import re
import json
import base64
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path("/Users/aryankinha/Documents/Degree/temp/acfTOhtml copy/backend")
sys.path.insert(0, str(backend_dir))

from workspace.compiler import compile_workspace
from workspace.builder import build_website

ENV_PATH = backend_dir / ".env"

def read_env_val(key):
    if not ENV_PATH.exists():
        return None
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    return None

def write_env_val(key, val):
    lines = []
    found = False
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={val}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{key}={val}\n")
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

def run_compile_and_build(workspace_slug="test-1"):
    # Clear os.environ cache for the key to force reload
    if "LEAD_BASE_URL" in os.environ:
        del os.environ["LEAD_BASE_URL"]
    
    # Reload env using load_env logic in main / engine
    from renderer.engine import load_env
    load_env()
    
    print(f"🔄 LEAD_BASE_URL in env: {os.environ.get('LEAD_BASE_URL')}")
    print(f"🔧 Compiling {workspace_slug}...")
    compile_workspace(workspace_slug)
    print(f"🔧 Building {workspace_slug}...")
    build_website(workspace_slug)

def verify_lead_urls(expected_base, workspace_slug="test-1"):
    build_dir = backend_dir / "workspaces" / workspace_slug / "build"
    print(f"🕵️ Auditing HTML files in {build_dir}...")
    
    html_files = list(build_dir.rglob("*.html"))
    if not html_files:
        raise ValueError(f"No HTML files found in {build_dir}")
        
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        relative_path = html_file.relative_to(build_dir)
        
        is_course = False
        is_spec = False
        course_slug = None
        spec_slug = None
        
        # Check course / spec by directory name or path structure
        parts = relative_path.parts
        if len(parts) > 1:
            dir_name = parts[0]
            if dir_name not in ("assets", "blog", "programs", "specializations"):
                if "management" in dir_name or "marketing" in dir_name or "finance" in dir_name or "analytics" in dir_name:
                    is_spec = True
                    spec_slug = dir_name
                    # Parent course slug for test-1
                    parent_course_slug = "test-1-online-mba"
                else:
                    is_course = True
                    course_slug = dir_name

        # Match new lead URL scheme: expected_base/form?d=ENCODED_PAYLOAD
        # Match pattern for href
        links = re.findall(rf'href=["\']({re.escape(expected_base)}/form\?[^"\']+)["\']', content)
        
        if not links:
            if relative_path.name in ("index.html", "programs/index.html", "specializations/index.html", "blog/index.html") or is_course or is_spec:
                print(f"⚠️ Warning: No lead form links found in {relative_path}")
            continue
            
        print(f"📄 Checking {relative_path} ({len(links)} links found)...")
        for link in links:
            # Check for legacy query parameter names (should not exist in the URL string)
            for legacy_param in ("uni=", "program=", "specialization=", "source="):
                if legacy_param in link:
                    raise ValueError(f"Legacy parameter '{legacy_param}' found in URL: {link} in file {relative_path}")
            
            # Extract 'd' parameter
            match_d = re.search(r"[?&]d=([a-zA-Z0-9_-]+)", link)
            if not match_d:
                raise ValueError(f"Missing or invalid encoded payload 'd' parameter in link: {link} in file {relative_path}")
            
            encoded_payload = match_d.group(1)
            
            # Decode payload
            try:
                # Add padding if needed
                padding_needed = len(encoded_payload) % 4
                if padding_needed:
                    encoded_payload += '=' * (4 - padding_needed)
                decoded_bytes = base64.urlsafe_b64decode(encoded_payload)
                payload = json.loads(decoded_bytes.decode('utf-8'))
            except Exception as e:
                raise ValueError(f"Failed to base64 decode or parse JSON from parameter d='{encoded_payload}' in link: {link}. Error: {e}")
            
            # Print parsed payload sample for verification
            # print(f"   Parsed payload: {payload}")
            
            # 1. Assert core parameters
            if payload.get("uni") != workspace_slug:
                raise ValueError(f"Mismatch uni parameter in payload: {payload} in link {link} (expected {workspace_slug})")
                
            source = payload.get("source")
            if source not in ("apply", "brochure", "enquiry", "fees", "counselling"):
                raise ValueError(f"Invalid source parameter in payload: {payload} in link {link}")
                
            # 2. Check course-specific details
            if is_course:
                if "program" not in payload:
                    raise ValueError(f"Missing program in payload for course page {relative_path}: {payload}")
                if payload.get("program") != course_slug:
                    raise ValueError(f"Mismatch program in payload for course page {relative_path}: {payload} (expected {course_slug})")
                if "specialization" in payload:
                    raise ValueError(f"Unexpected specialization in course payload {relative_path}: {payload}")
                    
            # 3. Check specialization-specific details
            elif is_spec:
                if "program" not in payload:
                    raise ValueError(f"Missing program in payload for spec page {relative_path}: {payload}")
                if "specialization" not in payload:
                    raise ValueError(f"Missing specialization in payload for spec page {relative_path}: {payload}")
                if payload.get("specialization") != spec_slug:
                    raise ValueError(f"Mismatch specialization in payload for spec page {relative_path}: {payload} (expected {spec_slug})")
                if payload.get("program") != parent_course_slug:
                    raise ValueError(f"Mismatch parent program in payload for spec page {relative_path}: {payload} (expected {parent_course_slug})")
                    
    print("✅ All Base64 JSON checks passed successfully for this base URL!")

def main():
    original_base = read_env_val("LEAD_BASE_URL")
    print(f"Original LEAD_BASE_URL: {original_base}")
    
    try:
        # Test Case 1: Default http://localhost:3001
        print("\n--- Test Case 1: Default http://localhost:3001 ---")
        write_env_val("LEAD_BASE_URL", "http://localhost:3001")
        run_compile_and_build()
        verify_lead_urls("http://localhost:3001")
        
        # Print a sample payload from the build dir to verify manually
        build_dir = backend_dir / "workspaces" / "test-1" / "build"
        for html_file in build_dir.rglob("*.html"):
            content = html_file.read_text(encoding="utf-8")
            match_d = re.search(r"form\?d=([a-zA-Z0-9_-]+)", content)
            if match_d:
                encoded = match_d.group(1)
                padding_needed = len(encoded) % 4
                if padding_needed:
                    encoded += '=' * (4 - padding_needed)
                decoded = base64.urlsafe_b64decode(encoded).decode('utf-8')
                print(f"\n💡 [Verification Sample] Decoded payload from {html_file.name}:")
                print(f"   Raw: {match_d.group(0)}")
                print(f"   Decoded: {decoded}")
                break
        
        # Test Case 2: Custom domain prefix https://test-leads.custom.org
        print("\n--- Test Case 2: Custom domain prefix https://test-leads.custom.org ---")
        write_env_val("LEAD_BASE_URL", "https://test-leads.custom.org")
        run_compile_and_build()
        verify_lead_urls("https://test-leads.custom.org")
        
    finally:
        # Restore original value
        if original_base:
            print(f"\nRestoring original LEAD_BASE_URL to: {original_base}")
            write_env_val("LEAD_BASE_URL", original_base)
        else:
            print("\nRestoring default LEAD_BASE_URL: http://localhost:3001")
            write_env_val("LEAD_BASE_URL", "http://localhost:3001")
        run_compile_and_build()

if __name__ == "__main__":
    main()
