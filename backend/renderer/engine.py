from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.router import get_transformer
import os
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

TEMPLATE_MAP = {
    "university": "university.html",
    "course": "course.html",
    "specialization": "specialization.html",
    "blog": "blog.html",
    "programs_listing": "programs_listing.html",
    "specializations_listing": "specializations_listing.html",
    "blog_listing": "blog_listing.html",
}


def build_lead_url(uni_slug: str, course_slug: str = None, source: str = "page") -> str:
    """Build a centralized DegreeBaba lead capture URL with query parameters."""
    base = "https://apply.degreebaba.com"
    params = f"?university={uni_slug}"
    if course_slug:
        params += f"&course={course_slug}"
    params += f"&source={source}"
    return base + params

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

def render_resolved(resolved: dict, standalone: bool = False) -> str:
    transformer = get_transformer(resolved)
    ctx = transformer.transform()

    # Dynamic names & links
    uni_name = resolved.get("university_slug", "nmims").upper()
    raw_dict = resolved.get("raw") or {}
    if raw_dict.get("university_name"):
        uni_name = raw_dict["university_name"]
    elif raw_dict.get("university_full_name"):
        uni_name = raw_dict["university_full_name"]

    uni_slug = resolved.get("university_slug") or "nmims"
    page_type = resolved.get("page_type", "course")
    course_slug = resolved.get("parent_slug") or resolved.get("slug") or ""

    ctx["university_name"] = uni_name
    ctx["university_letter"] = uni_name[0].upper() if uni_name else "N"
    ctx["homepage_href"] = f"{uni_slug}.dc.html"
    ctx["course_href"] = f"{uni_slug}-online-mba.dc.html"
    ctx["spec_href"] = f"{uni_slug}-mba-marketing.dc.html"
    ctx["blog_href"] = f"{uni_slug}-blog.dc.html"
    # New listing page hrefs (workspace-relative)
    ctx["programs_listing_href"] = "programs_listing.html"
    ctx["specs_listing_href"] = "specializations_listing.html"
    ctx["blog_listing_href"] = "blog_listing.html"
    # Centralized lead URL — no contact/lead forms in this project
    ctx["lead_url"] = build_lead_url(uni_slug, course_slug, source=page_type)
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
    # Priority: workspace specs injected by compiler (via transformer) → source data items → hardcoded fallback
    workspace_specs_ctx = ctx.get("_workspace_specs") or []
    if workspace_specs_ctx:
        # Build spec cards from real workspace specialization records (capped at 6)
        spec_list = []
        for sp in workspace_specs_ctx[:6]:
            if not isinstance(sp, dict):
                continue
            data = sp.get("data", {})
            sp_slug = sp.get("slug", "")
            spec_list.append({
                "t": data.get("spec_name") or data.get("program_name") or sp_slug.replace("-", " ").title(),
                "d": data.get("hero_description") or data.get("description") or "",
                "href": f"{sp_slug}.html",
                "fee": data.get("total_fee") or data.get("starting_fee") or "",
            })
    else:
        specs_raw = (ctx.get("specializations") or {}).get("items", []) or []
        if isinstance(specs_raw, str):
            specs_raw = [{"t": specs_raw, "d": ""}]
        elif isinstance(specs_raw, list):
            new_s = []
            for s in specs_raw:
                if isinstance(s, str):
                    new_s.append({"t": s, "d": ""})
                elif isinstance(s, dict):
                    new_s.append(s)
            specs_raw = new_s
        spec_list = [
            {
                "t": s.get("name") or s.get("t", ""),
                "d": s.get("description") or s.get("d", ""),
                "href": (
                    s.get("href")
                    if s.get("href", "").startswith(("#", "/")) or ".html" in s.get("href", "")
                    else (f"{uni_slug}-" + s.get("href", "").strip("/").replace("page/", "") + ".dc.html" if s.get("href") else "#")
                )
            }
            for s in specs_raw[:6]
        ]
        # Hardcoded fallback — only used when workspace is truly empty
        if not spec_list:
            spec_list = [
                {"t": "Marketing Management", "d": "Brand, digital & consumer strategy", "href": "#"},
                {"t": "Financial Management", "d": "Corporate finance & valuation", "href": "#"},
                {"t": "Human Resource Management", "d": "Talent, OB & HR analytics", "href": "#"},
                {"t": "Operations & Supply Chain", "d": "Logistics, lean & procurement", "href": "#"},
                {"t": "Business Analytics", "d": "Data-driven decision making", "href": "#"},
                {"t": "IT & Systems Management", "d": "Digital transformation & ERP", "href": "#"},
            ]
    ctx["specs_json"] = json.dumps(spec_list, ensure_ascii=False)
    
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
    
    # 6. Admission Steps
    steps_list = parse_admission_html((ctx.get("admission") or {}).get("steps") if ctx.get("admission") else "")
    if not steps_list:
        steps_list = [
            {"n": "1", "t": "Register on the university portal and verify your mobile number."},
            {"n": "2", "t": "Complete the application form and choose Online MBA with your preferred specialization."},
            {"n": "3", "t": "Upload graduation marksheets, photo ID and a passport-size photograph."},
            {"n": "4", "t": "Pay the first installment online — enrollment and LMS access follow within 7 working days."}
        ]
    ctx["steps_json"] = json.dumps(steps_list, ensure_ascii=False)
    
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

    # Specialization specific other specs list
    siblings = ctx.get("other_specs") or []
    other_specs_list = []
    hero_dict = ctx.get("hero") or {}
    stat_card = hero_dict.get("stat_card") or {}
    hero_title = hero_dict.get("title") or ""
    stat_value = stat_card.get("value") or ""
    other_specs_list.append([hero_title, stat_value, True])
    for s in siblings:
        other_specs_list.append([s.get("name") or "", s.get("fee") or "", False])
    if len(other_specs_list) <= 1:
        other_specs_list = [
            ["Marketing Management", "₹2,00,000", True],
            ["Financial Management", "₹2,00,000", False],
            ["Human Resource Management", "₹2,00,000", False],
            ["Operations & Supply Chain", "₹2,00,000", False],
            ["Business Analytics", "₹2,16,000", False],
            ["IT & Systems Management", "₹2,00,000", False],
            ["International Business", "₹2,08,000", False]
        ]
    ctx["other_specs_json"] = json.dumps(other_specs_list, ensure_ascii=False)

    # University specific features, recruiters, financing, testimonials
    ctx["features_json"] = json.dumps([
        {"stat": "Live", "t": "Weekend Classes", "d": "Plus lifetime access to all recordings on the LMS."},
        {"stat": "120+", "t": "Expert Faculty", "d": "Learn from academics and industry practitioners."},
        {"stat": "4 Sem", "t": "Capstone Project", "d": "Industry-mentored capstone to apply your skills."},
        {"stat": "24mo", "t": "No-cost EMI", "d": "Flexible fee plans starting from ₹8,334 per month."}
    ], ensure_ascii=False)
    ctx["recruiters_json"] = json.dumps(['Deloitte', 'Amazon', 'HDFC', 'TCS', 'Accenture', 'HUL'], ensure_ascii=False)
    
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
    ctx["financing_json"] = json.dumps([
        {"stat": "₹8,334", "t": "No-cost EMI", "d": "Flexible plans starting from ₹8,334 per month."},
        {"stat": "3–12 mo", "t": "EMI tenures", "d": "Choose a 3, 6, 9 or 12-month repayment plan."},
        {"stat": "20% off", "t": "Defence scholarship", "d": "For armed forces personnel & their family."}
    ], ensure_ascii=False)
    ctx["banks_json"] = json.dumps(['HDFC', 'ICICI', 'Axis', 'Citi', 'Standard Chartered', 'HSBC', 'Kotak Mahindra'], ensure_ascii=False)

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
            "fee": data.get("total_fee") or data.get("starting_fee") or "",
            "duration": data.get("duration") or "2 Years",
            "eligibility": data.get("eligibility_summary") or "Bachelor's degree",
            "description": data.get("hero_description") or "",
            "mode": data.get("mode") or "100% Online",
        })
    ctx["programs_json"] = json.dumps(uni_programs[:4], ensure_ascii=False)
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
            "fee": data.get("total_fee") or "",
            "duration": data.get("duration") or "2 Years",
            "description": data.get("hero_description") or "",
        })
    ctx["spec_groups_json"] = json.dumps(list(spec_groups_map.values()), ensure_ascii=False)

    # Blog categories & posts
    ctx["cat_labels_json"] = json.dumps(['All', 'Career', 'Admissions', 'Guide', 'Finance', 'Student Life'], ensure_ascii=False)

    # Priority: workspace blogs (via transformer _workspace_blogs) → hardcoded demo fallback
    workspace_blogs_ctx = ctx.get("_workspace_blogs") or []
    if workspace_blogs_ctx:
        blog_posts = []
        for b in workspace_blogs_ctx[:3]:
            if not isinstance(b, dict):
                continue
            data = b.get("data", {})
            b_slug = b.get("slug", "")
            # Determine the blog page href — relative path to the blog detail HTML
            blog_href = f"{b_slug}.html"
            blog_posts.append({
                "tag": data.get("category") or data.get("tag") or "Article",
                "title": data.get("blog_title") or data.get("title") or b_slug.replace("-", " ").title(),
                "excerpt": data.get("hero_description") or data.get("excerpt") or "",
                "meta": data.get("read_time") or data.get("meta") or "",
                "href": blog_href,
                "image": data.get("hero_image_url") or "",
            })
    else:
        # Demo fallback — only shown when workspace contains no blogs
        blog_posts = [
            {"tag": "Guide", "title": "How to choose the right MBA specialization", "excerpt": "Marketing, finance, HR or analytics? A practical framework to match a track to your goals and background.", "meta": "6 min · Dec 2025", "href": "#", "image": ""},
            {"tag": "Finance", "title": "Online MBA fees & EMI options, fully explained", "excerpt": "Semester-wise, annual and one-time plans compared — plus how no-cost EMI actually works.", "meta": "5 min · Dec 2025", "href": "#", "image": ""},
            {"tag": "Admissions", "title": f"{uni_name} Online MBA eligibility & admission, step by step", "excerpt": "Documents, deadlines and the exact portal flow — everything you need before you apply.", "meta": "7 min · Nov 2025", "href": "#", "image": ""},
        ]
    ctx["all_posts_json"] = json.dumps(blog_posts, ensure_ascii=False)

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
