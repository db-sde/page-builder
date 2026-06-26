from difflib import get_close_matches

# Canonical heading anchors per page type
HEADING_ANCHORS = {
    "course": {
        "about": ["about", "overview", "program overview", "about the program"],
        "highlights": ["highlights", "program highlights", "key features"],
        "eligibility": ["eligibility", "who can apply", "eligibility criteria"],
        "fees": ["fees", "fee structure", "fees and financing", "pricing"],
        "emi": ["emi", "financing", "emi options", "emi details"],
        "admission": ["admission", "admission process", "how to apply", "admissions"],
        "syllabus": ["syllabus", "curriculum", "course structure"],
        "placement": ["placement", "career services", "placements"],
        "certificate": ["certificate", "degree certification", "degree certificate", "certification"],
        "faqs": ["faq", "faqs", "frequently asked questions"],
        "reviews": ["reviews", "testimonials", "student reviews"],
    },
    "specialization": {
        "about": ["about", "overview", "about the specialization"],
        "highlights": ["highlights", "specialization highlights"],
        "eligibility": ["eligibility", "eligibility criteria"],
        "fees": ["fees", "fee structure", "fee structure & installments"],
        "emi": ["emi", "emi details", "financing", "fees and financing"],
        "admission": ["admission", "admission process", "how to apply"],
        "syllabus": ["syllabus", "curriculum", "year 1", "year 2", "syllabus curriculum"],
        "placement": ["placement", "career services", "placement assistance"],
        "certificate": ["certificate", "degree certification", "degree certificate", "certification"],
        "jobs": ["job profiles", "career profiles", "jobs after", "career outcomes", "job profiles & salary ranges"],
        "faqs": ["faq", "faqs", "frequently asked questions", "faq questions"],
        "reviews": ["reviews", "student reviews", "testimonials"],
    },
    "university": {
        "about": ["about", "about us", "overview", "about the university"],
        "why_choose": ["why choose", "why nmims", "why us", "advantages"],
        "facts": ["quick facts", "facts", "key facts", "at a glance"],
        "accreditations": ["accreditations", "approvals", "rankings", "recognition"],
        "programs": ["programs", "courses offered", "programs and fees"],
        "admission": ["admission", "admission process", "how to apply"],
        "emi": ["emi", "financing", "fees and financing", "scholarships"],
        "exam": ["exam", "examination", "exam pattern"],
        "placement": ["placement", "placements", "career services"],
        "faqs": ["faq", "faqs", "frequently asked questions"],
        "reviews": ["reviews", "testimonials", "student reviews"],
    }
}

def normalize_heading(text: str, anchors: list[str]) -> str | None:
    text_lower = text.lower().strip()
    # Exact match first
    if text_lower in anchors:
        return text_lower
    # Fuzzy match
    matches = get_close_matches(text_lower, anchors, n=1, cutoff=0.6)
    return matches[0] if matches else None

def blocks_to_sections(blocks: list[dict], page_type: str) -> dict:
    anchors_map = HEADING_ANCHORS.get(page_type, {})
    # Build reverse map: anchor_variant → canonical key
    reverse = {}
    for key, variants in anchors_map.items():
        for v in variants:
            reverse[v] = key

    sections = {}
    current_key = None
    current_blocks = []

    def flush():
        if current_key and current_blocks:
            sections[current_key] = current_blocks[:]

    for block in blocks:
        if block["type"] in ("h1", "h2", "h3"):
            flush()
            current_blocks = []
            
            # Check for square bracket tags first
            text_lower = block["text"].lower()
            import re
            tags_match = re.search(r'\[([^\]]+)\]', text_lower)
            matched_key = None
            if tags_match:
                tag_content = tags_match.group(1)
                for key in anchors_map.keys():
                    if key in tag_content or (key + "_heading") in tag_content or (key + "_content") in tag_content or (key + "_description") in tag_content:
                        matched_key = key
                        break
            
            if matched_key:
                current_key = matched_key
            else:
                matched = normalize_heading(block["text"], list(reverse.keys()))
                current_key = reverse.get(matched) if matched else None
        elif current_key:
            current_blocks.append(block)

    flush()
    return sections

def blocks_to_html(blocks: list[dict]) -> str:
    parts = []
    in_list = False
    for b in blocks:
        if b["type"] == "list_item":
            if not in_list:
                parts.append("<ul>")
                in_list = True
            clean_text = b.get("text", "")
            for prefix in ("•", "▪", "●", "○", "■", "- ", "* "):
                if clean_text.startswith(prefix):
                    clean_text = clean_text[len(prefix):].strip()
                    break
            parts.append(f"  <li>{clean_text}</li>")
        else:
            if in_list:
                parts.append("</ul>")
                in_list = False

            btype = b["type"]
            text = b.get("text", "")

            if btype == "h1":
                parts.append(f"<h2>{text}</h2>")   # demote h1 in body to h2
            elif btype == "h2":
                parts.append(f"<h2>{text}</h2>")
            elif btype == "h3":
                parts.append(f"<h3>{text}</h3>")
            elif btype == "h4":
                parts.append(f"<h3>{text}</h3>")   # render h4 as h3 for readability
            elif btype == "paragraph":
                parts.append(f"<p>{text}</p>")
            elif btype == "bold_para":
                parts.append(f"<p><strong>{text}</strong></p>")
            elif btype == "table":
                rows = b.get("rows", [])
                if rows:
                    header_row = rows[0]
                    thead = "<thead><tr>" + "".join(f"<th>{c}</th>" for c in header_row) + "</tr></thead>"
                    tbody_rows = "".join(
                        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
                        for row in rows[1:]
                    )
                    parts.append(f"<table>{thead}<tbody>{tbody_rows}</tbody></table>")
                else:
                    parts.append("<table></table>")
    if in_list:
        parts.append("</ul>")
    return "\n".join(parts)

def blocks_to_list(blocks: list[dict]) -> list[dict]:
    items = []
    for b in blocks:
        if b["type"] in ("paragraph", "bold_para", "list_item"):
            clean_text = b["text"]
            for prefix in ("•", "▪", "●", "○", "■", "- ", "* "):
                if clean_text.startswith(prefix):
                    clean_text = clean_text[len(prefix):].strip()
                    break
            items.append({"text": clean_text})
    return items

def _first_kv(kv: dict, keys: list[str]):
    for key in keys:
        val = kv.get(key)
        if val:
            return val
    return None

def _apply_kv_aliases(acf: dict, kv: dict, aliases: list[tuple[str, list[str]]]) -> None:
    for target_key, kv_keys in aliases:
        val = _first_kv(kv, kv_keys)
        if val:
            acf[target_key] = val

def extract_acf(blocks: list[dict], page_type: str, meta: dict) -> dict:
    sections = blocks_to_sections(blocks, page_type)
    acf = {}

    # Always carry meta fields through
    acf.update(meta)

    # Extract KV fields from the top blocks (before any section heading)
    kv = {}
    anchors_map = HEADING_ANCHORS.get(page_type, {})
    reverse = {}
    for key, variants in anchors_map.items():
        for v in variants:
            reverse[v] = key

    for b in blocks:
        if b["type"] in ("h1", "h2", "h3"):
            # Check if this heading corresponds to a valid section anchor
            text_lower = b.get("text", "").lower()
            import re
            tags_match = re.search(r'\[([^\]]+)\]', text_lower)
            matched_key = None
            if tags_match:
                tag_content = tags_match.group(1)
                for key in anchors_map.keys():
                    if key in tag_content or (key + "_heading") in tag_content or (key + "_content") in tag_content or (key + "_description") in tag_content:
                        matched_key = key
                        break
            if not matched_key:
                matched = normalize_heading(b.get("text", ""), list(reverse.keys()))
                matched_key = reverse.get(matched) if matched else None
            
            if matched_key:
                break
            else:
                continue
        text = b.get("text", "")
        if not text:
            continue
        parts = []
        if ":" in text:
            parts = text.split(":", 1)
        elif "-" in text:
            parts = text.split("-", 1)
        if len(parts) == 2:
            k = parts[0].strip().lower().replace(" ", "_")
            v = parts[1].strip()
            # Clean up trailing garbage or NA
            if v.lower() in ("na", "n/a", "null", "none"):
                v = None
            kv[k] = v

    if page_type == "course":
        _apply_kv_aliases(acf, kv, [
            ("duration", ["duration"]),
            ("mode", ["mode"]),
            ("naac_grade", ["naac_grade"]),
            ("ugc_status", ["ugc", "ugc_status", "ugc_approved_status"]),
            ("aicte_status", ["aicte", "aicte_status", "aicte_approved_status"]),
            ("eligibility", ["eligibility", "eligibility_criteria"]),
            ("total_fee", ["total_fee", "fee", "fees", "program_fee"]),
            ("fee", ["fee", "fees", "program_fee", "total_fee"]),
            ("fee_note", ["fee_note", "admission_fee_note", "fees_note", "note"]),
            ("admission_process", ["admission_process", "admissions_process"]),
            ("syllabus", ["syllabus", "curriculum"]),
            ("credits", ["credits", "total_credits"]),
        ])

        # Backwards-compatible aliases used by existing transformers.
        for target_key, kv_keys in [
            ("total_fee", ["total_fee"]),
            ("emi_amount", ["emi", "emi_amount"]),
        ]:
            if not acf.get(target_key):
                for k in kv_keys:
                    if kv.get(k):
                        acf[target_key] = kv[k]
                        break

        # hero_description from first paragraph of about section or top of doc
        about_blocks = sections.get("about", [])
        about_para = next((b["text"] for b in about_blocks if b["type"] in ("paragraph", "bold_para") and b.get("text")), "")
        if about_para:
            acf["hero_description"] = about_para
        else:
            acf["hero_description"] = next((b["text"] for b in blocks if b["type"] in ("paragraph", "bold_para") and b.get("text") and ":" not in b["text"] and "-" not in b["text"]), "")

        acf["about_content"] = blocks_to_html(sections.get("about", []))
        acf["highlights"] = [
            {"highlight_title": b["text"].split("—")[0].strip(),
             "highlight_description": b["text"].split("—")[1].strip() if "—" in b["text"] else ""}
            for b in sections.get("highlights", [])
            if b["type"] in ("paragraph", "bold_para", "list_item")
        ]
        acf["eligibility_content"] = blocks_to_html(sections.get("eligibility", []))
        acf["admission_steps"] = blocks_to_html(sections.get("admission", []))
        acf["syllabus_content"] = blocks_to_html(sections.get("syllabus", []))
        acf["placement_content"] = blocks_to_html(sections.get("placement", []))
        fee_plans, detected_specializations = _classify_fee_table(sections.get("fees", []))
        acf["fee_plans"] = fee_plans
        acf["detected_specializations"] = detected_specializations
        acf["faqs"] = _extract_faqs(sections.get("faqs", []))
        acf["reviews"] = _extract_reviews(sections.get("reviews", []))
        # Image fields — populated by upload pipeline, not docx extraction
        acf["hero_image_url"] = meta.get("hero_image_url", None)
        acf["hero_image_alt"] = meta.get("hero_image_alt", "")
        acf["og_image_url"] = meta.get("og_image_url", None)

    elif page_type == "specialization":
        _apply_kv_aliases(acf, kv, [
            ("spec_name", ["spec_name", "specialization_name", "title"]),
            ("specialization_name", ["specialization_name", "spec_name", "title"]),
            ("title", ["title", "specialization_name", "spec_name"]),
            ("parent", ["parent", "parent_program", "program_name"]),
            ("duration", ["duration"]),
            ("mode", ["mode"]),
            ("naac_grade", ["naac_grade"]),
            ("ugc_status", ["ugc", "ugc_status", "ugc_approved_status"]),
            ("eligibility", ["eligibility", "eligibility_criteria"]),
            ("fees", ["fees", "fee", "total_fee", "program_fee"]),
            ("total_fee", ["total_fee", "fees", "fee", "program_fee"]),
        ])

        # Backwards-compatible aliases used by existing transformers.
        for target_key, kv_keys in [
            ("emi_amount", ["emi", "emi_amount"]),
        ]:
            if not acf.get(target_key):
                for k in kv_keys:
                    if kv.get(k):
                        acf[target_key] = kv[k]
                        break

        # hero_description from first paragraph of about section
        about_blocks = sections.get("about", [])
        about_para = next((b["text"] for b in about_blocks if b["type"] in ("paragraph", "bold_para") and b.get("text")), "")
        if about_para:
            acf["hero_description"] = about_para
        else:
            acf["hero_description"] = next((b["text"] for b in blocks if b["type"] in ("paragraph", "bold_para") and b.get("text") and ":" not in b["text"] and "-" not in b["text"]), "")

        # certificate_description
        cert_blocks = sections.get("certificate", [])
        acf["certificate_description"] = next((b["text"] for b in cert_blocks if b["type"] in ("paragraph", "bold_para") and b.get("text")), "")

        acf["about_content"] = blocks_to_html(sections.get("about", []))
        acf["highlights"] = [
            {"highlight_title": b["text"].split("—")[0].strip(),
             "highlight_description": b["text"].split("—")[1].strip() if "—" in b["text"] else ""}
            for b in sections.get("highlights", [])
            if b["type"] in ("paragraph", "bold_para", "list_item")
        ]
        acf["eligibility_content"] = blocks_to_html(sections.get("eligibility", []))
        acf["admission_steps"] = blocks_to_html(sections.get("admission", []))
        acf["syllabus_content"] = blocks_to_html(sections.get("syllabus", []))
        acf["placement_content"] = blocks_to_html(sections.get("placement", []))
        acf["fee_plans"] = _extract_fee_plans(sections.get("fees", []))
        acf["job_profiles"] = _extract_jobs(sections.get("jobs", []))
        acf["faqs"] = _extract_faqs(sections.get("faqs", []))
        acf["reviews"] = _extract_reviews(sections.get("reviews", []))
        # Image fields — populated by upload pipeline, not docx extraction
        acf["hero_image_url"] = meta.get("hero_image_url", None)
        acf["hero_image_alt"] = meta.get("hero_image_alt", "")
        acf["og_image_url"] = meta.get("og_image_url", None)

    elif page_type == "university":
        _apply_kv_aliases(acf, kv, [
            ("university_name", ["university_name", "university", "name"]),
            ("university_full_name", ["university_full_name", "university_name", "university", "name"]),
            ("established_year", ["established_year", "establishment_year", "established", "established_in"]),
            ("naac_grade", ["naac_grade", "naac", "naac_accreditation", "naac_rating"]),
            ("ugc_status", ["ugc", "ugc_status", "ugc_approved_status", "ugc_approved"]),
            ("aicte_status", ["aicte", "aicte_status", "aicte_approved_status", "aicte_approved"]),
            ("nirf_rank", ["nirf", "nirf_rank", "nirf_ranking"]),
            ("rankings", ["rankings", "ranking"]),
            ("approvals", ["approvals", "recognitions", "recognition"]),
        ])
        acf["about_content"] = blocks_to_html(sections.get("about", []))
        acf["why_choose_content"] = blocks_to_html(sections.get("why_choose", []))
        acf["facts"] = [
            {"fact_title": b["text"].split("—")[0].strip(),
             "fact_description": b["text"].split("—")[1].strip() if "—" in b["text"] else ""}
            for b in sections.get("facts", [])
            if b["type"] in ("paragraph", "bold_para", "list_item")
        ]
        acf["accreditations"] = _extract_accreditations(sections.get("accreditations", []))
        acf["programs_table"] = _extract_programs_table(sections.get("programs", []))
        acf["admission_steps"] = blocks_to_html(sections.get("admission", []))
        acf["emi_content"] = blocks_to_html(sections.get("emi", []))
        acf["exam_content"] = blocks_to_html(sections.get("exam", []))
        acf["placement_content"] = blocks_to_html(sections.get("placement", []))
        acf["faqs"] = _extract_faqs(sections.get("faqs", []))
        acf["reviews"] = _extract_reviews(sections.get("reviews", []))
        # Image fields — populated by upload pipeline, not docx extraction
        acf["hero_image_url"] = meta.get("hero_image_url", None)
        acf["hero_image_alt"] = meta.get("hero_image_alt", "")
        acf["og_image_url"] = meta.get("og_image_url", None)

    elif page_type == "blog":
        _apply_kv_aliases(acf, kv, [
            ("title", ["title"]),
            ("author", ["author", "written_by", "by"]),
            ("published_date", ["published_date", "published_on", "date"]),
            ("date", ["date", "published_date", "published_on"]),
            ("reading_time", ["reading_time", "read_time", "min_read"]),
            ("read_time", ["read_time", "reading_time", "min_read"]),
        ])
        acf["featured_image_url"] = meta.get("featured_image_url", None)

    return acf

# --- Private extraction helpers ---

def classify_fee_plans(plans: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Classify a list of fee plan dicts.
    Returns: (classified_fee_plans, detected_specializations)
    """
    if not plans:
        return [], []

    payment_keywords = [
        "semester", "annual", "one-time", "one time", "emi", "installment", 
        "year 1", "year 2", "admission", "registration", "exam", "full program", 
        "regular", "default", "standard", "installment 1", "installment 2", 
        "term", "lump sum", "lumpsum", "yearly", "monthly", "admission fee", 
        "caution deposit", "exam fee", "tuition fee"
    ]

    academic_keywords = [
        "marketing", "finance", "hr", "human resource", "operations", 
        "analytics", "banking", "insurance", "retail", "supply chain", 
        "logistics", "international business", "entrepreneurship", 
        "hospitality", "tourism", "digital marketing", "data science", 
        "artificial intelligence", "fintech", "media", "brand", 
        "healthcare", "it ", "information technology", "ib ", "system",
        "general management", "airlines", "airport", "disaster"
    ]

    # Clean amount helper
    import re
    def get_numeric_amount(val_str):
        if not val_str:
            return None
        digits = re.sub(r"[^\d]", "", str(val_str))
        return int(digits) if digits else None

    # Analyze rows
    num_payment = 0
    num_academic = 0
    amounts = []

    for p in plans:
        name = p.get("plan_name", "").lower().strip()
        
        # Count keyword occurrences
        has_payment = any(kw in name for kw in payment_keywords)
        has_academic = any(kw in name for kw in academic_keywords)
        
        if has_payment:
            num_payment += 1
        if has_academic:
            num_academic += 1

        amt = get_numeric_amount(p.get("plan_amount"))
        if amt is not None:
            amounts.append(amt)

    # Check uniformity of amounts (if we have amounts)
    amounts_are_uniform = len(set(amounts)) <= 1 if amounts else False

    # Decide classification
    is_spec = False
    if num_academic > num_payment:
        is_spec = True
    elif amounts_are_uniform and num_academic > 0:
        is_spec = True
    elif num_academic > 0 and num_payment == 0:
        is_spec = True

    if is_spec:
        detected_specs = []
        for p in plans:
            name = p.get("plan_name", "").strip()
            if name and name.lower() not in ("full program", "regular", "default", "standard"):
                detected_specs.append(name)
        return [], detected_specs
    else:
        return plans, []

def _classify_fee_table(blocks):
    raw_plans = []
    for b in blocks:
        if b["type"] == "table":
            for row in b["rows"][1:]:  # skip header row
                if len(row) >= 2:
                    raw_plans.append({
                        "plan_name": row[0],
                        "plan_amount": row[1],
                        "plan_total": row[2] if len(row) >= 3 else row[1]
                    })
    
    return classify_fee_plans(raw_plans)

def _extract_fee_plans(blocks):
    plans = []
    for b in blocks:
        if b["type"] == "table":
            for row in b["rows"][1:]:  # skip header row
                if len(row) >= 2:
                    plans.append({
                        "plan_name": row[0],
                        "plan_amount": row[1],
                        "plan_total": row[2] if len(row) >= 3 else row[1]
                    })
    return plans

def _extract_faqs(blocks):
    faqs = []
    i = 0
    while i < len(blocks):
        if blocks[i]["type"] == "bold_para":
            question = blocks[i]["text"]
            answer = blocks[i+1]["text"] if i+1 < len(blocks) and blocks[i+1]["type"] == "paragraph" else ""
            faqs.append({"question": question, "answer": answer})
            i += 2
        else:
            i += 1
    return faqs

def _extract_reviews(blocks):
    reviews = []
    i = 0
    while i < len(blocks):
        if blocks[i]["type"] in ("paragraph",) and blocks[i]["text"].startswith('"'):
            text = blocks[i]["text"].strip('"')
            label = blocks[i+1]["text"] if i+1 < len(blocks) else ""
            reviews.append({"review_text": text, "reviewer_label": label})
            i += 2
        else:
            i += 1
    return reviews

def _extract_jobs(blocks):
    jobs = []
    for b in blocks:
        if b["type"] == "table":
            for row in b["rows"][1:]:
                if len(row) >= 2:
                    jobs.append({"job_title": row[0], "avg_salary": row[1]})
    return jobs

def _extract_accreditations(blocks):
    items = []
    for b in blocks:
        if b["type"] in ("paragraph", "bold_para", "list_item") and "—" in b["text"]:
            parts = b["text"].split("—")
            items.append({
                "body_name": parts[0].strip(),
                "body_descriptor": parts[1].strip() if len(parts) > 1 else "",
                "body_detail": parts[2].strip() if len(parts) > 2 else ""
            })
    return items

def _extract_programs_table(blocks):
    for b in blocks:
        if b["type"] == "table":
            rows = []
            for row in b["rows"][1:]:
                if len(row) >= 3:
                    rows.append({
                        "program_name": row[0],
                        "program_fee": row[1],
                        "program_eligibility": row[2]
                    })
            return rows
    return []
