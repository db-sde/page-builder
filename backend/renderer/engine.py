from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.router import get_transformer
from core.utils import format_fee as clean_fee
from workspace.manager import WORKSPACES_ROOT
import os
from pathlib import Path
import json
import re
from html.parser import HTMLParser

# TODO: add Redis caching layer here — render_resolved should check cache before re-rendering

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
TEMPLATES_V2_DIR = os.path.join(os.path.dirname(__file__), "..", "templates_v2")

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)

from jinja2 import pass_context
from PIL import Image

env_v2 = Environment(
    loader=FileSystemLoader(TEMPLATES_V2_DIR),
    autoescape=select_autoescape(["html"]),
)

# Custom filter — strips None safely for templates
def default_empty(value):
    return value if value is not None else ""

env.filters["de"] = default_empty
env_v2.filters["de"] = default_empty

def webp_variant_filter(url, width=None):
    if not url:
        return ""
    p = Path(url)
    if width:
        return str(p.with_name(f"{p.stem}-{width}.webp"))
    else:
        return str(p.with_name(f"{p.stem}.webp"))

@pass_context
def image_width_filter(context, url):
    if not url:
        return "0"
    uni_slug = context.get("university_slug")
    if not uni_slug:
        return "0"
    filename = Path(url).name
    src_file = WORKSPACES_ROOT / uni_slug / "Assets" / "images" / filename
    if src_file.exists():
        try:
            with Image.open(src_file) as img:
                return str(img.width)
        except Exception:
            pass
    return "0"

@pass_context
def image_height_filter(context, url):
    if not url:
        return "0"
    uni_slug = context.get("university_slug")
    if not uni_slug:
        return "0"
    filename = Path(url).name
    src_file = WORKSPACES_ROOT / uni_slug / "Assets" / "images" / filename
    if src_file.exists():
        try:
            with Image.open(src_file) as img:
                return str(img.height)
        except Exception:
            pass
    return "0"

env_v2.filters["webp_variant"] = webp_variant_filter
env_v2.filters["image_width"] = image_width_filter
env_v2.filters["image_height"] = image_height_filter

# clean_fee is now the single canonical implementation, imported as
# core.utils.format_fee (previously duplicated verbatim here and as
# BaseTransformer.format_fee in transformers/base.py).

TEMPLATE_MAP = {
    "university": "university.html",
    "course": "course.html",
    "specialization": "specialization.html",
    "blog": "blog.html",
    "programs_listing": "programs_listing.html",
    "specializations_listing": "specializations_listing.html",
    "blog_listing": "blog_listing.html",
}

def load_env():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env()

def build_lead_payload(
    university_slug: str = None,
    program_slug: str = None,
    specialization_slug: str = None,
    source: str = None,
    uni_name: str = None,
    logo_letter: str = None,
    program_name: str = None,
    specialization_name: str = None
) -> str:
    """Build a deterministic, URL-safe Base64 encoded JSON payload ignoring null/empty fields."""
    import base64
    import json
    payload = {}
    if university_slug and str(university_slug).strip():
        payload["uni"] = str(university_slug).strip()
    if program_slug and str(program_slug).strip():
        payload["program"] = str(program_slug).strip()
    if specialization_slug and str(specialization_slug).strip():
        payload["specialization"] = str(specialization_slug).strip()
    if source and str(source).strip():
        payload["source"] = str(source).strip()
    if uni_name and str(uni_name).strip():
        payload["uni_name"] = str(uni_name).strip()
    if logo_letter and str(logo_letter).strip():
        payload["logo_letter"] = str(logo_letter).strip()
    if program_name and str(program_name).strip():
        payload["program_name"] = str(program_name).strip()
    if specialization_name and str(specialization_name).strip():
        payload["specialization_name"] = str(specialization_name).strip()
    
    json_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return base64.urlsafe_b64encode(json_bytes).decode('utf-8')

def build_lead_url(
    uni_slug: str,
    course_slug: str = None,
    source: str = "page",
    spec_slug: str = None,
    uni_name: str = None,
    logo_letter: str = None,
    program_name: str = None,
    specialization_name: str = None
) -> str:
    """Build a centralized lead capture URL with encoded payload."""
    base = os.environ.get("LEAD_BASE_URL")
    if not base:
        raise ValueError("LEAD_BASE_URL environment variable is missing")
        
    base = base.rstrip("/")
    payload = build_lead_payload(
        university_slug=uni_slug,
        program_slug=course_slug,
        specialization_slug=spec_slug,
        source=source,
        uni_name=uni_name,
        logo_letter=logo_letter,
        program_name=program_name,
        specialization_name=specialization_name
    )
    return f"{base}/form?d={payload}"

class SyllabusHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.syllabus_years = []
        self.current_year_dict = None
        self.current_sem = None
        self.in_heading = False
        self.in_li = False
        self.heading_text = ""
        self.li_text = ""

    def handle_starttag(self, tag, attrs):
        if tag in ("h3", "h4", "h5", "h6"):
            self.in_heading = True
            self.heading_text = ""
        elif tag == "li":
            self.in_li = True
            self.li_text = ""

    def handle_endtag(self, tag):
        if tag in ("h3", "h4", "h5", "h6"):
            self.in_heading = False
            text = self.heading_text.strip()
            if text:
                year_match = re.search(r"\byear\b\s*(i+|v+|[1-9]\b|one|two|three|four|five)", text, re.IGNORECASE)
                sem_match = re.search(r"\bsem(ester)?\b\s*(i+|v+|[1-9]\b|one|two|three|four|five|six|seven|eight)", text, re.IGNORECASE)
                
                if year_match and not sem_match:
                    year_label = text
                    existing = next((y for y in self.syllabus_years if y["label"].lower() == year_label.lower()), None)
                    if existing:
                        self.current_year_dict = existing
                    else:
                        self.current_year_dict = {"label": year_label, "semesters": []}
                        self.syllabus_years.append(self.current_year_dict)
                elif sem_match:
                    if self.current_year_dict is None:
                        self.current_year_dict = {"label": "Year I", "semesters": []}
                        self.syllabus_years.append(self.current_year_dict)
                    self.current_sem = {"title": text, "subjects": []}
                    self.current_year_dict["semesters"].append(self.current_sem)
        elif tag == "li":
            self.in_li = False
            text = self.li_text.strip()
            if text and self.current_sem is not None:
                self.current_sem["subjects"].append(text)

    def handle_data(self, data):
        if self.in_heading:
            self.heading_text += data
        elif self.in_li:
            self.li_text += data

def parse_syllabus_html(html_str: str) -> list[dict]:
    if not html_str:
        return []
    parser = SyllabusHTMLParser()
    try:
        parser.feed(html_str)
        return parser.syllabus_years
    except Exception:
        return []

class AdmissionHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.steps = []
        self.in_p = False
        self.in_li = False
        self.p_text = ""
        self.li_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.in_p = True
            self.p_text = ""
        elif tag == "li":
            self.in_li = True
            self.li_text = ""

    def handle_endtag(self, tag):
        if tag == "p":
            self.in_p = False
            text = self.p_text.strip()
            if text:
                self._add_step(text)
        elif tag == "li":
            self.in_li = False
            text = self.li_text.strip()
            if text:
                self._add_step(text)

    def handle_data(self, data):
        if self.in_p:
            self.p_text += data
        elif self.in_li:
            self.li_text += data

    def _add_step(self, text):
        for prefix in ("•", "▪", "●", "○", "■", "- ", "* "):
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        match = re.match(r"^(Step\s*(\d+)[\.\s:]*|(\d+)[\.\s:]+)(.*)$", text, re.IGNORECASE)
        if match:
            step_num = match.group(2) or match.group(3)
            step_text = match.group(4).strip()
            self.steps.append({"n": step_num, "t": step_text})
        else:
            if len(self.steps) == 0 and ("admission" in text.lower() or "process" in text.lower() or "enroll" in text.lower() or "follow" in text.lower()):
                return
            idx = len(self.steps) + 1
            self.steps.append({"n": str(idx), "t": text})

def parse_admission_html(html_str: str) -> list[dict]:
    if not html_str:
        return []
    parser = AdmissionHTMLParser()
    try:
        parser.feed(html_str)
        return parser.steps
    except Exception:
        return []

def clean_spec_name(name: str, uni_name: str = None, prog_name: str = None) -> str:
    if not name:
        return name
    name_clean = name.strip()
    
    # 1. Targeted regex pattern to strip any university or course prefix followed by "Online MBA in" / "MBA in"
    # E.g., "Manipal Online Mba In Human Resource Management" -> "Human Resource Management"
    pattern = re.compile(r'.*?\b(online\s+)?(mba|mca|bba|bca|msc|bcom|mcom)\s+in\s+', re.IGNORECASE)
    match = pattern.match(name_clean)
    if match:
        return name_clean[match.end():].strip()
        
    # 2. Split fallback: if there is a standalone "in"/"In", get the final part
    parts = re.split(r'\s+in\s+', name_clean, flags=re.IGNORECASE)
    if len(parts) > 1:
        candidate = parts[-1].strip()
        if candidate:
            return candidate
            
    return name_clean


def clean_html_tables(html: str) -> str:
    if not html:
        return html

    def repl(match):
        table_open_tag = match.group(1)
        table_content = match.group(2)
        
        # Find all tr blocks inside table_content
        tr_blocks = re.findall(r'<tr[^>]*>.*?</tr>', table_content, re.DOTALL | re.IGNORECASE)
        if tr_blocks:
            first_tr = tr_blocks[0]
            # Find cells in the first row
            cells = re.findall(r'<(?:th|td)[^>]*>(.*?)</(?:th|td)>', first_tr, re.DOTALL | re.IGNORECASE)
            cells_cleaned = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            
            if cells_cleaned and len(cells_cleaned) > 1 and len(set(cells_cleaned)) == 1 and cells_cleaned[0]:
                table_title = cells_cleaned[0]
                
                if len(tr_blocks) >= 2:
                    second_tr = tr_blocks[1]
                    second_cells = re.findall(r'<(?:th|td)[^>]*>(.*?)</(?:th|td)>', second_tr, re.DOTALL | re.IGNORECASE)
                    
                    if second_cells:
                        new_thead = "<thead><tr>" + "".join(f"<th>{c}</th>" for c in second_cells) + "</tr></thead>"
                        new_tbody_rows = "".join(tr_blocks[2:])
                        return f"<h3>{table_title}</h3>\n{table_open_tag}\n{new_thead}\n<tbody>\n{new_tbody_rows}\n</tbody>\n</table>"
                        
        return match.group(0)

    return re.sub(r'(<table[^>]*>)(.*?)</table>', repl, html, flags=re.DOTALL | re.IGNORECASE)


def render_resolved(resolved: dict, standalone: bool = False, render_mode: str = "v1") -> str:
    from workspace.knowledge import load_or_create_knowledge, resolve_field, resolve_list

    uni_slug = resolved.get("university_slug") or "nmims"
    knowledge = load_or_create_knowledge(uni_slug)

    transformer = get_transformer(resolved)
    ctx = transformer.transform()    # Phase 3 — Context Extraction
    raw_dict = resolved.get("raw") or {}
    
    # 1. University Display Name
    uni_name = resolve_field(raw_dict, knowledge, "university_name")
    if not uni_name and ctx.get("university_name"):
        uni_name = ctx["university_name"]
    if not uni_name and raw_dict.get("name") and resolved.get("page_type") == "university":
        uni_name = raw_dict["name"]
    if not uni_name:
        uni_name = resolve_field(raw_dict, knowledge, "university_full_name") or resolved.get("university_slug", "nmims").upper()
        
    logo_letter = uni_name[0].upper() if uni_name else "N"
    
    page_type = resolved.get("page_type", "course")
    course_slug = resolved.get("parent_slug") or resolved.get("slug") or ""

    ctx["university_name"] = uni_name
    ctx["university_letter"] = logo_letter

    branding_logo = resolve_field(raw_dict, knowledge, "logo")
    branding_favicon = resolve_field(raw_dict, knowledge, "favicon")
    if not branding_logo or not branding_favicon:
        meta_path = WORKSPACES_ROOT / uni_slug / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_json = json.load(f)
                    branding = meta_json.get("branding") or {}
                    if not branding_logo:
                        branding_logo = branding.get("logo") or ""
                    if not branding_favicon:
                        branding_favicon = branding.get("favicon") or ""
            except Exception:
                pass
    ctx["branding_logo"] = branding_logo
    ctx["branding_favicon"] = branding_favicon
    ctx["homepage_href"] = f"{uni_slug}.dc.html"
    ctx["course_href"] = f"{uni_slug}-online-mba.dc.html"
    ctx["spec_href"] = f"{uni_slug}-mba-marketing.dc.html"
    ctx["blog_href"] = f"{uni_slug}-blog.dc.html"
    ctx["programs_listing_href"] = "programs_listing.html"
    ctx["specs_listing_href"] = "specializations_listing.html"
    ctx["blog_listing_href"] = "blog_listing.html"

    # 2. Program Display Name
    prog_name = None
    
    # Check parent course first if on specialization page
    if page_type == "specialization":
        parent_course = raw_dict.get("_workspace_parent") or {}
        parent_data = parent_course.get("data") or parent_course.get("raw") or {}
        if parent_data:
            prog_name = (
                parent_data.get("program_name") or
                parent_data.get("course_name") or
                parent_data.get("title")
            )
            
    # Search current page raw_dict and ctx
    if not prog_name:
        prog_name = (
            raw_dict.get("program_name") or
            raw_dict.get("course_name") or
            raw_dict.get("title") or
            ctx.get("program_name") or
            ctx.get("course_name")
        )
        
    # Priority 3: Search other courses in the workspace
    if not prog_name:
        workspace_courses = raw_dict.get("_workspace_courses") or []
        for c in workspace_courses:
            if isinstance(c, dict):
                c_data = c.get("data") or c.get("raw") or {}
                val = c_data.get("program_name") or c_data.get("course_name") or c_data.get("title")
                if val and str(val).strip():
                    prog_name = str(val).strip()
                    break
                    
    # Priority 4: Last-resort fallback to slug
    if not prog_name:
        course_slug_val = resolved.get("parent_slug") if page_type == "specialization" else (resolved.get("slug") if page_type == "course" else None)
        if course_slug_val:
            prog_name = course_slug_val.replace("-", " ").title()

    # 3. Specialization Display Name
    spec_name = None
    if page_type == "specialization":
        raw_spec_name = (
            raw_dict.get("spec_name") or
            raw_dict.get("specialization_name") or
            raw_dict.get("title") or
            ctx.get("spec_name") or
            ctx.get("specialization_name")
        )
        
        if raw_spec_name:
            spec_name = clean_spec_name(raw_spec_name, uni_name=uni_name, prog_name=prog_name)
            
        if not spec_name and resolved.get("slug"):
            slug_val = resolved.get("slug")
            parent_val = resolved.get("parent_slug") or ""
            if parent_val and slug_val.startswith(parent_val + "-"):
                slug_val = slug_val[len(parent_val) + 1:]
            spec_name = slug_val.replace("-", " ").title()

    # Centralized lead URL — no contact/lead forms in this project
    # Centralized lead URL — only pass program_name/specialization_name on course/specialization pages
    spec_slug_arg = resolved.get("slug") if page_type == "specialization" else None
    course_slug_val = resolved.get("parent_slug") if page_type == "specialization" else (resolved.get("slug") if page_type == "course" else None)
    
    send_prog_name = prog_name if page_type in ("course", "specialization") else None
    send_spec_name = spec_name if page_type == "specialization" else None

    ctx["lead_url"] = build_lead_url(
        uni_slug, course_slug_val, source=page_type, spec_slug=spec_slug_arg,
        uni_name=uni_name, logo_letter=logo_letter, program_name=send_prog_name,
        specialization_name=send_spec_name
    )
    
    # Inject lead URLs context variables
    ctx["lead_base_url"] = os.environ.get("LEAD_BASE_URL", "http://localhost:3001")
    ctx["university_slug"] = uni_slug
    ctx["slug"] = resolved.get("slug") or ""
    ctx["parent_course_slug"] = resolved.get("parent_slug") or ""
    ctx["specialization_slug"] = resolved.get("slug") or ""
    
    # Inject action-specific encoded lead URLs
    ctx["lead_url_apply"] = build_lead_url(
        uni_slug, course_slug_val, "apply", spec_slug_arg,
        uni_name=uni_name, logo_letter=logo_letter, program_name=send_prog_name,
        specialization_name=send_spec_name
    )
    ctx["lead_url_brochure"] = build_lead_url(
        uni_slug, course_slug_val, "brochure", spec_slug_arg,
        uni_name=uni_name, logo_letter=logo_letter, program_name=send_prog_name,
        specialization_name=send_spec_name
    )
    ctx["lead_url_enquiry"] = build_lead_url(
        uni_slug, course_slug_val, "enquiry", spec_slug_arg,
        uni_name=uni_name, logo_letter=logo_letter, program_name=send_prog_name,
        specialization_name=send_spec_name
    )
    ctx["lead_url_fees"] = build_lead_url(
        uni_slug, course_slug_val, "fees", spec_slug_arg,
        uni_name=uni_name, logo_letter=logo_letter, program_name=send_prog_name,
        specialization_name=send_spec_name
    )
    ctx["lead_url_counselling"] = build_lead_url(
        uni_slug, course_slug_val, "counselling", spec_slug_arg,
        uni_name=uni_name, logo_letter=logo_letter, program_name=send_prog_name,
        specialization_name=send_spec_name
    )
    ctx["lead_url_syllabus"] = build_lead_url(
        uni_slug, course_slug_val, "syllabus", spec_slug_arg,
        uni_name=uni_name, logo_letter=logo_letter, program_name=send_prog_name,
        specialization_name=send_spec_name
    )
    ctx["lead_url_whatsapp"] = build_lead_url(
        uni_slug, course_slug_val, "whatsapp", spec_slug_arg,
        uni_name=uni_name, logo_letter=logo_letter, program_name=send_prog_name,
        specialization_name=send_spec_name
    )
    
    if "parent_program_name" not in ctx:
        ctx["parent_program_name"] = prog_name
    if "parent_course_name" not in ctx:
        ctx["parent_course_name"] = prog_name

    ctx["site"] = ctx.get("site") or {}

    # Pre-serialize variables to JSON for the Component script block
    # 1. Stats
    ctx["stats_json"] = json.dumps(ctx.get("stats", []), ensure_ascii=False)
    
    # 2. Rail Def
    rail_list = [[r["label"], r["href"]] for r in ctx.get("rail", [])]
    ctx["rail_json"] = json.dumps(rail_list, ensure_ascii=False)
    
    # 3. Highlights
    highlights_raw = ctx.get("highlights", []) or []
    if isinstance(highlights_raw, str):
        highlights_raw = [{"highlight_title": "Highlight", "highlight_description": highlights_raw}]
    elif isinstance(highlights_raw, list):
        new_h = []
        for h in highlights_raw:
            if isinstance(h, str):
                new_h.append({"highlight_title": "Highlight", "highlight_description": h})
            elif isinstance(h, dict):
                new_h.append(h)
        highlights_raw = new_h
    h_list = [
        {
            "t": h.get("t") or h.get("highlight_title", ""),
            "d": h.get("d") or h.get("highlight_description", "")
        }
        for h in highlights_raw
    ]
    ctx["highlights_json"] = json.dumps(h_list, ensure_ascii=False)
    
    # 4. Specs (items)
    # ONLY use real workspace specializations filtered by parent_course_slug.
    # No fallback to raw specialization field or hardcoded placeholders.
    if page_type != "specializations_listing":
        workspace_specs_ctx = ctx.get("_workspace_specs") or []
        workspace_courses = raw_dict.get("_workspace_courses") or []
        spec_list = []
        for sp in workspace_specs_ctx:
            if not isinstance(sp, dict):
                continue
            data = sp.get("data", {})
            sp_slug = sp.get("slug", "")
            parent = sp.get("parent_slug") or data.get("parent_slug") or "general"
            course_name = parent.replace("-", " ").title()
            for c in workspace_courses:
                if isinstance(c, dict) and c.get("slug") == parent:
                    cd = c.get("data", {})
                    course_name = cd.get("program_name") or cd.get("course_name") or course_name
                    break
            spec_list.append({
                "course_name": course_name,
                "t": data.get("spec_name") or data.get("program_name") or sp_slug.replace("-", " ").title(),
                "d": data.get("hero_description") or data.get("description") or "",
                "href": f"{sp_slug}.html",
                "fee": clean_fee(data.get("total_fee") or data.get("starting_fee") or ""),
            })
        ctx["specs_json"] = json.dumps(spec_list, ensure_ascii=False)
        ctx["specs"] = spec_list
    fee_plans = (ctx.get("fees") or {}).get("plans") or resolve_list(raw_dict, knowledge, "fee_plans")
    if isinstance(fee_plans, str):
        fee_plans = [{"plan_name": "Full Program", "plan_amount": fee_plans, "plan_total": fee_plans}]
    elif isinstance(fee_plans, list):
        new_plans = []
        for f in fee_plans:
            if isinstance(f, str):
                new_plans.append({"plan_name": "Full Program", "plan_amount": f, "plan_total": f})
            elif isinstance(f, dict):
                new_plans.append(f)
        fee_plans = new_plans
    fee_list = [
        {
            "plan": f.get("plan") or f.get("plan_name", ""),
            "amt": f.get("amt") or f.get("plan_amount", ""),
            "total": f.get("total") or f.get("plan_total", ""),
            "bg": f.get("bg", "#fff")
        }
        for f in fee_plans
    ]
    if not fee_list:
        fee_list = [
            {"plan": "Semester-wise", "amt": "₹50,000 / semester", "total": "₹2,00,000", "bg": "#fff"},
            {"plan": "Annual", "amt": "₹96,000 / year", "total": "₹1,92,000", "bg": "#F6F4FB"},
            {"plan": "One-time (Full Program)", "amt": "₹1,80,000 once", "total": "₹1,80,000", "bg": "#fff"}
        ]
    ctx["fees_json"] = json.dumps(fee_list, ensure_ascii=False)
    
    # 6. Admission Steps
    steps_list = parse_admission_html((ctx.get("admission") or {}).get("steps") if ctx.get("admission") else "")
    if not steps_list:
        steps_raw = resolve_field(raw_dict, knowledge, "admission_steps")
        if steps_raw:
            steps_list = parse_admission_html(steps_raw)
        else:
            steps_list = [
                {"n": "1", "t": "Register on the university portal and verify your mobile number."},
                {"n": "2", "t": "Complete the application form and choose Online MBA with your preferred specialization."},
                {"n": "3", "t": "Upload graduation marksheets, photo ID and a passport-size photograph."},
                {"n": "4", "t": "Pay the first installment online — enrollment and LMS access follow within 7 working days."}
            ]
    ctx["steps_json"] = json.dumps(steps_list, ensure_ascii=False)
    
    # 7. Job profiles
    jobs_raw = ctx.get("jobs") or resolve_list(raw_dict, knowledge, "job_profiles")
    if isinstance(jobs_raw, str):
        jobs_raw = [{"job_title": jobs_raw, "avg_salary": ""}]
    elif isinstance(jobs_raw, list):
        new_j = []
        for j in jobs_raw:
            if isinstance(j, str):
                new_j.append({"job_title": j, "avg_salary": ""})
            elif isinstance(j, dict):
                new_j.append(j)
        jobs_raw = new_j
    job_list = [
        {
            "t": j.get("t") or j.get("job_title", ""),
            "s": j.get("s") or j.get("avg_salary", "")
        }
        for j in jobs_raw
    ]
    if not job_list:
        job_list = [
            {"t": "Marketing Manager", "s": "₹12.5 LPA"},
            {"t": "Financial Analyst", "s": "₹9.8 LPA"},
            {"t": "HR Business Partner", "s": "₹10.2 LPA"},
            {"t": "Operations Manager", "s": "₹11.4 LPA"},
            {"t": "Business Analyst", "s": "₹10.8 LPA"},
            {"t": "Product Manager", "s": "₹16.5 LPA"}
        ]
    ctx["jobs_json"] = json.dumps(job_list, ensure_ascii=False)
    
    # 8. Reviews
    reviews_raw = ctx.get("reviews") or resolve_list(raw_dict, knowledge, "reviews")
    if isinstance(reviews_raw, str):
        reviews_raw = [{"review_text": reviews_raw, "reviewer_label": "Student"}]
    elif isinstance(reviews_raw, list):
        new_rv = []
        for r in reviews_raw:
            if isinstance(r, str):
                new_rv.append({"review_text": r, "reviewer_label": "Student"})
            elif isinstance(r, dict):
                new_rv.append(r)
        reviews_raw = new_rv
    review_list = [
        {
            "q": r.get("q") or r.get("review_text", ""),
            "a": r.get("a") or r.get("reviewer_label", "")
        }
        for r in reviews_raw
    ]
    if not review_list:
        review_list = [
            {"q": "\"Weekend live classes fit perfectly around my job. The electives were genuinely hands-on.\"", "a": "— Sneha Kulkarni, Online MBA (2024)"},
            {"q": "\"The capstone project with an industry mentor was the highlight — it became the centerpiece of my promotion case.\"", "a": "— Rohit Verma, Online MBA (2023)"},
            {"q": "\"Transparent fees, easy EMI, responsive support team. Exactly what I needed as a working parent.\"", "a": "— Deepa Krishnan, Online MBA (2025)"}
        ]
    ctx["reviews_json"] = json.dumps(review_list, ensure_ascii=False)
    
    # 9. FAQs
    faqs_raw = ctx.get("faqs") or resolve_list(raw_dict, knowledge, "faqs")
    if isinstance(faqs_raw, str):
        faqs_raw = [{"question": faqs_raw, "answer": ""}]
    elif isinstance(faqs_raw, list):
        new_fq = []
        for f in faqs_raw:
            if isinstance(f, str):
                new_fq.append({"question": f, "answer": ""})
            elif isinstance(f, dict):
                new_fq.append(f)
        faqs_raw = new_fq
    faq_list = [
        {
            "q": f.get("q") or f.get("question", ""),
            "a": f.get("a") or f.get("answer", ""),
            "sign": "+",
            "disp": "none"
        }
        for f in faqs_raw
    ]
    if not faq_list:
        faq_list = [
            {"q": "Is the Online MBA equivalent to a regular MBA?", "a": "Yes. Under UGC regulations, online degrees from entitled universities are equivalent to on-campus degrees for employment and higher education.", "sign": "+", "disp": "none"},
            {"q": "When can I choose my specialization?", "a": "Specializations are selected at the end of year one, before semester 3 begins.", "sign": "+", "disp": "none"},
            {"q": "How are exams conducted?", "a": "Term-end exams are online and remotely proctored. Internal assignments contribute 30% and term-end exams 70% of your grade.", "sign": "+", "disp": "none"},
            {"q": "Is there any campus immersion?", "a": "Campus immersion is optional. Convocation is held on-campus, but no visit is mandatory.", "sign": "+", "disp": "none"},
            {"q": "Can I get a refund if I withdraw?", "a": "Refunds follow UGC's refund policy — a full refund is available within the notified withdrawal window after admission.", "sign": "+", "disp": "none"}
        ]
    ctx["faq_data_json"] = json.dumps(faq_list, ensure_ascii=False)
 
    # 10. Syllabus Semester 1 & 2 / Semester 3 & 4
    syllabus_years = parse_syllabus_html(ctx.get("syllabus") or resolve_field(raw_dict, knowledge, "syllabus_content", ""))
    if not syllabus_years:
        syllabus_years = [
            {
                "label": "Year I",
                "semesters": [
                    { "title": "Semester I", "subjects": ["Management Theory & Practice", "Organisational Behaviour", "Marketing Management", "Business Economics", "Financial Accounting & Analysis", "Information Systems for Managers"] },
                    { "title": "Semester II", "subjects": ["Business Communication", "Essentials of HRM", "Business Law", "Strategic Management", "Operations Management", "Decision Science & Analytics"] }
                ]
            },
            {
                "label": "Year II",
                "semesters": [
                    { "title": "Semester III (Specialization Electives)", "subjects": ["Specialization Course I", "Specialization Course II", "Specialization Course III", "Research Methodology", "International Business", "Cost & Management Accounting"] },
                    { "title": "Semester IV (Specialization + Capstone)", "subjects": ["Specialization Course IV", "Specialization Course V", "Business Ethics & CSR", "Entrepreneurship", "Capstone Project"] }
                ]
            }
        ]
    ctx["syllabus_years_json"] = json.dumps(syllabus_years, ensure_ascii=False)
 
    # Specialization specific other specs list
    siblings = ctx.get("other_specs") or []
    other_specs_list = []
    hero_dict = ctx.get("hero") or {}
    stat_card = hero_dict.get("stat_card") or {}
    hero_title = hero_dict.get("title") or ""
    stat_value = stat_card.get("value") or ""
    current_slug = ctx.get("slug") or ""
    
    other_specs_list.append({
        "name": hero_title,
        "fee": clean_fee(stat_value),
        "cur": True,
        "href": "",
        "slug": current_slug
    })
    for s in siblings:
        other_specs_list.append({
            "name": s.get("name") or "",
            "fee": clean_fee(s.get("fee") or ""),
            "cur": False,
            "href": f"{s.get('slug')}.html" if s.get('slug') else "",
            "slug": s.get("slug") or ""
        })
    if len(other_specs_list) <= 1:
        other_specs_list = resolve_list(raw_dict, knowledge, "other_specs")
        if other_specs_list:
            other_specs_list = [
                {
                    "name": s.get("name") or s.get("other_spec_name") or "",
                    "fee": clean_fee(s.get("fee") or ""),
                    "cur": False,
                    "href": f"{s.get('slug')}.html" if s.get('slug') else "",
                    "slug": s.get("slug") or ""
                }
                for s in other_specs_list
            ]
        else:
            other_specs_list = [
                {"name": "Marketing Management", "fee": "₹2,00,000", "cur": True, "href": "", "slug": ""},
                {"name": "Financial Management", "fee": "₹2,00,000", "cur": False, "href": "", "slug": ""},
                {"name": "Human Resource Management", "fee": "₹2,00,000", "cur": False, "href": "", "slug": ""},
                {"name": "Operations & Supply Chain", "fee": "₹2,00,000", "cur": False, "href": "", "slug": ""},
                {"name": "Business Analytics", "fee": "₹2,16,000", "cur": False, "href": "", "slug": ""},
                {"name": "IT & Systems Management", "fee": "₹2,00,000", "cur": False, "href": "", "slug": ""},
                {"name": "International Business", "fee": "₹2,08,000", "cur": False, "href": "", "slug": ""}
            ]
    ctx["other_specs_json"] = json.dumps(other_specs_list, ensure_ascii=False)
    other_specs_formatted = []
    for i, item in enumerate(other_specs_list):
        cur = item.get("cur", False)
        name = f"{item['name']} (you are here)" if cur else item["name"]
        other_specs_formatted.append({
            "name": name,
            "fee": item.get("fee") or "Contact for fee",
            "cur": cur,
            "href": item.get("href") or "",
            "bg": "#FFF0EB" if cur else ("#F6F4FB" if i % 2 == 1 else "#fff"),
            "weight": "700" if cur else "400",
            "color": "#1C1B22" if cur else "#434346",
            "bt": "2px solid #FF5C35" if cur else "none",
            "bb": "2px solid #FF5C35" if cur else "1px solid #E9E5F2",
            "padding": "11px 14px" if cur else "0"
        })
    ctx["otherSpecs"] = other_specs_formatted
    ctx["other_specs"] = other_specs_formatted
 
 
    # University specific features, recruiters, financing, testimonials
    features_list = resolve_list(raw_dict, knowledge, "features")
    if not features_list:
        features_list = [
            {"stat": "Live", "t": "Weekend Classes", "d": "Plus lifetime access to all recordings on the LMS."},
            {"stat": "120+", "t": "Expert Faculty", "d": "Learn from academics and industry practitioners."},
            {"stat": "4 Sem", "t": "Capstone Project", "d": "Industry-mentored capstone to apply your skills."},
            {"stat": "24 months", "t": "No-cost EMI", "d": "Flexible fee plans starting from ₹8,334 per month."}
        ]
    ctx["features_json"] = json.dumps(features_list, ensure_ascii=False)
    
    recruiters_list = resolve_list(raw_dict, knowledge, "recruiters")
    if not recruiters_list:
        recruiters_list = ["Tata", "Indiamart", "Wockhardt", "Zalaris", "Milkbasket", "Shopx"]
    ctx["recruiters_json"] = json.dumps(recruiters_list, ensure_ascii=False)
    
    # testimonials is reviews mapped for homepage
    testimonials = []
    for r in review_list:
        testimonials.append({
            "q": r["q"],
            "name": r["a"].replace("—", "").split(",")[0].strip(),
            "role": r["a"].replace("—", "").split(",")[1].strip() if "," in r["a"] else "Online MBA",
            "initial": r["a"].replace("—", "").strip()[0].upper() if r["a"] else "S"
        })
    ctx["testimonials_json"] = json.dumps(testimonials, ensure_ascii=False)
    
    # financing for homepage
    financing_list = resolve_list(raw_dict, knowledge, "financing")
    if not financing_list:
        financing_list = [
            {"stat": "₹8,334", "t": "No-cost EMI", "d": "Flexible plans starting from ₹8,334 per month."},
            {"stat": "3–12 months", "t": "EMI tenures", "d": "Choose a 3, 6, 9 or 12-month repayment plan."},
            {"stat": "20% off", "t": "Defence scholarship", "d": "For armed forces personnel & their family."}
        ]
    ctx["financing_json"] = json.dumps(financing_list, ensure_ascii=False)
    
    banks_list = resolve_list(raw_dict, knowledge, "banks")
    if not banks_list:
        banks_list = ['HDFC', 'ICICI', 'Axis', 'Citi', 'Standard Chartered', 'HSBC', 'Kotak Mahindra']
    ctx["banks_json"] = json.dumps(banks_list, ensure_ascii=False)

    # Programs list for homepage (enriched from workspace courses if available)
    workspace_courses = raw_dict.get("_workspace_courses") or []
    if workspace_courses:
        uni_programs = []
        for i, c in enumerate(workspace_courses):
            data = c.get("data", {}) if isinstance(c, dict) else {}
            slug = c.get("slug", "") if isinstance(c, dict) else ""
            
            # Determine dynamic level based on course title
            name_lower = (data.get("program_name") or data.get("course_name") or slug).lower()
            is_undergrad = any(x in name_lower for x in ["bba", "bca", "bcom", "bsc", "ba "]) or name_lower.startswith("ba-") or name_lower.startswith("ba ")
            level = "Undergraduate" if is_undergrad else "Postgraduate"
            
            uni_programs.append({
                "level": level,
                "name": data.get("program_name") or data.get("course_name") or slug.replace("-", " ").title(),
                "dur": data.get("duration") or "2 Years · 4 Sem",
                "fee": clean_fee(data.get("total_fee") or data.get("starting_fee") or "") or "₹2,00,000",
                "feeUnit": "total course",
                "d": data.get("hero_description") or "Industry-aligned specializations, taught by expert faculty.",
                "href": f"{slug}.html",
                "featured": i == 0,
                "mode": data.get("mode") or "100% Online",
            })
    else:
        dur_val = resolve_field({}, knowledge, "duration", "2 Years · 4 Sem")
        fee_val = (ctx.get("sticky_bar") or {}).get("fee") or clean_fee(resolve_field({}, knowledge, "starting_fee", "")) or "₹2,00,000"
        mode_val = resolve_field({}, knowledge, "mode", "100% Online")
        uni_programs = [
            {"level": "Postgraduate", "name": "Online MBA", "dur": dur_val, "fee": fee_val, "feeUnit": "total course", "elig": "Bachelor's, 50%", "d": "Seven industry-aligned specializations, taught by expert faculty.", "href": ctx["course_href"], "featured": True, "mode": mode_val}
        ]

    # Map mk(p) styling attributes for homepage cards
    for p in uni_programs:
        f = bool(p.get("featured"))
        p["cardStyle"] = 'background:#6B4FC9;border:1px solid #6B4FC9' if f else 'background:#fff;border:1px solid #E9E5F2'
        p["nameColor"] = '#fff' if f else '#1C1B22'
        p["descColor"] = '#D9D2F2' if f else '#6E6A78'
        p["metaLabel"] = '#EAE7FD' if f else '#706A80'
        p["metaVal"] = '#fff' if f else '#434346'
        p["divider"] = '1px solid rgba(255,255,255,.18)' if f else '1px solid #ECE7F5'
        p["feeUnitColor"] = '#EAE7FD' if f else '#706A80'
        p["badgeStyle"] = 'background:rgba(255,92,53,.18);color:#E04015' if f else 'background:#FFE7E0;color:#CC3910'

    ctx["programs_json"] = json.dumps(uni_programs[:4], ensure_ascii=False)

    # Serialized programs/specs data for listing templates
    programs_list_data = []
    for c in workspace_courses:
        if not isinstance(c, dict): continue
        data = c.get("data", {})
        slug = c.get("slug", "")
        programs_list_data.append({
            "name": data.get("program_name") or data.get("course_name") or slug.replace("-", " ").title(),
            "slug": slug,
            "fee": clean_fee(data.get("total_fee") or data.get("starting_fee") or ""),
            "duration": data.get("duration") or "2 Years",
            "eligibility": data.get("eligibility_summary") or "Bachelor's degree",
            "description": data.get("hero_description") or "",
            "mode": data.get("mode") or "100% Online",
        })
    ctx["programs_list_json"] = json.dumps(programs_list_data, ensure_ascii=False)

    # Spec groups for specializations listing page
    workspace_specs = raw_dict.get("_workspace_specs") or []
    spec_groups_map: dict = {}
    for sp in workspace_specs:
        if not isinstance(sp, dict): continue
        data = sp.get("data", {})
        sp_slug = sp.get("slug", "")
        parent = sp.get("parent_slug") or data.get("parent_slug") or "general"
        if parent not in spec_groups_map:
            # Find course name from workspace_courses
            course_name = parent.replace("-", " ").title()
            for c in workspace_courses:
                if isinstance(c, dict) and c.get("slug") == parent:
                    cd = c.get("data", {})
                    course_name = cd.get("program_name") or cd.get("course_name") or course_name
                    break
            spec_groups_map[parent] = {"course_name": course_name, "course_slug": parent, "specs": []}
        spec_groups_map[parent]["specs"].append({
            "name": data.get("spec_name") or sp_slug.replace("-", " ").title(),
            "slug": sp_slug,
            "fee": clean_fee(data.get("total_fee") or ""),
            "duration": data.get("duration") or "2 Years",
            "description": data.get("hero_description") or "",
        })
    ctx["spec_groups_json"] = json.dumps(list(spec_groups_map.values()), ensure_ascii=False)

    # Blog categories & posts
    ctx["cat_labels_json"] = json.dumps(['All', 'Career', 'Admissions', 'Guide', 'Finance', 'Student Life'], ensure_ascii=False)

    # Priority: workspace blogs (via transformer _workspace_blogs) → hardcoded demo fallback
    workspace_blogs_ctx = raw_dict.get("_workspace_blogs") or []
    blog_posts = []
    if workspace_blogs_ctx:
        for b in workspace_blogs_ctx:
            if not isinstance(b, dict):
                continue
            data = b.get("data", {})
            b_slug = b.get("slug", "")
            # Determine the blog page href — relative path to the blog detail HTML
            blog_href = f"{b_slug}.html"
            img_url = data.get("hero_image_url") or ""
            blog_posts.append({
                "tag": data.get("category") or data.get("tag") or "Article",
                "title": data.get("blog_title") or data.get("title") or b_slug.replace("-", " ").title(),
                "excerpt": data.get("hero_description") or data.get("excerpt") or "",
                "meta": data.get("read_time") or data.get("meta") or "",
                "href": blog_href,
                "image": img_url,
                "hero_image_url": img_url,
            })
    else:
        # Demo fallback — only shown when workspace contains no blogs
        blog_posts = [
            {"tag": "Guide", "title": "How to choose the right MBA specialization", "excerpt": "Marketing, finance, HR or analytics? A practical framework to match a track to your goals and background.", "meta": "6 min · Dec 2025", "href": "#", "image": "", "hero_image_url": ""},
            {"tag": "Finance", "title": "Online MBA fees & EMI options, fully explained", "excerpt": "Semester-wise, annual and one-time plans compared — plus how no-cost EMI actually works.", "meta": "5 min · Dec 2025", "href": "#", "image": "", "hero_image_url": ""},
            {"tag": "Admissions", "title": f"{uni_name} Online MBA eligibility & admission, step by step", "excerpt": "Documents, deadlines and the exact portal flow — everything you need before you apply.", "meta": "7 min · Nov 2025", "href": "#", "image": "", "hero_image_url": ""},
        ]
    ctx["posts"] = blog_posts[:3]
    ctx["blog_posts"] = blog_posts
    ctx["all_posts_json"] = json.dumps(blog_posts, ensure_ascii=False)

    # Contact details — sourced from the workspace-aware site config (see
    # core/site_config.get_site_config); no hardcoded NMIMS fallback here,
    # since that previously leaked NMIMS's email/address onto every other
    # university's page whenever their own contact info wasn't set.
    ctx["details_json"] = json.dumps([
        {"icon": "✉", "k": "Email", "v": (ctx.get("site") or {}).get("email") or ""},
        {"icon": "⌖", "k": "Visit", "v": (ctx.get("site") or {}).get("address") or ""}
    ], ensure_ascii=False)

    # For V2 rendering compatibility: populate lists directly on the context
    ctx["features"] = features_list
    ctx["recruiters"] = recruiters_list
    ctx["testimonials"] = testimonials
    ctx["financing"] = financing_list
    ctx["banks"] = banks_list
    ctx["programs"] = uni_programs if page_type == "university" else programs_list_data
    if page_type == "university":
        processed_steps = []
        for idx, s in enumerate(steps_list):
            num_str = str(idx + 1)
            t = f"Step {num_str}"
            d = s.get("t", "")
            
            parts = re.split(r"[:\.]", d, maxsplit=1)
            if len(parts) > 1 and len(parts[0]) < 30:
                sliced_d = d[len(parts[0]) + 1:].strip()
                if sliced_d:
                    t = parts[0].strip()
                    d = sliced_d
                    
            processed_steps.append({
                "n": num_str.zfill(2),
                "t": t,
                "d": d
            })
        ctx["admission"] = processed_steps
    else:
        ctx["admission"] = ctx.get("admission")
    ctx["steps"] = steps_list
    ctx["highlights"] = h_list
    ctx["fees"] = fee_list
    ctx["jobs"] = job_list
    ctx["reviews"] = review_list
    ctx["faqs"] = faq_list
    
    # Syllabus tabs formatting for course and specialization details
    if page_type in ("course", "specialization"):
        syllabus_tabs_data = []
        for idx, y in enumerate(syllabus_years):
            active = (idx == 0)
            syllabus_tabs_data.append({
                "label": y.get("label", ""),
                "bg": "#6B4FC9" if active else "#fff",
                "color": "#fff" if active else "#6E6A78",
                "border": "#6B4FC9" if active else "#E9E5F2"
            })
        ctx["syllabusTabs"] = syllabus_tabs_data
        ctx["syllabus_years"] = syllabus_years
        
        sems_data = []
        for y in syllabus_years:
            for sem in y.get("semesters", []):
                sems_data.append(sem)
        ctx["sems"] = sems_data

    if page_type == "specializations_listing":
        specs_data = []
        for sp in workspace_specs:
            if not isinstance(sp, dict): continue
            data = sp.get("data", {})
            sp_slug = sp.get("slug", "")
            parent = sp.get("parent_slug") or data.get("parent_slug") or "general"
            course_name = parent.replace("-", " ").title()
            for c in workspace_courses:
                if isinstance(c, dict) and c.get("slug") == parent:
                    cd = c.get("data", {})
                    course_name = cd.get("program_name") or cd.get("course_name") or course_name
                    break
            specs_data.append({
                "slug": sp_slug,
                "course_name": course_name,
                "name": data.get("spec_name") or sp_slug.replace("-", " ").title(),
                "description": data.get("hero_description") or data.get("description") or "",
                "fee": clean_fee(data.get("total_fee") or data.get("starting_fee") or ""),
            })
        ctx["specs"] = specs_data

    # Map specs for the homepage as well (adding default icon support for the layout grid)
    if page_type == "university":
        for sp in ctx.get("specs") or []:
            if isinstance(sp, dict) and "icon" not in sp:
                sp["icon"] = "◑"

    # Default whiteHero styling parameters
    ctx["heroWrap"] = 'background:#fff;border-bottom:1px solid #ECE8F6;color:#434346'
    ctx["heroH1"] = '#5737C5'
    ctx["heroSub"] = '#6E6A78'
    ctx["heroBadge"] = 'background:#FFF0EB;border:1px solid #FFD3C6;color:#E0431F'
    ctx["heroSecBtn"] = 'border:1.5px solid #D9CFF0;color:#5737C5'
    ctx["heroStatLabel"] = '#6E6A78'
    ctx["heroStatDivider"] = '#ECE8F6'
    ctx["heroImg"] = 'background:repeating-linear-gradient(135deg,#EFEBF8,#EFEBF8 14px,#E4DEF4 14px,#E4DEF4 28px);border:1px solid #E9E5F2'
    ctx["heroImgText"] = '#A99BD8'
    ctx["heroCrumb"] = '#9A93A8'
    ctx["heroChip"] = 'background:#F6F4FB;border:1px solid #E9E5F2;color:#5737C5'

    ctx["ctx_json"] = json.dumps(ctx, default=str)
    ctx["standalone"] = standalone  # controls nav/footer visibility in templates
    template_name = TEMPLATE_MAP.get(resolved["page_type"], f"{resolved['page_type']}.html")
    
    if render_mode == "v2":
        template = env_v2.get_template(template_name)
    else:
        template = env.get_template(template_name)
        
    return clean_html_tables(template.render(**ctx))
