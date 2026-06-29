import os
import json
from pathlib import Path
import sys

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workspace.manager import WORKSPACES_ROOT
from workspace.knowledge import (
    load_or_create_knowledge,
    save_knowledge,
    update_university_knowledge
)

def run_migration():
    print("🔄 Running University Knowledge Migration...")
    
    if not WORKSPACES_ROOT.exists():
        print(f"❌ Workspaces root not found at: {WORKSPACES_ROOT}")
        return
        
    workspaces = [d for d in WORKSPACES_ROOT.iterdir() if d.is_dir()]
    print(f"Found {len(workspaces)} workspace directories.")
    
    for ws_dir in workspaces:
        uni_slug = ws_dir.name
        print(f"\n📂 Migrating workspace: {uni_slug}")
        
        # Load or create base template
        knowledge = load_or_create_knowledge(uni_slug)
        
        # 1. Parse metadata.json
        meta_path = ws_dir / "metadata.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                
                # Identity
                knowledge["identity"]["university_name"] = meta.get("university_name") or knowledge["identity"]["university_name"] or uni_slug.upper()
                knowledge["identity"]["university_full_name"] = meta.get("university_full_name") or knowledge["identity"]["university_full_name"] or meta.get("university_name")
                
                # Branding assets
                branding = meta.get("branding") or {}
                knowledge["assets"]["logo"] = branding.get("logo") or knowledge["assets"]["logo"]
                knowledge["assets"]["favicon"] = branding.get("favicon") or knowledge["assets"]["favicon"]
                
                # Contact details
                site_config = meta.get("site") or {}
                knowledge["contact"]["email"] = site_config.get("email") or knowledge["contact"]["email"]
                knowledge["contact"]["address"] = site_config.get("address") or knowledge["contact"]["address"]
                knowledge["contact"]["phone"] = site_config.get("phone") or knowledge["contact"]["phone"]
                knowledge["contact"]["whatsapp"] = site_config.get("whatsapp") or knowledge["contact"]["whatsapp"]
                
                print("  ✓ Imported metadata.json settings")
            except Exception as e:
                print(f"  ⚠️ Error parsing metadata.json: {e}")
                
        save_knowledge(uni_slug, knowledge)

        # 2. Extract from University/source.json
        uni_page_path = ws_dir / "University" / "source.json"
        if uni_page_path.exists():
            try:
                uni_page_data = json.loads(uni_page_path.read_text(encoding="utf-8"))
                payload = uni_page_data.get("data") or {}
                update_university_knowledge(uni_slug, payload, "university")
                print("  ✓ Extracted University page source.json")
            except Exception as e:
                print(f"  ⚠️ Error extracting from University page: {e}")

        # 3. Extract from Courses/*/source.json
        courses_dir = ws_dir / "Courses"
        if courses_dir.exists():
            for c_dir in courses_dir.iterdir():
                if not c_dir.is_dir():
                    continue
                c_source = c_dir / "source.json"
                if c_source.exists():
                    try:
                        c_data = json.loads(c_source.read_text(encoding="utf-8"))
                        payload = c_data.get("data") or {}
                        update_university_knowledge(uni_slug, payload, "course")
                        
                        # Specializations inside Courses
                        specs_dir = c_dir / "Specializations"
                        if specs_dir.exists():
                            for s_dir in specs_dir.iterdir():
                                if not s_dir.is_dir():
                                    continue
                                s_source = s_dir / "source.json"
                                if s_source.exists():
                                    try:
                                        s_data = json.loads(s_source.read_text(encoding="utf-8"))
                                        s_payload = s_data.get("data") or {}
                                        update_university_knowledge(uni_slug, s_payload, "specialization")
                                    except Exception as e:
                                        print(f"  ⚠️ Error parsing specialization source: {e}")
                    except Exception as e:
                        print(f"  ⚠️ Error parsing course source: {e}")

        # 4. Extract from Blogs/*/source.json
        blogs_dir = ws_dir / "Blogs"
        if blogs_dir.exists():
            for b_dir in blogs_dir.iterdir():
                if not b_dir.is_dir():
                    continue
                b_source = b_dir / "source.json"
                if b_source.exists():
                    try:
                        b_data = json.loads(b_source.read_text(encoding="utf-8"))
                        payload = b_data.get("data") or {}
                        update_university_knowledge(uni_slug, payload, "blog")
                    except Exception as e:
                        print(f"  ⚠️ Error parsing blog source: {e}")

        # Verification printout
        k = load_or_create_knowledge(uni_slug)
        print(f"  → Finalized knowledge. Name: '{k['identity']['university_name']}', Conflicts count: {len(k.get('conflicts', []))}")
        
    print("\n🎉 MIGRATION COMPLETE!")

if __name__ == "__main__":
    run_migration()
