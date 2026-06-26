from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, Response
from core.router import get_transformer
from renderer.engine import render_resolved
from workspace.manager import (
    save_page, list_workspaces, ensure_metadata, init_system_pages, WORKSPACES_ROOT
)
from workspace.compiler import compile_workspace, get_workspace_tree
from workspace.builder import build_website, get_build_status, zip_build
import json
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Optional
# Load environment variables manually from .env if present
def load_env():
    import os
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def _heuristic_detect_parent(spec_slug: str, university_slug: str, candidate_courses: list[str]) -> str | None:
    """
    Given a specialization slug and a list of known course slugs in the workspace,
    return the best-matching parent course slug using token overlap scoring.

    Strategy:
    1. Strip the university_slug prefix from the spec slug to get the "bare" spec tokens.
    2. For each candidate course, strip the university_slug prefix → "bare" course tokens.
    3. Score = number of shared tokens (longest prefix match weighted higher).
    4. Return the course with the highest score. If tied or no candidates, return None.
    """
    if not candidate_courses:
        return None

    import re

    def tokenize(slug: str, prefix: str) -> list[str]:
        bare = slug
        if bare.startswith(prefix + "-"):
            bare = bare[len(prefix) + 1:]
        return [t for t in re.split(r"[-_]+", bare) if t]

    spec_tokens = tokenize(spec_slug, university_slug)
    if not spec_tokens:
        return None

    best_course = None
    best_score = -1

    for course_slug in candidate_courses:
        course_tokens = tokenize(course_slug, university_slug)
        # Count overlapping tokens (ordered prefix match counts double)
        shared = 0
        for i, ct in enumerate(course_tokens):
            if ct in spec_tokens:
                shared += 2 if i < len(spec_tokens) and spec_tokens[i] == ct else 1

        if shared > best_score:
            best_score = shared
            best_course = course_slug

    # Only accept the match if there is at least 1 shared token
    return best_course if best_score > 0 else None


def _get_workspace_course_slugs(university_slug: str) -> list[str]:
    """Return the list of course slugs already saved in the workspace (for heuristic detection)."""
    courses_dir = WORKSPACES_ROOT / university_slug / "Courses"
    if not courses_dir.exists():
        return []
    slugs = []
    for p in courses_dir.iterdir():
        if p.is_dir():
            src = p / "source.json"
            if src.exists():
                try:
                    import json as _json
                    record = _json.loads(src.read_text(encoding="utf-8"))
                    if record.get("page_type") == "course":
                        slugs.append(record.get("slug") or p.name)
                except Exception:
                    slugs.append(p.name)
    return slugs


def extract_metadata_from_json(payload: dict) -> tuple[str, str, str, str | None, dict]:
    # Check if this is a wrapped record (has a "payload" or "data" field)
    if "payload" in payload and isinstance(payload["payload"], dict):
        data = payload["payload"].copy()
        slug = payload.get("slug")
        page_type = payload.get("page_type")
        university_slug = payload.get("university_slug")
        parent_slug = payload.get("parent_slug")
    elif "data" in payload and isinstance(payload["data"], dict):
        data = payload["data"].copy()
        slug = payload.get("slug")
        page_type = payload.get("page_type")
        university_slug = payload.get("university_slug")
        parent_slug = payload.get("parent_slug")
    else:
        data = payload.copy()
        slug = data.pop("slug", None)
        page_type = data.pop("page_type", None)
        university_slug = data.pop("university_slug", None)
        parent_slug = data.pop("parent_slug", None)

    # Pop metadata keys from data if they exist inside the content block
    for k in ["slug", "page_type", "university_slug", "parent_slug"]:
        data.pop(k, None)

    # If page_type is not provided, derive it
    if not page_type:
        if "spec_name" in data:
            page_type = "specialization"
        elif "program_name" in data:
            page_type = "course"
        elif  "university_full_name" in data or "established_year" in data:
            page_type = "university"
        elif "posts" in data:
            page_type = "blog"
        else:
            page_type = "course" # default fallback

    # If university_slug is not provided, derive it
    if not university_slug:
        uni_name = data.get("university_name") or data.get("university_full_name") or "unknown"
        university_slug = uni_name.lower().replace(" online", "").replace("'", "").replace(" ", "-").strip()

    # If slug is not provided, derive it
    if not slug:
        name = data.get("spec_name") or data.get("program_name") or data.get("university_name") or data.get("hero_title") or data.get("title")
        if name:
            import re
            clean_name = name.lower().replace(" ", "-").replace("_", "-")
            clean_name = re.sub(r"[^a-z0-9\-]", "", clean_name)
            clean_name = re.sub(r"-+", "-", clean_name)
            slug = clean_name.strip("-")
            # If university prefix is missing for courses/specializations, prepend it
            if page_type in ("course", "specialization") and not slug.startswith(university_slug):
                slug = f"{university_slug}-{slug}"
        else:
            slug = "untitled"

    # Resolve parent_slug for specializations — NO hardcoded fallback
    if page_type == "specialization" and not parent_slug:
        # 1. Check if it was embedded in the data block
        parent_slug = data.get("parent_slug")

        # 2. If still missing, use heuristic detection against workspace course slugs
        if not parent_slug and university_slug and slug:
            known_courses = _get_workspace_course_slugs(university_slug)
            parent_slug = _heuristic_detect_parent(slug, university_slug, known_courses)
            # parent_slug may still be None — that is valid and expected
            # The frontend will prompt the user to assign it manually

    # Normalize specialization name fields in data if page_type is specialization
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
                    # Combine all title variations to ensure we strip both "EMBA" and "Executive MBA"
                    names = [c_raw.get("program_name"), c_raw.get("course_name"), c_raw.get("title")]
                    parent_program_name = " ".join(filter(None, names))
            except Exception:
                pass
        
        if not parent_program_name:
            parent_program_name = parent_slug.replace("-", " ").title() if parent_slug else ""
            
        from core.utils import normalize_specialization_name
        for field in ["spec_name", "specialization_name", "title", "course_name", "hero_title", "hero_heading"]:
            if field in data and isinstance(data[field], str) and data[field].strip():
                data[field] = normalize_specialization_name(data[field], parent_program_name, uni_name)
                
        if "hero" in data and isinstance(data["hero"], dict):
            if "title" in data["hero"] and isinstance(data["hero"]["title"], str) and data["hero"]["title"].strip():
                data["hero"]["title"] = normalize_specialization_name(data["hero"]["title"], parent_program_name, uni_name)


    return slug, page_type, university_slug, parent_slug, data


def save_base64_image(base64_str: str, dest_dir: Path, filename_prefix: str) -> str | None:
    import base64
    import re
    if not base64_str:
        return None
    if base64_str.startswith("/assets/images/") or base64_str.startswith("http://") or base64_str.startswith("https://"):
        return base64_str
    match = re.match(r"^data:image/(\w+);base64,(.+)$", base64_str)
    if not match:
        return base64_str
    ext = match.group(1)
    if ext == "jpeg":
        ext = "jpg"
    data_b64 = match.group(2)
    try:
        data = base64.b64decode(data_b64)
    except Exception:
        return base64_str
    filename = f"{filename_prefix}.{ext}"
    dest_path = dest_dir / filename
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(data)
    return f"/assets/images/{filename}"


def image_prefix_for_slot(page_type: str, slug: str, slot: str) -> str:
    if page_type == "university":
        return "university-hero" if slot == "hero_image_url" else f"university-{slot}"
    if page_type == "course":
        if slot == "hero_image_url":
            return f"{slug}-hero"
        if slot == "certificate_image_url":
            return f"{slug}-certificate"
    if page_type == "specialization":
        return f"{slug}-hero" if slot == "hero_image_url" else f"{slug}-{slot}"
    if page_type == "blog":
        return f"blog-{slug}-hero" if slot in ("hero_image_url", "featured_image_url") else f"blog-{slug}-{slot}"
    return f"{slug}-{slot}"

@app.get("/assets/images/{filename}")
async def get_asset_image(filename: str):
    from fastapi.responses import FileResponse
    for p in WORKSPACES_ROOT.glob(f"*/Assets/images/{filename}"):
        if p.exists():
            ext = p.suffix.lower()
            media_type = "image/jpeg"
            if ext == ".png":
                media_type = "image/png"
            elif ext == ".webp":
                media_type = "image/webp"
            elif ext == ".gif":
                media_type = "image/gif"
            elif ext == ".svg":
                media_type = "image/svg+xml"
            elif ext in (".ico", ".icon"):
                media_type = "image/x-icon"
            return FileResponse(p, media_type=media_type)
    raise HTTPException(status_code=404, detail="Image not found")

@app.get("/assets/{path:path}")
async def get_build_asset(path: str):
    from fastapi.responses import FileResponse
    for p in WORKSPACES_ROOT.glob(f"*/build/assets/{path}"):
        if p.exists() and p.is_file():
            ext = p.suffix.lower()
            media_type = "application/octet-stream"
            if ext == ".js":
                media_type = "application/javascript"
            elif ext == ".css":
                media_type = "text/css"
            elif ext == ".png":
                media_type = "image/png"
            elif ext in (".jpg", ".jpeg"):
                media_type = "image/jpeg"
            elif ext == ".webp":
                media_type = "image/webp"
            elif ext == ".gif":
                media_type = "image/gif"
            elif ext == ".svg":
                media_type = "image/svg+xml"
            elif ext == ".pdf":
                media_type = "application/pdf"
            return FileResponse(p, media_type=media_type)
    
    if path == "support.js":
        return await get_support_js()
        
    raise HTTPException(status_code=404, detail="Asset not found")

@app.get("/support.js")
async def get_support_js():
    from fastapi.responses import FileResponse
    base_dir = Path(__file__).resolve().parent
    search_paths = [
        base_dir / "support.js",
        base_dir.parent / "support.js",
        base_dir.parent / "frontend" / "public" / "support.js",
    ]
    for p in search_paths:
        if p.exists():
            return FileResponse(p, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="support.js not found")

class SaveTempRequest(BaseModel):
    data: dict[str, Any]

@app.post("/save-temp-json")
async def save_temp_json(req: SaveTempRequest):
    try:
        base_dir = Path(__file__).resolve().parent
        temp_file = base_dir / "generated" / "temp_debug.json"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(req.data, f, indent=2, ensure_ascii=False)
        return {"status": "saved", "path": str(temp_file)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

class IngestRequest(BaseModel):
    acf_data: dict[str, Any]

@app.post("/ingest-acf")
async def ingest_acf(req: IngestRequest):
    try:
        slug, page_type, university_slug, parent_slug, acf_data = extract_metadata_from_json(req.acf_data)
        resolved = {
            "slug": slug,
            "page_type": page_type,
            "university_slug": university_slug,
            "parent_slug": parent_slug,
            "raw": acf_data
        }
        transformer = get_transformer(resolved)
        ctx = transformer.transform()
        import json
        ctx["ctx_json"] = json.dumps(ctx, default=str)
        return {
            "status": "ok",
            "context": ctx,
            "page_type": page_type,
            "slug": slug,
            "university_slug": university_slug,
            "parent_slug": parent_slug,
            "acf_data": acf_data
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Helper to save draft preview JSON
def save_draft_data(university_slug: str, page_type: str, slug: str, parent_slug: str | None, data: dict, images: dict):
    base_dir = Path(__file__).resolve().parent
    draft_dir = base_dir / "generated" / "drafts" / university_slug / page_type
    draft_dir.mkdir(parents=True, exist_ok=True)
    draft_file = draft_dir / f"{slug}.json"
    draft_record = {
        "university_slug": university_slug,
        "page_type": page_type,
        "slug": slug,
        "parent_slug": parent_slug,
        "data": data,
        "images": images
    }
    draft_file.write_text(json.dumps(draft_record, indent=2, ensure_ascii=False), encoding="utf-8")

# Helper to load draft preview JSON
def load_draft_data(university_slug: str, page_type: str, slug: str) -> dict | None:
    base_dir = Path(__file__).resolve().parent
    draft_file = base_dir / "generated" / "drafts" / university_slug / page_type / f"{slug}.json"
    if draft_file.exists():
        try:
            return json.loads(draft_file.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None

class RenderRequest(BaseModel):
    acf_data: dict[str, Any]
    images: dict[str, str] = {}

@app.post("/preview-html", response_class=HTMLResponse)
async def preview_html(req: RenderRequest):
    """Render dynamically without database persistence — return HTML as text (for iframe preview)."""
    try:
        slug, page_type, university_slug, parent_slug, acf_data = extract_metadata_from_json(req.acf_data)
        
        # Save draft data for GET preview-file endpoint to consume
        save_draft_data(university_slug, page_type, slug, parent_slug, acf_data, req.images)
        
        merged = {**acf_data, **req.images}
        
        # Load baseline workspace index
        from workspace.compiler import _build_index, _enrich_resolved
        index = _build_index(university_slug)
        
        # Construct draft record and inject it into the temporary index
        draft_record = {
            "university_slug": university_slug,
            "page_type": page_type,
            "slug": slug,
            "parent_slug": parent_slug,
            "data": merged
        }
        if page_type in index:
            index[page_type][slug] = draft_record
            
        # Enrich raw draft data with index-based workspace context
        enriched_record = _enrich_resolved(draft_record, index)
        
        resolved = {
            "slug": slug,
            "page_type": page_type,
            "university_slug": university_slug,
            "parent_slug": parent_slug,
            "raw": enriched_record["raw"]
        }
        standalone = page_type in ("course", "specialization", "blog")
        html = render_resolved(resolved, standalone=standalone)
        return HTMLResponse(content=html)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/preview-file", response_class=HTMLResponse)
async def preview_file(university_slug: str, page_type: str, slug: str):
    """Serve dynamic preview from GET query params. Uses draft cache if available, else saved workspace data."""
    try:
        # Load baseline workspace index
        from workspace.compiler import _build_index, _enrich_resolved
        index = _build_index(university_slug)

        draft = load_draft_data(university_slug, page_type, slug)
        if draft:
            parent_slug = draft.get("parent_slug")
            merged = {**(draft.get("data") or {}), **(draft.get("images") or {})}
        else:
            # Fallback to saved data in index if draft does not exist
            if page_type in index and slug in index[page_type]:
                record = index[page_type][slug]
                parent_slug = record.get("parent_slug")
                merged = record.get("data") or {}
            else:
                raise HTTPException(status_code=404, detail="Preview data not found")

        # Construct draft record and inject it into the temporary index
        draft_record = {
            "university_slug": university_slug,
            "page_type": page_type,
            "slug": slug,
            "parent_slug": parent_slug,
            "data": merged
        }
        if page_type in index:
            index[page_type][slug] = draft_record
            
        # Enrich raw draft data with index-based workspace context
        enriched_record = _enrich_resolved(draft_record, index)
        
        resolved = {
            "slug": slug,
            "page_type": page_type,
            "university_slug": university_slug,
            "parent_slug": parent_slug,
            "raw": enriched_record["raw"]
        }
        standalone = page_type in ("course", "specialization", "blog")
        html = render_resolved(resolved, standalone=standalone)
        return HTMLResponse(content=html)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/render-html")
async def render_html(req: RenderRequest):
    """Render dynamically, save file to generated/{page_type}/{slug}.html — return HTML as downloadable attachment."""
    try:
        slug, page_type, university_slug, parent_slug, acf_data = extract_metadata_from_json(req.acf_data)
        merged = {**acf_data, **req.images}
        
        # Load baseline workspace index
        from workspace.compiler import _build_index, _enrich_resolved
        index = _build_index(university_slug)
        
        # Construct draft record and inject it into the temporary index
        draft_record = {
            "university_slug": university_slug,
            "page_type": page_type,
            "slug": slug,
            "parent_slug": parent_slug,
            "data": merged
        }
        if page_type in index:
            index[page_type][slug] = draft_record
            
        # Enrich raw draft data with index-based workspace context
        enriched_record = _enrich_resolved(draft_record, index)
        
        resolved = {
            "slug": slug,
            "page_type": page_type,
            "university_slug": university_slug,
            "parent_slug": parent_slug,
            "raw": enriched_record["raw"]
        }
        standalone = page_type in ("course", "specialization", "blog")
        html = render_resolved(resolved, standalone=standalone)
        
        # Save compiled HTML to backend/generated/{page_type}/{slug}.dc.html
        base_dir = Path(__file__).resolve().parent
        generated_dir = base_dir / "generated" / page_type
        generated_dir.mkdir(parents=True, exist_ok=True)
        (generated_dir / f"{slug}.dc.html").write_text(html, encoding="utf-8")
        
        return Response(
            content=html,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={slug}.dc.html"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

def forward_to_micro_pipeline(file_bytes: bytes, filename: str, page_type: str | None = None) -> dict:
    import os
    import urllib.request
    import urllib.error
    import uuid

    micro_app_url = os.environ.get("MICRO_APP_URL")
    if micro_app_url is None:
        raise HTTPException(
            status_code=500,
            detail="Environment variable 'MICRO_APP_URL' is not set."
        )

    if not micro_app_url.strip():
        raise HTTPException(
            status_code=500,
            detail="Environment variable 'MICRO_APP_URL' is empty."
        )
    
    url = micro_app_url.strip()
    if url.endswith("/"):
        url = url[:-1]

    # Determine the endpoint (match the rules from frontend api.js)
    if url.endswith("/upload") or url.endswith("/parse-docx"):
        endpoint = url
    else:
        endpoint = f"{url}/upload"

    boundary = uuid.uuid4().hex
    body = []

    # File field
    body.append(f"--{boundary}".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode("utf-8"))
    body.append(b"Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    body.append(b"")
    body.append(file_bytes)

    # page_type field
    if page_type:
        body.append(f"--{boundary}".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="page_type"'.encode("utf-8"))
        body.append(b"")
        body.append(page_type.encode("utf-8"))

    body.append(f"--{boundary}--".encode("utf-8"))
    body.append(b"")

    body_data = b"\r\n".join(body)

    req = urllib.request.Request(endpoint, data=body_data)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Content-Length", str(len(body_data)))

    try:
        with urllib.request.urlopen(req, timeout=180) as res:
            response_data = res.read().decode("utf-8")
            return json.loads(response_data)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            detail = error_json.get("detail", error_json.get("error", str(e)))
        except Exception:
            detail = error_body or str(e)
        raise HTTPException(status_code=e.code, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to communicate with micro-pipeline: {str(e)}")

@app.post("/parse-docx")
async def parse_docx_endpoint(
    file: UploadFile = File(...),
    page_type: str | None = Form(default=None)
):
    """Parse a .docx document into ACF JSON fields. If it's a blog page type, parse using generic parser; otherwise use micro-pipeline."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported.")

    import tempfile
    import os
    from ingestion.parser import parse_docx
    from ingestion.extractor import blocks_to_html
    from pathlib import Path

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Write to a temp file to parse/inspect headings and content
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        # Parse the docx to get blocks
        blocks = parse_docx(tmp_path)

        # Determine/Detect page type
        detected_type = page_type
        if not detected_type:
            filename_lower = file.filename.lower()
            headings = [b["text"].lower() for b in blocks if b["type"] in ("h1", "h2", "h3")]
            paragraphs = [b["text"].lower() for b in blocks if b["type"] in ("paragraph", "bold_para", "list_item")]
            
            scores = {"university": 0, "course": 0, "specialization": 0, "blog": 0}
            
            # --- Specialization Specific Keywords ---
            spec_keywords = [
                "marketing", "finance", "human resource", "hr-", "hr ", "human-resource",
                "operations", "banking", "insurance", "retail", "supply chain", "logistics", 
                "analytics", "data science", "information technology", "digital marketing", 
                "business management", "financial management", "applied finance",
                "leadership", "strategy", "operations", "supply chain", "management",
                "specialisation", "specialization"
            ]
            
            # --- 1. Filename Indicators ---
            if "university" in filename_lower or "uni_page" in filename_lower:
                scores["university"] += 5
            if any(w in filename_lower for w in ["course", "program", "mba", "mca", "bba", "bca"]):
                scores["course"] += 3
            if any(w in filename_lower for w in ["specialization", "spec"]) or any(w in filename_lower for w in spec_keywords):
                scores["specialization"] += 4
            if " in " in filename_lower and any(w in filename_lower for w in ["mba", "bba", "mca", "bca"]):
                scores["specialization"] += 5
            if any(w in filename_lower for w in ["blog", "post", "article", "guide", "how-to", "read", "career-path", "salary-after"]):
                scores["blog"] += 5
                
            # --- 2. Heading Indicators ---
            for h in headings:
                if any(w in h for w in ["about the university", "why choose", "accreditation", "facts", "ugc approved", "rankings"]):
                    scores["university"] += 3
                if any(w in h for w in ["about the course", "about the program", "course highlights", "specializations offered", "syllabus", "fee structure", "fee plans", "eligibility"]):
                    if "specializations offered" in h or "list of specializations" in h or "available specializations" in h:
                        scores["course"] += 3
                    else:
                        scores["course"] += 2
                if any(w in h for w in ["about the specialization", "specialization highlights", "job roles", "job profiles", "career prospects", "curriculum electives"]):
                    scores["specialization"] += 3
                if any(w in h for w in spec_keywords):
                    scores["specialization"] += 2
                if any(w in h for w in ["blog", "post", "article", "author", "published", "conclusion", "verdict", "key takeaway"]):
                    scores["blog"] += 2

            # --- 3. Content Paragraph / Metadata Indicators ---
            blog_metadata_words = ["author", "read time", "min read", "published on", "written by", "date:"]
            for p in paragraphs[:15]:
                if any(w in p for w in blog_metadata_words):
                    scores["blog"] += 4
                if "author:" in p or "by aditi" in p or "read time:" in p:
                    scores["blog"] += 5
                    
            # Check other content indicators
            all_text = " ".join(paragraphs)
            if any(w in all_text for w in ["established in", "vice chancellor", "accreditations", "naac grade"]):
                scores["university"] += 2
            if any(w in all_text for w in ["semester 1", "semester 2", "syllabus", "fee details", "program duration"]):
                scores["course"] += 2
            if any(w in all_text for w in ["career paths", "specialization highlights", "job opportunities"]):
                scores["specialization"] += 2
            if any(w in all_text for w in spec_keywords):
                scores["specialization"] += 1

            detected_type = max(scores, key=scores.get)
            
            # If it's a tie at 0, check if we can make a guess based on filename, otherwise fallback to course
            if scores[detected_type] == 0:
                if any(w in filename_lower for w in ["why-", "how-", "top-", "best-", "guide", "salary", "jobs"]):
                    detected_type = "blog"
                else:
                    detected_type = "course"

        # Check if the page type is a blog/generic type
        is_blog_or_generic = detected_type in ("blog", "blog_post", "generic")

        if is_blog_or_generic:
            # Route to the blog/generic parser logic
            import math
            import re
            from datetime import datetime

            # Clean blocks first
            cleaned_blocks = []
            for b in blocks:
                cleaned_block = {"type": b["type"]}
                if "text" in b:
                    cleaned_text = b["text"]
                    cleaned_text = re.sub(r"^Copy of\s+", "", cleaned_text, flags=re.IGNORECASE)
                    cleaned_block["text"] = cleaned_text
                if "rows" in b:
                    cleaned_block["rows"] = b["rows"]
                cleaned_blocks.append(cleaned_block)

            # Find the title (usually the first heading block)
            title = None
            title_index = -1
            for i, b in enumerate(cleaned_blocks):
                if b["type"] in ("h1", "h2", "h3") and "text" in b:
                    title = b["text"]
                    title_index = i
                    break

            if not title:
                title = Path(file.filename).stem
                title = re.sub(r"^Copy of\s+", "", title, flags=re.IGNORECASE)
                title = re.sub(r"^[hH][1-4][_\s:]+", "", title)
                title = title.replace("-", " ").replace("_", " ").title()

            # Find excerpt: usually the first paragraph after the title
            excerpt = ""
            start_search = title_index + 1 if title_index != -1 else 0
            for i in range(start_search, len(cleaned_blocks)):
                b = cleaned_blocks[i]
                if b["type"] in ("paragraph", "bold_para") and "text" in b:
                    excerpt = b["text"]
                    break

            # Filter blocks for content: skip the title heading block to avoid duplicates
            content_blocks = []
            for i, b in enumerate(cleaned_blocks):
                if i == title_index:
                    continue
                # Also skip "Introduction" heading if it appears right after title and is redundant
                if i == title_index + 1 and b["type"] == "h2" and b.get("text", "").lower() == "introduction":
                    continue
                content_blocks.append(b)

            content_html = blocks_to_html(content_blocks)

            # Estimate reading time based on word count
            word_count = 0
            for b in content_blocks:
                if b.get("text"):
                    word_count += len(b["text"].split())
            read_time_mins = max(1, math.ceil(word_count / 200))
            read_time = f"{read_time_mins} min read"

            # Classify category/tag based on keywords in title and filename
            title_lower = title.lower()
            filename_lower = file.filename.lower()
            tag = "Guide"
            if any(w in title_lower or w in filename_lower for w in ["scholarship", "fee", "cost", "financing"]):
                tag = "Finance"
            elif any(w in title_lower or w in filename_lower for w in ["placement", "career", "salary", "jobs", "working", "work"]):
                tag = "Career"
            elif any(w in title_lower or w in filename_lower for w in ["subject", "year", "syllabus", "student"]):
                tag = "Student Life"
            elif any(w in title_lower or w in filename_lower for w in ["admission", "valid", "eligibility", "ignou", "mca"]):
                tag = "Admissions"

            payload = {
                "title": title,
                "excerpt": excerpt,
                "content_html": content_html,
                "tag": tag,
                "author": "Aditi Rao",
                "author_role": "Career Editor",
                "read_time": read_time,
                "date": datetime.now().strftime("%b %d, %Y"),
                "blocks": cleaned_blocks
            }

            result = {
                "filename": file.filename,
                "page_type": detected_type,
                "payload": payload
            }
        else:
            # Route to the micro-pipeline (passing the original file bytes)
            result = forward_to_micro_pipeline(file_bytes, file.filename, detected_type)
            
            # Micro-First Ingestion: Adapt, Validate, and Fallback Merge
            if result and isinstance(result, dict) and "payload" in result:
                payload = result["payload"]
                if isinstance(payload, dict):
                    from ingestion.extractor import extract_acf, classify_fee_plans
                    from ingestion.adapter import adapt_and_validate, merge_micro_and_local
                    
                    # 1. Adapt and Validate raw Micro Parser output
                    adapted_payload, warnings = adapt_and_validate(payload, detected_type)
                    
                    # 2. Run classifier on adapted fee_plans if it is a course
                    if detected_type == "course":
                        micro_fee_plans = adapted_payload.get("fee_plans")
                        if isinstance(micro_fee_plans, list) and micro_fee_plans:
                            classified_plans, detected_specs = classify_fee_plans(micro_fee_plans)
                            adapted_payload["fee_plans"] = classified_plans
                            if detected_specs:
                                existing_specs = adapted_payload.get("detected_specializations") or []
                                for spec in detected_specs:
                                    if spec not in existing_specs:
                                        existing_specs.append(spec)
                                adapted_payload["detected_specializations"] = existing_specs

                    # 3. Local Parser serves ONLY as a fallback/recovery mechanism (fills missing/empty fields)
                    local_acf = extract_acf(blocks, detected_type, {})
                    merged_payload = merge_micro_and_local(adapted_payload, local_acf)

                    # Merge specializations list for courses (since they are arrays of stubs, not atomic overrides)
                    if detected_type == "course":
                        local_specs = local_acf.get("detected_specializations") or []
                        if local_specs:
                            existing_specs = merged_payload.get("detected_specializations") or []
                            for spec in local_specs:
                                if spec not in existing_specs:
                                    existing_specs.append(spec)
                            merged_payload["detected_specializations"] = existing_specs

                    result["payload"] = merged_payload
                    result["validation_warnings"] = warnings

        from core.router import normalize_value
        return normalize_value(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# ──────────────────────────────────────────────────────────────────────────────
# Hybrid Parent Mapping endpoints
# ──────────────────────────────────────────────────────────────────────────────

class DetectParentRequest(BaseModel):
    spec_slug: str
    university_slug: str
    current_parent_slug: Optional[str] = None


@app.post("/detect-parent")
async def detect_parent_endpoint(req: DetectParentRequest):
    """
    Return the heuristic-detected parent course and a list of all available
    course slugs in the workspace so the frontend can offer a dropdown.

    Response:
    {
      "detected_parent_slug": str | null,
      "confidence": "auto" | "heuristic" | "none",
      "available_courses": [ { "slug": str, "name": str } ]
    }
    """
    try:
        known_courses = _get_workspace_course_slugs(req.university_slug)

        # If an explicit parent_slug is already set and it exists in the workspace, trust it
        if req.current_parent_slug and req.current_parent_slug in known_courses:
            confidence = "auto"
            detected = req.current_parent_slug
        else:
            detected = _heuristic_detect_parent(req.spec_slug, req.university_slug, known_courses)
            confidence = "heuristic" if detected else "none"

        # Build human-readable labels from source.json (use program_name or fall back to slug)
        courses_dir = WORKSPACES_ROOT / req.university_slug / "Courses"
        available = []
        for course_slug in known_courses:
            label = course_slug
            src = courses_dir / course_slug / "source.json"
            if src.exists():
                try:
                    rec = json.loads(src.read_text(encoding="utf-8"))
                    name = (rec.get("data") or {}).get("program_name") or course_slug
                    label = name
                except Exception:
                    pass
            available.append({"slug": course_slug, "name": label})

        return {
            "detected_parent_slug": detected,
            "confidence": confidence,
            "available_courses": available,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


class RemapParentRequest(BaseModel):
    university_slug: str
    spec_slug: str
    new_parent_slug: str


@app.post("/remap-parent")
async def remap_parent_endpoint(req: RemapParentRequest):
    """
    Update the parent_slug stored in an existing specialization source.json
    without requiring a full re-upload.  Returns the updated record summary.

    Use-case:
      - Fix historically saved specs that have the wrong parent_slug.
      - User picks a different parent from the dropdown in the Review screen.
    """
    try:
        spec_dir = WORKSPACES_ROOT / req.university_slug / "Specializations" / req.spec_slug
        src_path = spec_dir / "source.json"
        if not src_path.exists():
            raise HTTPException(status_code=404, detail=f"Specialization '{req.spec_slug}' not found in workspace '{req.university_slug}'")

        record = json.loads(src_path.read_text(encoding="utf-8"))
        old_parent = record.get("parent_slug")
        record["parent_slug"] = req.new_parent_slug
        src_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "status": "remapped",
            "spec_slug": req.spec_slug,
            "university_slug": req.university_slug,
            "old_parent_slug": old_parent,
            "new_parent_slug": req.new_parent_slug,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


class GenerateSpecializationStubRequest(BaseModel):
    university_slug: str
    spec_name: str
    parent_course_slug: str


@app.post("/generate-specialization-stub")
async def generate_specialization_stub_endpoint(req: GenerateSpecializationStubRequest):
    try:
        import re
        from workspace.manager import save_page, resolve_page_dir
        from workspace.compiler import compile_workspace
        from core.router import render_resolved

        # 1. Clean inputs
        uni_slug = req.university_slug.lower().strip()
        spec_name = req.spec_name.strip()
        parent_slug = req.parent_course_slug.lower().strip()

        # 2. Derive specialization slug
        spec_slugified = re.sub(r"[^a-z0-9]+", "-", spec_name.lower()).strip("-")
        spec_slug = f"{uni_slug}-{spec_slugified}"

        # 3. Inherit defaults from parent course if possible
        course_dir = resolve_page_dir(uni_slug, "course", parent_slug)
        course_json_path = course_dir / "source.json"

        uni_name = uni_slug.upper()
        mode = "100% Online"
        duration = "2 Years"
        naac_grade = None
        ugc_status = None
        parent_program_name = None

        if course_json_path.exists():
            try:
                import json
                course_data = json.loads(course_json_path.read_text(encoding="utf-8"))
                c_raw = course_data.get("data", {})
                uni_name = c_raw.get("university_name") or uni_name
                mode = c_raw.get("mode") or mode
                duration = c_raw.get("duration") or duration
                naac_grade = c_raw.get("naac_grade")
                ugc_status = c_raw.get("ugc_status")
                names = [c_raw.get("program_name"), c_raw.get("course_name"), c_raw.get("title")]
                parent_program_name = " ".join(filter(None, names))
            except Exception:
                pass

        if not parent_program_name:
            parent_program_name = parent_slug.replace("-", " ").title()


        # Clean the spec name using the normalization helper
        from core.utils import normalize_specialization_name
        cleaned_name = normalize_specialization_name(spec_name, parent_program_name, uni_name)


        # Prepare source JSON
        source_json = {
            "spec_name": cleaned_name,
            "university_name": uni_name,
            "mode": mode,
            "duration": duration,
            "total_fee": "",
            "hero_description": f"Boost your career with an online specialization in {cleaned_name} from {uni_name}.",
            "about_content": f"<p>The specialization in {cleaned_name} is designed to equip you with the advanced skills and knowledge needed for high-growth roles in this domain.</p>",
            "hero_image_url": "/Assets/images/default-spec.jpg",
            "hero_image_alt": f"Online specialization in {cleaned_name}",
        }
        if naac_grade:
            source_json["naac_grade"] = naac_grade
        if ugc_status:
            source_json["ugc_status"] = ugc_status

        # Prepare dummy/stub rendered html
        resolved = {
            "slug": spec_slug,
            "page_type": "specialization",
            "university_slug": uni_slug,
            "parent_slug": parent_slug,
            "raw": source_json,
        }

        html = render_resolved(resolved, standalone=True)

        # Save stub page
        result = save_page(
            university_slug=uni_slug,
            page_type="specialization",
            slug=spec_slug,
            source_json=source_json,
            rendered_html=html,
            parent_slug=parent_slug
        )

        # Run compile to build the compiled html output and update the sibling specs cache
        compile_workspace(uni_slug)

        return {
            "slug": spec_slug,
            "parent_slug": parent_slug,
            "status": "created"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# Workspace endpoints
# ──────────────────────────────────────────────────────────────────────────────

class CreateWorkspaceRequest(BaseModel):
    university_slug: str
    university_name: Optional[str] = None
    metadata_overrides: Optional[dict[str, Any]] = None


@app.post("/workspaces")
async def create_workspace_endpoint(req: CreateWorkspaceRequest):
    """
    Create a new university workspace on disk:
    1. Writes metadata.json with university info.
    2. Initialises the 3 system listing pages (Programs, Specializations, Blog).

    Returns { university_slug, workspace_dir, pages_created }
    """
    try:
        slug = req.university_slug.lower().strip()
        overrides = req.metadata_overrides or {}
        if req.university_name:
            overrides["university_name"] = req.university_name

        meta = ensure_metadata(slug, overrides)

        # Initialise the 3 system listing pages
        listing_results = init_system_pages(slug)

        return {
            "status": "created",
            "university_slug": slug,
            "workspace_dir": str(WORKSPACES_ROOT / slug),
            "metadata": meta,
            "pages_created": len(listing_results),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


class SaveToWorkspaceRequest(BaseModel):
    acf_data: dict[str, Any]
    images: dict[str, str] = {}
    metadata_overrides: Optional[dict[str, Any]] = None


@app.post("/save-to-workspace")
async def save_to_workspace(req: SaveToWorkspaceRequest):
    """
    Transform the ACF JSON, render the HTML, and persist both into the
    university workspace folder structure.

    source.json (source of truth) + page.html are written to:
      university  → workspaces/<uni>/University/
      course      → workspaces/<uni>/Courses/<slug>/
      spec        → workspaces/<uni>/Courses/<parent>/Specializations/<slug>/
      blog        → workspaces/<uni>/Blogs/<slug>/
    """
    try:
        slug, page_type, university_slug, parent_slug, acf_data = extract_metadata_from_json(req.acf_data)
        acf_data.pop("detected_specializations", None)
        
        # 1. Validate required images before compile/save
        required_slots = {
            "university": ["hero_image_url"],
            "course": ["hero_image_url", "certificate_image_url"],
            "specialization": ["hero_image_url"],
            "blog": ["hero_image_url"]
        }
        
        if page_type in required_slots:
            for slot in required_slots[page_type]:
                val_in_images = req.images.get(slot)
                val_in_acf = acf_data.get(slot)
                if not val_in_images and not val_in_acf:
                    labels = {
                        "hero_image_url": "Hero Image",
                        "certificate_image_url": "Degree Certificate Image"
                    }
                    slot_name = labels.get(slot, slot.replace("_", " ").title())
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required image: {slot_name}"
                    )

        # 2. Process and save base64 images to local Assets/images/ directory
        assets_dir = WORKSPACES_ROOT / university_slug / "Assets" / "images"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        image_slots = set(req.images.keys()) | {
            "hero_image_url", "certificate_image_url", "featured_image_url", "og_image_url"
        }

        for slot in image_slots:
            img_data = req.images.get(slot) or acf_data.get(slot)
            if not img_data:
                continue
            prefix = image_prefix_for_slot(page_type, slug, slot)
            local_path = save_base64_image(img_data, assets_dir, prefix)
            if local_path:
                acf_data[slot] = local_path

        # Prepare for rendering
        resolved = {
            "slug": slug,
            "page_type": page_type,
            "university_slug": university_slug,
            "parent_slug": parent_slug,
            "raw": acf_data,
        }

        # Render the HTML
        standalone = page_type in ("course", "specialization", "blog")
        html = render_resolved(resolved, standalone=standalone)

        # Optionally update workspace metadata (phone, email, theme, etc.)
        if req.metadata_overrides:
            ensure_metadata(university_slug, req.metadata_overrides)

        # Save to workspace
        result = save_page(
            university_slug=university_slug,
            page_type=page_type,
            slug=slug,
            source_json=acf_data,
            rendered_html=html,
            parent_slug=parent_slug,
        )

        # After saving user content, auto-re-render all 3 listing pages
        # so they always reflect the latest workspace state.
        try:
            from workspace.compiler import _build_index, _auto_render_listing_pages
            index = _build_index(university_slug)
            _auto_render_listing_pages(university_slug, index)
        except Exception as listing_err:
            # Non-fatal: listing pages will be refreshed on next compile
            import logging
            logging.warning(f"Listing page re-render skipped: {listing_err}")

        return {
            "status": "saved",
            **result,
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/compile-workspace")
async def compile_workspace_endpoint(university_slug: str = Form(...)):
    """
    Run the two-pass workspace compiler for the given university.

    Pass 1 — scans all source.json files and builds a global index of
             courses, specs, blogs and the university page.
    Pass 2 — enriches each page with resolved parent/sibling context,
             re-renders via the Jinja2 engine, and overwrites each .html file.
    """
    try:
        result = compile_workspace(university_slug)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/workspaces/{university_slug}/branding")
async def upload_branding_endpoint(
    university_slug: str,
    logo: UploadFile = File(None),
    favicon: UploadFile = File(None)
):
    """
    Upload university logo and/or favicon.
    Updates workspace metadata.json and re-compiles pages immediately.
    """
    try:
        uni_dir = WORKSPACES_ROOT / university_slug
        if not uni_dir.exists():
            raise HTTPException(status_code=404, detail=f"Workspace '{university_slug}' not found")
        
        meta = ensure_metadata(university_slug)
        if "branding" not in meta:
            meta["branding"] = {"logo": "", "favicon": ""}
        
        # Validation: Logo is required either now or previously uploaded
        if not logo and not meta["branding"].get("logo"):
            raise HTTPException(status_code=400, detail="University Logo is required.")
        
        assets_dir = uni_dir / "Assets" / "images"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        logo_ext = None
        logo_saved = False
        
        if logo and logo.filename:
            logo_ext = Path(logo.filename).suffix.lower()
            if not logo_ext:
                logo_ext = ".png"
            logo_filename = f"branding-{university_slug}-logo{logo_ext}"
            logo_path = assets_dir / logo_filename
            
            content = await logo.read()
            logo_path.write_bytes(content)
            
            meta["branding"]["logo"] = f"/assets/images/{logo_filename}"
            logo_saved = True
            
        # Get logo extension from metadata if logo was not uploaded but exists
        if not logo_saved and meta["branding"].get("logo"):
            logo_ext = Path(meta["branding"]["logo"]).suffix.lower()
            
        if favicon and favicon.filename:
            fav_ext = Path(favicon.filename).suffix.lower()
            if not fav_ext:
                fav_ext = ".ico"
            fav_filename = f"branding-{university_slug}-favicon{fav_ext}"
            fav_path = assets_dir / fav_filename
            
            content = await favicon.read()
            fav_path.write_bytes(content)
            
            meta["branding"]["favicon"] = f"/assets/images/{fav_filename}"
        elif logo_saved and logo_ext and not meta["branding"].get("favicon"):
            # Auto-generate favicon from logo by copying it
            fav_filename = f"branding-{university_slug}-favicon{logo_ext}"
            fav_path = assets_dir / fav_filename
            logo_filename = f"branding-{university_slug}-logo{logo_ext}"
            logo_path = assets_dir / logo_filename
            
            import shutil
            shutil.copy2(logo_path, fav_path)
            meta["branding"]["favicon"] = f"/assets/images/{fav_filename}"
            
        # Save updated metadata
        meta_path = uni_dir / "metadata.json"
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        
        # Compile workspace
        compile_result = compile_workspace(university_slug)
        
        return {
            "status": "success",
            "branding": meta["branding"],
            "compile_result": compile_result
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/workspaces/{university_slug}/pages/{page_type}/{slug}")
async def get_workspace_page_endpoint(
    university_slug: str,
    page_type: str,
    slug: str,
    parent_slug: Optional[str] = None
):
    """Retrieve a single page's source.json content for editing in frontend."""
    try:
        from workspace.manager import resolve_page_dir, read_source
        page_dir = resolve_page_dir(university_slug, page_type, slug, parent_slug)
        source_path = page_dir / "source.json"
        
        if not source_path.exists():
            # Specialization flat directory search fallback
            if page_type == "specialization":
                for p in (WORKSPACES_ROOT / university_slug / "Specializations").glob("*/source.json"):
                    try:
                        record = json.loads(p.read_text(encoding="utf-8"))
                        if record.get("slug") == slug:
                            return record
                    except Exception:
                        pass
            raise HTTPException(status_code=404, detail="Page source.json not found")
        
        record = read_source(source_path)
        if not record:
            raise HTTPException(status_code=404, detail="Failed to read page source")
        return record
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/workspace-tree")
async def workspace_tree_endpoint(university_slug: str):
    """
    Return a nested JSON tree describing the workspace structure for a university.
    Used by the frontend workspace browser.
    """
    try:
        tree = get_workspace_tree(university_slug)
        return tree
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.delete("/delete-page")
async def delete_page_endpoint(
    university_slug: str,
    page_type: str,
    slug: str,
    parent_slug: str | None = None
):
    """
    Delete a page from the university workspace directory on disk,
    then trigger a workspace re-compilation to update the index and listing pages.
    """
    try:
        if page_type not in ("course", "specialization", "blog"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete page of type '{page_type}'"
            )

        from workspace.manager import resolve_page_dir
        
        # Get directory on disk
        page_dir = resolve_page_dir(university_slug, page_type, slug, parent_slug)
        
        # Security check: Ensure page_dir is inside WORKSPACES_ROOT / university_slug
        uni_root = (WORKSPACES_ROOT / university_slug).resolve()
        resolved_page_dir = page_dir.resolve()
        
        try:
            resolved_page_dir.relative_to(uni_root)
        except ValueError:
            raise HTTPException(
                status_code=403,
                detail="Access denied: invalid page path"
            )
            
        if not resolved_page_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Page directory for '{slug}' not found"
            )
            
        # Delete directory recursively
        import shutil
        shutil.rmtree(resolved_page_dir)
        
        # Re-compile workspace to update indexes/listings
        compile_result = compile_workspace(university_slug)
        
        return {
            "status": "success",
            "message": f"Successfully deleted {page_type} page '{slug}'",
            "compile_result": compile_result
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.delete("/workspaces/{university_slug}")
async def delete_workspace_endpoint(university_slug: str):
    """
    Delete an entire university workspace folder from disk.
    """
    try:
        slug = university_slug.lower().strip()
        uni_dir = (WORKSPACES_ROOT / slug).resolve()
        
        # Security check: Ensure we only delete directories inside WORKSPACES_ROOT
        try:
            uni_dir.relative_to(WORKSPACES_ROOT.resolve())
        except ValueError:
            raise HTTPException(
                status_code=403,
                detail="Access denied: invalid workspace path"
            )
            
        if not uni_dir.exists() or not uni_dir.is_dir():
            raise HTTPException(
                status_code=404,
                detail=f"Workspace '{slug}' not found"
            )
            
        import shutil
        shutil.rmtree(uni_dir)
        
        return {
            "status": "success",
            "message": f"Successfully deleted workspace '{slug}'"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/workspaces")
async def list_workspaces_endpoint():
    """Return a list of all university workspaces that exist on disk."""
    slugs = list_workspaces()
    workspaces = []
    for slug in slugs:
        try:
            meta = ensure_metadata(slug)
        except Exception:
            meta = {}
        workspaces.append({
            "slug": slug,
            "name": meta.get("university_name", slug.replace("-", " ").title()),
            "last_compiled_at": meta.get("last_compiled_at"),
            "created_at": meta.get("created_at"),
            "branding": meta.get("branding", {"logo": "", "favicon": ""}),
        })
    return {"workspaces": workspaces}


# ──────────────────────────────────────────────────────────────────────────────
# Website Builder endpoints (Pass 4 — deployable static export)
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/build-website")
async def build_website_endpoint(
    university_slug: str = Form(...),
    skip_compile: bool = Form(False),
):
    """
    Build a deployable static website package for a university workspace.

    By default, runs a full workspace compile (Pass 1–3) first so the
    exported build always reflects the latest source.json files. Pass
    `skip_compile=true` to export the already-compiled .html files as-is.

    Writes the build to workspaces/<uni>/build/ and returns a summary:
      { pages_compiled, pages_failed, images_copied, downloads_copied,
        routes_generated, build_path, build_url, routes, errors, built_at }
    """
    try:
        compile_summary = None
        if not skip_compile:
            compile_summary = compile_workspace(university_slug)

        result = build_website(university_slug)
        result["compile_summary"] = compile_summary
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/build-status")
async def build_status_endpoint(university_slug: str):
    """
    Return whether a build exists for a workspace (without rebuilding),
    plus its routes and basic stats. Used by the frontend to render the
    'Build Complete' panel on load.
    """
    try:
        return get_build_status(university_slug)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/build-file")
async def build_file_endpoint(university_slug: str, path: str = "index.html"):
    """
    Serve a single file from a workspace's build/ folder.
    Used by the iframe / new-tab preview of the built website.
    """
    from fastapi.responses import FileResponse
    try:
        slug = university_slug.lower().strip()
        build_dir = WORKSPACES_ROOT / slug / "build"
        # Normalise and prevent path traversal outside build/
        target = (build_dir / path).resolve()
        try:
            target.relative_to(build_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid path")

        if not target.exists() or not target.is_file():
            raise HTTPException(status_code=404, detail="Build file not found")

        # Guess media type from extension
        ext = target.suffix.lower()
        media_type = "application/octet-stream"
        if ext == ".html":
            media_type = "text/html"
        elif ext == ".css":
            media_type = "text/css"
        elif ext == ".js":
            media_type = "application/javascript"
        elif ext == ".json":
            media_type = "application/json"
        elif ext == ".xml":
            media_type = "application/xml"
        elif ext == ".png":
            media_type = "image/png"
        elif ext in (".jpg", ".jpeg"):
            media_type = "image/jpeg"
        elif ext == ".webp":
            media_type = "image/webp"
        elif ext == ".gif":
            media_type = "image/gif"
        elif ext == ".svg":
            media_type = "image/svg+xml"
        elif ext == ".pdf":
            media_type = "application/pdf"

        if ext == ".html":
            html = target.read_text(encoding="utf-8")
            # Inject a client-side link interception script to make navigation work with build-file params
            script = f"""
<script>
document.addEventListener('click', function(e) {{
  var a = e.target.closest('a');
  if (a && a.getAttribute('href')) {{
    var href = a.getAttribute('href');
    if (href.startsWith('/') && !href.startsWith('/build-file') && !href.startsWith('/download-build')) {{
      e.preventDefault();
      var path = href.substring(1);
      if (!path || path.endsWith('/')) {{
        path += 'index.html';
      }}
      var url = '/build-file?university_slug=' + encodeURIComponent('{university_slug}') + '&path=' + encodeURIComponent(path);
      window.location.href = url;
    }}
  }}
}});
</script>
"""
            if "</body>" in html:
                html = html.replace("</body>", f"{script}</body>")
            else:
                html += script
            
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html)

        return FileResponse(target, media_type=media_type)
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/download-build")
async def download_build_endpoint(university_slug: str):
    """
    Download the entire build/ folder as a ZIP archive.
    Returns a file attachment named <uni>-website.zip.
    """
    try:
        zip_bytes, filename = zip_build(university_slug)
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    host = "127.0.0.1"
    port = 8000
    print(f"\n=======================================================")
    print(f"🚀 Page Engine server running at: http://{host}:{port}")
    print(f"=======================================================\n")
    uvicorn.run("main:app", host=host, port=port, reload=True)
