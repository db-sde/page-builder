from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.router import get_transformer
import os
from pathlib import Path
import json
import re
from html.parser import HTMLParser

# TODO: add Redis caching layer here — render_resolved should check cache before re-rendering

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)

# Custom filter — strips None safely for templates
def default_empty(value):
    return value if value is not None else ""

env.filters["de"] = default_empty

def clean_fee(amount_str: str) -> str:
    if not amount_str:
        return ""
    s = str(amount_str).strip()
    if not s or s.upper() in ("NA", "N/A", "NIL", "FREE", "-", "--"):
        return ""
    if s.startswith("₹"):
        return s
    # Strip INR prefix (case-insensitive)
    s = re.sub(r'^INR\s*', '', s, flags=re.IGNORECASE).strip()
    # Strip trailing garbage: /-, /--, /year, /sem etc
    s = re.sub(r'\s*/[-–]+.*$', '', s).strip()
    s = re.sub(r'\s*/\s*(year|sem|semester|month|mo).*$', '', s, flags=re.IGNORECASE).strip()
    # Strip any non-numeric/comma/dot characters remaining at end
    s = re.sub(r'[^0-9,.].*$', '', s).strip()
    if not s:
        return ""
    return f"₹{s}"

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
        self.y1 = []
        self.y2 = []
        self.current_year = 1
        self.current_sem = None
        self.in_heading = False
        self.in_li = False
        self.heading_text = ""
        self.li_text = ""

    def handle_starttag(self, tag, attrs):
        if tag in ("h3", "h4", "h5"):
            self.in_heading = True
            self.heading_text = ""
        elif tag == "li":
            self.in_li = True
            self.li_text = ""

    def handle_endtag(self, tag):
        if tag in ("h3", "h4", "h5"):
            self.in_heading = False
            text = self.heading_text.strip()
            if text:
                # Check year
                if re.search(r"year\s*(i\b|1\b|one)", text, re.IGNORECASE):
                    self.current_year = 1
                elif re.search(r"year\s*(ii\b|2\b|two)", text, re.IGNORECASE):
                    self.current_year = 2
                # Check sem
                elif re.search(r"sem(ester)?\s*(i\b|1\b|one)", text, re.IGNORECASE):
                    self.current_sem = {"title": text, "subjects": []}
                    if self.current_year == 1:
                        self.y1.append(self.current_sem)
                    else:
                        self.y2.append(self.current_sem)
                elif re.search(r"sem(ester)?\s*(ii\b|2\b|two)", text, re.IGNORECASE):
                    self.current_sem = {"title": text, "subjects": []}
                    if self.current_year == 1:
                        self.y1.append(self.current_sem)
                    else:
                        self.y2.append(self.current_sem)
                elif re.search(r"sem(ester)?\s*(iii\b|3\b|three)", text, re.IGNORECASE):
                    self.current_sem = {"title": text, "subjects": []}
                    self.y2.append(self.current_sem)
                elif re.search(r"sem(ester)?\s*(iv\b|4\b|four)", text, re.IGNORECASE):
                    self.current_sem = {"title": text, "subjects": []}
                    self.y2.append(self.current_sem)
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

def parse_syllabus_html(html_str: str) -> tuple[list, list]:
    if not html_str:
        return [], []
    parser = SyllabusHTMLParser()
    try:
        parser.feed(html_str)
        return parser.y1, parser.y2
    except Exception:
        return [], []

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


def process_admission_steps(raw_steps):
    processed = []
    
    def is_numbered_step(s):
        import re
        return bool(re.match(r'^(Step\s*\d+|\d+[\.\s:]+)', s.strip(), re.IGNORECASE))
        
    i = 0
    n_steps = len(raw_steps)
    while i < n_steps:
        s = raw_steps[i]
        text = s.get("t", "").strip()
        
        if text.endswith(':') and len(text) < 40:
            header_title = text[:-1].strip()
            bullets = []
            j = i + 1
            while j < n_steps:
                next_item = raw_steps[j]
                next_text = next_item.get("t", "")
                if is_numbered_step(next_text):
                    break
                bullets.append(next_text.strip())
                j += 1
            if bullets:
                processed.append({
                    "n": str(len(processed) + 1).zfill(2),
                    "t": header_title,
                    "d": "\n".join("• " + b for b in bullets)
                })
                i = j
                continue
                
        # Standard splitting logic
        t = f"Step {s.get('n', '')}"
        d = text
        parts = re.split(r'[:\.]', text, maxsplit=1)
        if len(parts) > 1 and len(parts[0]) < 30:
            sliced_d = parts[1].strip()
            if sliced_d:
                t = parts[0].strip()
                d = sliced_d
                
        processed.append({
            "n": str(len(processed) + 1).zfill(2),
            "t": t,
            "d": d
        })
        i += 1
        
    return processed


def render_resolved(resolved: dict, standalone: bool = False) -> str:
    transformer = get_transformer(resolved)
    ctx = transformer.transform()    # Phase 3 — Context Extraction
    raw_dict = resolved.get("raw") or {}
    
    # 1. University Display Name
    uni_name = None
    if ctx.get("university_name"):
        uni_name = ctx["university_name"]
    elif raw_dict.get("university_name"):
        uni_name = raw_dict["university_name"]
    elif raw_dict.get("name") and resolved.get("page_type") == "university":
        uni_name = raw_dict["name"]
    else:
        uni_name = raw_dict.get("university_full_name") or resolved.get("university_slug", "nmims").upper()
        
    logo_letter = uni_name[0].upper() if uni_name else "N"
    
    uni_slug = resolved.get("university_slug") or "nmims"
    page_type = resolved.get("page_type", "course")
    course_slug = resolved.get("parent_slug") or resolved.get("slug") or ""

    ctx["university_name"] = uni_name
    ctx["university_letter"] = logo_letter

    branding_logo = ""
    branding_favicon = ""
    meta_path = Path("/Users/aryankinha/Documents/Degree/temp/acfTOhtml copy/backend/workspaces") / uni_slug / "metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_json = json.load(f)
                branding = meta_json.get("branding") or {}
                branding_logo = branding.get("logo") or ""
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
    ctx["highlights"] = h_list
    
    # 4. Specs (items)
        # ONLY use real workspace specializations filtered by parent_course_slug.
    # No fallback to raw specialization field or hardcoded placeholders.
    if page_type != "specializations_listing":
        workspace_specs_ctx = ctx.get("_workspace_specs") or []
        workspace_courses = raw_dict.get("_workspace_courses") or []
        spec_list = []
        for sp in workspace_specs_ctx[:6]:
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
        spec_icons = ['◑', '◧', '◴']
        for idx, sp in enumerate(spec_list):
            sp["icon"] = spec_icons[idx % len(spec_icons)]
        ctx["specs_json"] = json.dumps(spec_list, ensure_ascii=False)
        ctx["specs"] = spec_list
    
    # 5. Fees
    fee_plans = (ctx.get("fees") or {}).get("plans", []) or []
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
    ctx["fees"] = fee_list
    
    # 6. Admission Steps
    steps_list = parse_admission_html((ctx.get("admission") or {}).get("steps") if ctx.get("admission") else "")
    if steps_list:
        steps_list = process_admission_steps(steps_list)
    else:
        steps_list = [
            {"n": "01", "t": "Register on the university portal", "d": "Verify your mobile number and email to create your student account."},
            {"n": "02", "t": "Complete application form", "d": "Fill in your personal, professional, and academic details."},
            {"n": "03", "t": "Upload required documents", "d": "Upload copies of graduation marksheets, ID proof, and a photo."},
            {"n": "04", "t": "Pay the first installment", "d": "Pay the enrollment/course fee online to start your learning journey."}
        ]
    ctx["steps_json"] = json.dumps(steps_list, ensure_ascii=False)
    ctx["admission_steps"] = steps_list
    
    # 7. Job profiles
    jobs_raw = ctx.get("jobs", []) or []
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
    ctx["jobs"] = job_list
    
    # 8. Reviews
    reviews_raw = ctx.get("reviews", []) or []
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
    ctx["reviews"] = review_list
    
    # 9. FAQs
    faqs_raw = ctx.get("faqs", []) or []
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
            "a": f.get("a") or f.get("answer", "")
        }
        for f in faqs_raw
    ]
    if not faq_list:
        faq_list = [
            {"q": "Is the Online MBA equivalent to a regular MBA?", "a": "Yes. Under UGC regulations, online degrees from entitled universities are equivalent to on-campus degrees for employment and higher education."},
            {"q": "When can I choose my specialization?", "a": "Specializations are selected at the end of year one, before semester 3 begins."},
            {"q": "How are exams conducted?", "a": "Term-end exams are online and remotely proctored. Internal assignments contribute 30% and term-end exams 70% of your grade."},
            {"q": "Is there any campus immersion?", "a": "Campus immersion is optional. Convocation is held on-campus, but no visit is mandatory."},
            {"q": "Can I get a refund if I withdraw?", "a": "Refunds follow UGC's refund policy — a full refund is available within the notified withdrawal window after admission."}
        ]
    ctx["faq_data_json"] = json.dumps(faq_list, ensure_ascii=False)
    ctx["faqs"] = faq_list

    # 10. Syllabus Semester 1 & 2 / Semester 3 & 4
    y1, y2 = parse_syllabus_html(ctx.get("syllabus", ""))
    if not y1 and not y2:
        y1 = [
            { "title": "Semester 1", "subjects": ["Management Theory & Practice", "Organisational Behaviour", "Marketing Management", "Business Economics", "Financial Accounting & Analysis", "Information Systems for Managers"] },
            { "title": "Semester 2", "subjects": ["Business Communication", "Essentials of HRM", "Business Law", "Strategic Management", "Operations Management", "Decision Science & Analytics"] }
        ]
        y2 = [
            { "title": "Semester 3 (Specialization Electives)", "subjects": ["Specialization Course I", "Specialization Course II", "Specialization Course III", "Research Methodology", "International Business", "Cost & Management Accounting"] },
            { "title": "Semester 4 (Specialization + Capstone)", "subjects": ["Specialization Course IV", "Specialization Course V", "Business Ethics & CSR", "Entrepreneurship", "Capstone Project"] }
        ]
    ctx["y1_json"] = json.dumps(y1, ensure_ascii=False)
    ctx["y2_json"] = json.dumps(y2, ensure_ascii=False)
    ctx["y1"] = y1
    ctx["y2"] = y2

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
        other_specs_list = [
            {"name": "Marketing Management", "fee": "₹2,00,000", "cur": True, "href": "", "slug": ""},
            {"name": "Financial Management", "fee": "₹2,00,000", "cur": False, "href": "", "slug": ""},
            {"name": "Human Resource Management", "fee": "₹2,00,000", "cur": False, "href": "", "slug": ""},
            {"name": "Operations & Supply Chain", "fee": "₹2,00,000", "cur": False, "href": "", "slug": ""},
            {"name": "Business Analytics", "fee": "₹2,16,000", "cur": False, "href": "", "slug": ""},
            {"name": "IT & Systems Management", "fee": "₹2,00,000", "cur": False, "href": "", "slug": ""},
            {"name": "International Business", "fee": "₹2,08,000", "cur": False, "href": "", "slug": ""}
        ]

    for i, item in enumerate(other_specs_list):
        cur = (item["slug"] == current_slug) if (item.get("slug") and current_slug) else item.get("cur", False)
        name = f"{item['name']} (you are here)" if cur else item['name']
        item.update({
            "name": name,
            "cur": cur,
            "bg": '#FFF0EB' if cur else ('#F6F4FB' if i % 2 else '#fff'),
            "weight": '700' if cur else '400',
            "color": '#1C1B22' if cur else '#434346',
            "bt": '2px solid #FF5C35' if cur else 'none',
            "bb": '2px solid #FF5C35' if cur else '1px solid #E9E5F2',
            "padding": '11px 14px' if cur else '0'
        })
    ctx["other_specs_json"] = json.dumps(other_specs_list, ensure_ascii=False)
    ctx["other_specs"] = other_specs_list


    # University specific features, recruiters, financing, testimonials
    features_list = [
        {"stat": "Live", "t": "Weekend Classes", "d": "Plus lifetime access to all recordings on the LMS."},
        {"stat": "120+", "t": "Expert Faculty", "d": "Learn from academics and industry practitioners."},
        {"stat": "4 Sem", "t": "Capstone Project", "d": "Industry-mentored capstone to apply your skills."},
        {"stat": "24 Months", "t": "No-cost EMI", "d": "Flexible fee plans starting from ₹8,334 per month."}
    ]
    ctx["features_json"] = json.dumps(features_list, ensure_ascii=False)
    ctx["features"] = features_list

    recruiters_list = ['Deloitte', 'Amazon', 'HDFC', 'TCS', 'Accenture', 'HUL']
    ctx["recruiters_json"] = json.dumps(recruiters_list, ensure_ascii=False)
    ctx["recruiters"] = recruiters_list
    
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
    ctx["testimonials"] = testimonials
    
    # financing for homepage
    financing_list = [
        {"stat": "₹8,334", "t": "No-cost EMI", "d": "Flexible plans starting from ₹8,334 per month."},
        {"stat": "3–12 Months", "t": "EMI tenures", "d": "Choose a 3, 6, 9 or 12-month repayment plan."},
        {"stat": "20% off", "t": "Defence scholarship", "d": "For armed forces personnel & their family."}
    ]
    ctx["financing_json"] = json.dumps(financing_list, ensure_ascii=False)
    ctx["financing"] = financing_list

    banks_list = ['HDFC', 'ICICI', 'Axis', 'Citi', 'Standard Chartered', 'HSBC', 'Kotak Mahindra']
    ctx["banks_json"] = json.dumps(banks_list, ensure_ascii=False)
    ctx["banks"] = banks_list

    # Programs list for homepage (enriched from workspace courses if available)
    workspace_courses = raw_dict.get("_workspace_courses") or []
    if workspace_courses:
        uni_programs = []
        for i, c in enumerate(workspace_courses):
            data = c.get("data", {}) if isinstance(c, dict) else {}
            slug = c.get("slug", "") if isinstance(c, dict) else ""
            uni_programs.append({
                "level": "Postgraduate",
                "name": data.get("program_name") or data.get("course_name") or slug.replace("-", " ").title(),
                "dur": data.get("duration") or "2 Years · 4 Sem",
                "fee": data.get("total_fee") or data.get("starting_fee") or "₹2,00,000",
                "feeUnit": "total course",
                "elig": data.get("eligibility_summary") or "Bachelor's, 50%",
                "d": data.get("hero_description") or "Industry-aligned specializations, taught by expert faculty.",
                "href": f"{slug}.html",
                "featured": i == 0,
            })
    else:
        uni_programs = [
            {"level": "Postgraduate", "name": "Online MBA", "dur": "2 Years · 4 Sem", "fee": (ctx.get("sticky_bar") or {}).get("fee") or "₹2,00,000", "feeUnit": "total course", "elig": "Bachelor's, 50%", "d": "Seven industry-aligned specializations, taught by expert faculty.", "href": ctx["course_href"], "featured": True}
        ]

    uni_programs_enriched = []
    for p in uni_programs:
        p_copy = dict(p)
        f = p_copy.get("featured", False)
        p_copy.update({
            "cardStyle": "background:#6B4FC9;border:1px solid #6B4FC9" if f else "background:#fff;border:1px solid #E9E5F2",
            "nameColor": "#fff" if f else "#1C1B22",
            "descColor": "#D9D2F2" if f else "#6E6A78",
            "metaLabel": "#C9BEEC" if f else "#9A93A8",
            "metaVal": "#fff" if f else "#434346",
            "divider": "1px solid rgba(255,255,255,.18)" if f else "1px solid #ECE7F5",
            "feeUnitColor": "#C9BEEC" if f else "#9A93A8",
            "badgeStyle": "background:rgba(255,92,53,.18);color:#FF5C35" if f else "background:#FFE7E0;color:#E0431F"
        })
        uni_programs_enriched.append(p_copy)

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

    if page_type == "programs_listing":
        ctx["programs"] = programs_list_data
    else:
        ctx["programs"] = uni_programs_enriched[:4]

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

    listing_specs = []
    for grp in spec_groups_map.values():
        c_name = grp["course_name"]
        for sp in grp["specs"]:
            listing_specs.append({
                "course_name": c_name,
                "name": sp["name"],
                "description": sp["description"],
                "fee": sp["fee"],
                "slug": sp["slug"]
            })
    if page_type == "specializations_listing":
        ctx["specs"] = listing_specs

    # Blog categories & posts
    ctx["cat_labels_json"] = json.dumps(['All', 'Career', 'Admissions', 'Guide', 'Finance', 'Student Life'], ensure_ascii=False)

    # Priority: workspace blogs (via transformer _workspace_blogs) → hardcoded demo fallback
    workspace_blogs_ctx = ctx.get("_workspace_blogs") or raw_dict.get("_workspace_blogs") or []
    blog_posts = []
    if workspace_blogs_ctx:
        for b in workspace_blogs_ctx:
            if not isinstance(b, dict):
                continue
            data = b.get("data", {})
            b_slug = b.get("slug", "")
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
                "author": data.get("author") or "Admissions Team",
                "author_initial": (data.get("author") or "Admissions Team").strip()[0].upper()
            })
    else:
        # Demo fallback — only shown when workspace contains no blogs
        blog_posts = [
            {"tag": "Guide", "title": "How to choose the right MBA specialization", "excerpt": "Marketing, finance, HR or analytics? A practical framework to match a track to your goals and background.", "meta": "6 min · Dec 2025", "href": "#", "image": "", "hero_image_url": "", "author": "Admissions Team", "author_initial": "A"},
            {"tag": "Finance", "title": "Online MBA fees & EMI options, fully explained", "excerpt": "Semester-wise, annual and one-time plans compared — plus how no-cost EMI actually works.", "meta": "5 min · Dec 2025", "href": "#", "image": "", "hero_image_url": "", "author": "Admissions Team", "author_initial": "A"},
            {"tag": "Admissions", "title": f"{uni_name} Online MBA eligibility & admission, step by step", "excerpt": "Documents, deadlines and the exact portal flow — everything you need before you apply.", "meta": "7 min · Nov 2025", "href": "#", "image": "", "hero_image_url": "", "author": "Admissions Team", "author_initial": "A"},
        ]
    ctx["all_posts_json"] = json.dumps(blog_posts, ensure_ascii=False)

    if page_type == "blog_listing":
        if blog_posts:
            ctx["featured_post"] = blog_posts[0]
            ctx["blog_posts"] = blog_posts[1:]
        else:
            ctx["featured_post"] = None
            ctx["blog_posts"] = []
    else:
        ctx["blog_posts"] = blog_posts
        ctx["posts"] = blog_posts[:3]

    # Contact details
    ctx["details_json"] = json.dumps([
        {"icon": "✉", "k": "Email", "v": (ctx.get("site") or {}).get("email") or "admissions@nmimsonline.edu"},
        {"icon": "⌖", "k": "Visit", "v": (ctx.get("site") or {}).get("address") or "V. L. Mehta Road, Vile Parle (W), Mumbai 400056"}
    ], ensure_ascii=False)

    ctx["ctx_json"] = json.dumps(ctx, default=str)
    ctx["standalone"] = standalone  # controls nav/footer visibility in templates
    template_name = TEMPLATE_MAP.get(resolved["page_type"], f"{resolved['page_type']}.html")
    template = env.get_template(template_name)
    return template.render(**ctx)
