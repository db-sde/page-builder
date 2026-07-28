from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.router import get_transformer
from core.utils import build_public_route, build_public_url, format_fee as clean_fee
from workspace.manager import WORKSPACES_ROOT
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

from jinja2 import pass_context
from PIL import Image

# Custom filter — strips None safely for templates
def default_empty(value):
    return value if value is not None else ""

env.filters["de"] = default_empty

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

env.filters["webp_variant"] = webp_variant_filter
env.filters["image_width"] = image_width_filter
env.filters["image_height"] = image_height_filter

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
    "contact": "contact.html",
}


def _plain_text(value) -> str:
    """Collapse simple HTML content to plain text for JSON-LD values."""
    if value is None:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()


def _schema_price(value) -> str:
    """Extract an INR numeric price without inventing a value."""
    match = re.search(r"\d[\d,]*(?:\.\d+)?", str(value or ""))
    return match.group(0).replace(",", "") if match else ""


def _build_structured_data(ctx: dict, resolved: dict, raw: dict, primary_domain: str) -> list[dict]:
    """Build reusable, page-appropriate structured data from rendered content."""
    page_type = resolved.get("page_type") or ""
    slug = resolved.get("slug") or ""
    university_slug = resolved.get("university_slug") or ""
    canonical_url = ctx.get("canonical_url") or build_public_url(
        primary_domain,
        build_public_route(page_type, slug, university_slug),
        is_homepage=(page_type == "university"),
    )
    homepage_url = build_public_url(primary_domain, "/", is_homepage=True)
    university_name = (
        raw.get("university_name")
        or ctx.get("university_name")
        or university_slug.replace("-", " ").title()
    )
    graph: list[dict] = []

    if page_type == "university":
        organization = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{homepage_url}#organization",
            "name": university_name,
            "url": homepage_url,
        }
        logo = ctx.get("branding_logo") or ""
        if logo:
            organization["logo"] = build_public_url(primary_domain, logo)
        graph.append(organization)

    page_name = (
        raw.get("program_name")
        or raw.get("course_name")
        or raw.get("spec_name")
        or raw.get("title")
        or ctx.get("seo_title")
        or slug.replace("-", " ").title()
    )

    crumbs = [{"name": "Home", "url": homepage_url}]
    if page_type == "blog_listing":
        crumbs.append({"name": "Blog", "url": canonical_url})
    elif page_type == "programs_listing":
        crumbs.append({"name": "Programs", "url": canonical_url})
    elif page_type == "specializations_listing":
        crumbs.append({"name": "Specializations", "url": canonical_url})
    elif page_type == "contact":
        crumbs.append({"name": "Contact", "url": canonical_url})
    elif page_type == "blog":
        crumbs.append({
            "name": "Blog",
            "url": build_public_url(primary_domain, build_public_route("blog_listing")),
        })
        crumbs.append({"name": page_name, "url": canonical_url})
    elif page_type == "course":
        crumbs.append({
            "name": "Programs",
            "url": build_public_url(primary_domain, build_public_route("programs_listing")),
        })
        crumbs.append({"name": page_name, "url": canonical_url})
    elif page_type == "specialization":
        parent_slug = resolved.get("parent_slug") or ""
        parent = raw.get("_workspace_parent") or {}
        parent_data = parent.get("data") or {}
        parent_name = (
            parent_data.get("program_name")
            or parent_data.get("course_name")
            or parent_slug.replace("-", " ").title()
        )
        if parent_slug:
            crumbs.append({
                "name": parent_name,
                "url": build_public_url(
                    primary_domain,
                    build_public_route("course", parent_slug, university_slug),
                ),
            })
        crumbs.append({"name": page_name, "url": canonical_url})

    graph.append({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "name": crumb["name"],
                "item": crumb["url"],
            }
            for position, crumb in enumerate(crumbs, start=1)
        ],
    })

    if page_type in ("course", "specialization"):
        course = {
            "@context": "https://schema.org",
            "@type": "Course",
            "@id": f"{canonical_url}#course",
            "url": canonical_url,
            "name": page_name,
            "description": _plain_text(raw.get("hero_description") or ctx.get("meta_description")),
            "provider": {
                "@type": "Organization",
                "name": university_name,
                "url": homepage_url,
            },
        }
        price = _schema_price(raw.get("total_fee") or raw.get("starting_fee"))
        if price:
            course["offers"] = {
                "@type": "Offer",
                "price": price,
                "priceCurrency": "INR",
                "url": canonical_url,
            }
        graph.append(course)

    faqs = ctx.get("faqs") or raw.get("faqs") or []
    faq_entities = []
    if page_type in ("course", "specialization", "blog"):
        for faq in faqs:
            if not isinstance(faq, dict):
                continue
            question = _plain_text(faq.get("question") or faq.get("q"))
            answer = _plain_text(faq.get("answer") or faq.get("a"))
            if question and answer:
                faq_entities.append({
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {"@type": "Answer", "text": answer},
                })
    if faq_entities:
        graph.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_entities,
        })

    return graph

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


def _build_preview_panel(sections: list[dict]) -> str:
    """Preview-only indicator listing sections that cannot render yet.

    Production never receives this — it is appended after rendering, so preview
    and production share exactly one rendering pipeline and one template.
    """
    if not sections:
        return ""
    rows = []
    for section in sections:
        missing = []
        for entry in section.get("missing_required", []):
            missing.append(" or ".join(entry) if isinstance(entry, (list, tuple)) else str(entry))
        detail = ", ".join(missing) if missing else "no content yet"
        rows.append(
            '<li style="margin:4px 0"><strong>{label}</strong> — missing: {detail}</li>'.format(
                label=section.get("label", section.get("section", "")), detail=detail
            )
        )
    return (
        '<div data-preview-indicator style="position:fixed;left:16px;bottom:16px;z-index:9999;'
        'max-width:340px;background:#1C1B22;color:#F6F4FB;border-radius:10px;padding:14px 16px;'
        'font:13px/1.5 system-ui,sans-serif;box-shadow:0 12px 30px -12px rgba(0,0,0,.6)">'
        '<div style="font-weight:800;margin-bottom:6px">Preview — incomplete sections</div>'
        '<ul style="margin:0;padding-left:18px">' + "".join(rows) + "</ul>"
        '<div style="margin-top:8px;opacity:.7;font-size:12px">Hidden in production.</div>'
        "</div>"
    )


def render_resolved(resolved: dict, standalone: bool = False, preview: bool = False) -> str:
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

    # Resolve SEO Settings (primary_domain and default_og_image)
    primary_domain = ""
    default_og_image = ""
    meta_path = WORKSPACES_ROOT / uni_slug / "metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_json = json.load(f)
                site_meta = meta_json.get("site") or {}
                primary_domain = (site_meta.get("primary_domain") or meta_json.get("site_url") or meta_json.get("domain") or "").rstrip("/")
                default_og_image = site_meta.get("default_og_image") or ""
        except Exception:
            pass

    # Resolve Route and Canonical URL from the shared public-route implementation.
    slug = resolved.get("slug") or ""
    route = build_public_route(page_type, slug, uni_slug)
    canonical_url = build_public_url(primary_domain, route, is_homepage=(page_type == "university"))

    ctx["canonical_url"] = canonical_url

    # Resolve Open Graph Image URL (priority: page-specific -> hero -> featured -> default og image -> logo)
    raw_og_image = raw_dict.get("og_image_url") or raw_dict.get("featured_image_url") or ctx.get("og_image_url")
    raw_hero = raw_dict.get("hero_image_url") or ctx.get("hero_image_url")
    
    og_image_candidate = raw_og_image or raw_hero or default_og_image or branding_logo
    
    if og_image_candidate:
        if og_image_candidate.startswith("http://") or og_image_candidate.startswith("https://"):
            og_image_url = og_image_candidate
        elif primary_domain:
            og_image_url = build_public_url(primary_domain, og_image_candidate)
        else:
            og_image_url = og_image_candidate
    else:
        og_image_url = ""

    ctx["og_image_url"] = og_image_url
    ctx["homepage_href"] = build_public_route("university")
    ctx["course_href"] = build_public_route("course", f"{uni_slug}-online-mba", uni_slug)
    ctx["spec_href"] = build_public_route("specialization", f"{uni_slug}-mba-marketing", uni_slug)
    ctx["blog_href"] = build_public_route("blog_listing")
    ctx["programs_listing_href"] = build_public_route("programs_listing")
    ctx["specs_listing_href"] = build_public_route("specializations_listing")
    ctx["blog_listing_href"] = build_public_route("blog_listing")
    ctx["contact_href"] = build_public_route("contact")

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

    # Lead actions stay on the generated workspace site. The Contact page
    # submits directly to its workspace-configured webhook when available.
    ctx["university_slug"] = uni_slug
    ctx["slug"] = resolved.get("slug") or ""
    ctx["parent_course_slug"] = resolved.get("parent_slug") or ""
    ctx["specialization_slug"] = resolved.get("slug") or ""
    
    for key in (
        "lead_url", "lead_url_apply", "lead_url_brochure", "lead_url_enquiry",
        "lead_url_fees", "lead_url_counselling", "lead_url_syllabus", "lead_url_whatsapp",
    ):
        ctx[key] = ctx["contact_href"]
    
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
                "href": build_public_route("specialization", sp_slug, uni_slug),
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
    # No fabricated fee plans. An empty list hides the fee section (production)
    # or shows a placeholder indicator (preview).
    ctx["fees_json"] = json.dumps(fee_list, ensure_ascii=False)
    
    # 6. Admission Steps
    steps_list = parse_admission_html((ctx.get("admission") or {}).get("steps") if ctx.get("admission") else "")
    if not steps_list:
        # Knowledge base is real, shared university data — not fabrication.
        steps_raw = resolve_field(raw_dict, knowledge, "admission_steps")
        if steps_raw:
            steps_list = parse_admission_html(steps_raw)
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
    # No fabricated job titles or salaries.
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
    # No fabricated testimonials. Reviews are a MANUAL field — see
    # core/field_definitions.py; if none were supplied the section stays hidden.
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
    # No fabricated FAQs. These previously also leaked into the FAQPage JSON-LD.
    ctx["faq_data_json"] = json.dumps(faq_list, ensure_ascii=False)
 
    # 10. Syllabus Semester 1 & 2 / Semester 3 & 4
    syllabus_years = parse_syllabus_html(ctx.get("syllabus") or resolve_field(raw_dict, knowledge, "syllabus_content", ""))
    # No fabricated curriculum. An empty syllabus hides the section.
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
        sibling_slug = s.get("slug") or ""
        other_specs_list.append({
            "name": s.get("name") or "",
            "fee": clean_fee(s.get("fee") or ""),
            "cur": False,
            "href": build_public_route("specialization", sibling_slug, uni_slug) if sibling_slug else "",
            "slug": sibling_slug,
        })
    if len(other_specs_list) <= 1:
        # No workspace siblings — fall back to the page's own `other_specs`
        # schema field. If that is empty too, the comparison table is dropped
        # entirely (a table listing only the current page is not a comparison).
        schema_specs = resolve_list(raw_dict, knowledge, "other_specs")
        other_specs_list = [
            {
                "name": s.get("name") or s.get("other_spec_name") or "",
                "fee": clean_fee(s.get("fee") or s.get("other_spec_fee") or ""),
                "cur": False,
                "href": build_public_route("specialization", s.get("slug"), uni_slug) if s.get("slug") else "",
                "slug": s.get("slug") or ""
            }
            for s in schema_specs
            if isinstance(s, dict)
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
    # features / recruiters / financing / banks come from the university
    # knowledge base only. No hardcoded stats, recruiter logos or EMI figures.
    features_list = resolve_list(raw_dict, knowledge, "features")
    ctx["features_json"] = json.dumps(features_list, ensure_ascii=False)

    recruiters_list = resolve_list(raw_dict, knowledge, "recruiters")
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
    ctx["financing_json"] = json.dumps(financing_list, ensure_ascii=False)

    banks_list = resolve_list(raw_dict, knowledge, "banks")
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
            if uni_slug == "nmims-2" and "emba" in name_lower:
                is_undergrad = False
            level = "Undergraduate" if is_undergrad else "Postgraduate"
            
            uni_programs.append({
                "level": level,
                "name": data.get("program_name") or data.get("course_name") or slug.replace("-", " ").title(),
                "dur": data.get("duration") or "",
                "fee": clean_fee(data.get("total_fee") or data.get("starting_fee") or ""),
                "feeUnit": "total course",
                "d": data.get("hero_description") or "",
                "href": build_public_route("course", slug, uni_slug),
                "featured": i == 0,
                "mode": data.get("mode") or "100% Online",
            })
    else:
        # No courses in the workspace yet — no invented "Online MBA" card.
        uni_programs = []

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
            "href": build_public_route("course", slug, uni_slug),
            "fee": clean_fee(data.get("total_fee") or data.get("starting_fee") or ""),
            "duration": data.get("duration") or "",
            "eligibility": data.get("eligibility_summary") or "",
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
            "href": build_public_route("specialization", sp_slug, uni_slug),
            "fee": clean_fee(data.get("total_fee") or ""),
            "duration": data.get("duration") or "",
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
            blog_href = build_public_route("blog", b_slug, uni_slug)
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
    # No demo blog posts when the workspace has none (see REG-001).
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

    # Populate native template collections directly on the context.
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
                "href": build_public_route("specialization", sp_slug, uni_slug),
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

    # Preview vs production. The ONLY difference: preview marks sections that
    # cannot render yet. Production hides them silently. Same renderer, same
    # template, same context otherwise.
    incomplete_sections: list[dict] = []
    if preview:
        from core.editing_state import build_editing_state
        editing_state = build_editing_state(page_type, raw_dict, {
            "page_type": page_type,
            "slug": resolved.get("slug"),
            "university_slug": uni_slug,
            "parent_slug": resolved.get("parent_slug"),
        })
        incomplete_sections = [
            s for s in editing_state.get("sections", [])
            if not s["renderable"] and s["data_source"] == "page"
        ]
    ctx["preview_mode"] = preview
    ctx["preview_incomplete_sections"] = incomplete_sections

    ctx["ctx_json"] = json.dumps(ctx, default=str)
    ctx["standalone"] = standalone  # controls nav/footer visibility in templates
    template_name = TEMPLATE_MAP.get(resolved["page_type"], f"{resolved['page_type']}.html")
    
    template = env.get_template(template_name)

    html_out = clean_html_tables(template.render(**ctx))

    # SEO & Open Graph post-processor for every supported render mode.
    if "</head>" in html_out.lower():
        # Get existing meta/link tag helper
        def get_meta_tag(html_str: str, name_or_prop: str) -> str | None:
            m = re.search(
                rf'<meta[^>]+(?:property|name)=["\']{re.escape(name_or_prop)}["\'][^>]*content=["\']([^"\']*)["\']',
                html_str, re.IGNORECASE,
            )
            if m:
                return m.group(1)
            m = re.search(
                rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']{re.escape(name_or_prop)}["\']',
                html_str, re.IGNORECASE,
            )
            return m.group(1) if m else None

        def get_canonical_link(html_str: str) -> str | None:
            m = re.search(
                r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']*)["\']',
                html_str, re.IGNORECASE,
            )
            if m:
                return m.group(1)
            m = re.search(
                r'<link[^>]+href=["\']([^"\']*)["\'][^>]+rel=["\']canonical["\']',
                html_str, re.IGNORECASE,
            )
            return m.group(1) if m else None

        # Determine target values
        page_title = ctx.get("seo_title") or ctx.get("title") or ""
        page_desc = ctx.get("meta_description") or ""
        target_canonical = ctx.get("canonical_url") or ""
        target_og_type = "article" if resolved.get("page_type") == "blog" else "website"
        target_image = ctx.get("og_image_url") or ""

        # Build missing tags
        new_tags = []
        
        # 1. Canonical Link
        if get_canonical_link(html_out) is None and target_canonical:
            new_tags.append(f'  <link rel="canonical" href="{target_canonical}">')
            
        # 2. OG Url
        if get_meta_tag(html_out, "og:url") is None and target_canonical:
            new_tags.append(f'  <meta property="og:url" content="{target_canonical}">')
            
        # 3. OG Type
        if get_meta_tag(html_out, "og:type") is None:
            new_tags.append(f'  <meta property="og:type" content="{target_og_type}">')
            
        # 4. OG Title
        if get_meta_tag(html_out, "og:title") is None and page_title:
            new_tags.append(f'  <meta property="og:title" content="{page_title}">')
            
        # 5. OG Description
        if get_meta_tag(html_out, "og:description") is None and page_desc:
            new_tags.append(f'  <meta property="og:description" content="{page_desc}">')
            
        # 6. OG Image
        if get_meta_tag(html_out, "og:image") is None and target_image:
            new_tags.append(f'  <meta property="og:image" content="{target_image}">')
            
        # 7. Twitter Card
        if get_meta_tag(html_out, "twitter:card") is None:
            new_tags.append('  <meta name="twitter:card" content="summary_large_image">')
            
        # 8. Twitter Title
        if get_meta_tag(html_out, "twitter:title") is None and page_title:
            new_tags.append(f'  <meta name="twitter:title" content="{page_title}">')
            
        # 9. Twitter Description
        if get_meta_tag(html_out, "twitter:description") is None and page_desc:
            new_tags.append(f'  <meta name="twitter:description" content="{page_desc}">')
            
        # 10. Twitter Image
        if get_meta_tag(html_out, "twitter:image") is None and target_image:
            new_tags.append(f'  <meta name="twitter:image" content="{target_image}">')

        if new_tags:
            match = re.search(r"</head>", html_out, re.IGNORECASE)
            if match:
                idx = match.start()
                block = "\n".join(new_tags) + "\n"
                html_out = html_out[:idx] + block + html_out[idx:]

    if "</head>" in html_out.lower():
        structured_data = _build_structured_data(ctx, resolved, raw_dict, primary_domain)
        if structured_data:
            scripts = "\n".join(
                '<script type="application/ld+json">'
                + json.dumps(item, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
                + "</script>"
                for item in structured_data
            )
            match = re.search(r"</head>", html_out, re.IGNORECASE)
            if match:
                html_out = html_out[:match.start()] + scripts + "\n" + html_out[match.start():]

    if preview:
        panel = _build_preview_panel(incomplete_sections)
        if panel:
            match = re.search(r"</body>", html_out, re.IGNORECASE)
            if match:
                html_out = html_out[:match.start()] + panel + html_out[match.start():]
            else:
                html_out += panel

    return html_out
