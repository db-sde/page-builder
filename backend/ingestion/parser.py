import re
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

HEADING_MAP = {1: "h1", 2: "h2", 3: "h3", 4: "h4"}

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Strip HTML tag residue like </h1> or </H2>
    text = re.sub(r"</?[a-zA-Z0-9]+>", "", text)
    # Strip prefixes like H1_ or H1: (case-insensitive) at the beginning
    text = re.sub(r"^[hH][1-4][_\s:]+", "", text)
    # Strip "Copy of" prefix
    text = re.sub(r"^Copy of\s+", "", text, flags=re.IGNORECASE)
    return text.strip()

def iter_document_blocks(doc):
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


def _paragraph_to_block(para) -> dict | None:
        text = clean_text(para.text)
        if not text:
            return None

        style_name = para.style.name or ""
        pPr = para._p.pPr
        is_list = False
        if pPr is not None:
            numPr = pPr.find(qn('w:numPr'))
            if numPr is not None:
                is_list = True

        if style_name.strip().lower() == "title":
            return {"type": "h1", "text": text, "style": "Title"}
        if "Heading" in style_name:
            level = int(style_name.split()[-1]) if style_name.split()[-1].isdigit() else 1
            return {
                "type": HEADING_MAP.get(level, "h2"),
                "text": text,
                "style": style_name,
            }
        elif is_list or "List" in style_name or text.startswith(("•", "▪", "●", "○", "■", "- ", "* ")):
            num_pr = pPr.find(qn("w:numPr")) if pPr is not None else None
            ilvl = num_pr.find(qn("w:ilvl")) if num_pr is not None else None
            level = int(ilvl.get(qn("w:val"))) if ilvl is not None and ilvl.get(qn("w:val"), "").isdigit() else 0
            is_ordered = "number" in style_name.lower() or bool(re.match(r"^\s*\d+[.)]\s+", text))
            return {
                "type": "list_item",
                "text": text,
                "list_kind": "ol" if is_ordered else "ul",
                "list_level": level,
                "style": style_name,
            }
        elif "quote" in style_name.lower():
            return {"type": "blockquote", "text": text, "style": style_name}
        elif any(marker in style_name.lower() for marker in ("note", "callout")):
            return {"type": "callout", "text": text, "style": style_name}
        elif para.runs and any(r.bold for r in para.runs if r.text.strip()):
            return {"type": "bold_para", "text": text}
        else:
            return {"type": "paragraph", "text": text}


HEADER_MAP = {
    "course name": "Program Name",
    "degree name": "Program Name",
    "program": "Program Name",
    "course fee": "Fee Amount",
    "fee": "Fee Amount",
    "total fee": "Fee Amount",
    "eligibility criteria": "Eligibility",
    "course eligibility": "Eligibility",
    "program fee": "Fee Amount",
}

def normalize_header(h: str) -> str:
    h_clean = h.strip()
    h_lower = h_clean.lower()
    return HEADER_MAP.get(h_lower, h_clean)

def is_candidate_title(block) -> bool:
    if not block:
        return False
    btype = block.get("type")
    text = block.get("text", "").strip()
    if not text:
        return False
    if text.endswith((".", "?", "!", ":")):
        return False
    if len(text) > 100:
        return False
    if btype in ("h1", "h2", "h3", "h4", "bold_para"):
        return True
    if btype == "paragraph":
        return len(text) < 60
    return False

def process_table_block(raw_rows, last_text_block) -> tuple[dict, bool]:
    # Estimate column count
    col_count = max(len(row) for row in raw_rows) if raw_rows else 0
    
    table_title = ""
    headers = []
    data_rows = []
    warning = None
    consumed_title = False
    
    # 1. Check if first row is a merged title row (all cells are identical)
    first_row = raw_rows[0] if raw_rows else []
    first_row_cleaned = [c.strip() for c in first_row]
    is_merged_title = len(first_row_cleaned) > 0 and len(set(first_row_cleaned)) == 1
    
    if is_merged_title:
        table_title = first_row_cleaned[0]
        if len(raw_rows) >= 2:
            headers = raw_rows[1]
            data_rows = raw_rows[2:]
        else:
            headers = first_row
            data_rows = []
    else:
        # Check if preceding block is a candidate title
        if is_candidate_title(last_text_block):
            table_title = last_text_block["text"]
            consumed_title = True
            
        headers = first_row
        data_rows = raw_rows[1:]

    original_headers = list(headers)

    # 2. Duplicate header check / validation & recovery
    headers_cleaned = [h.strip() for h in headers]
    if len(headers_cleaned) > 0 and len(set(headers_cleaned)) == 1 and data_rows:
        # Recovery attempt: treat current headers as table_title (if not already set)
        if not table_title:
            table_title = headers_cleaned[0]
        headers = data_rows[0]
        data_rows = data_rows[1:]
        headers_cleaned = [h.strip() for h in headers]
        warning = "TABLE_HEADER_RECOVERED"

    # Normalize headers
    headers = [normalize_header(h) for h in headers]
    headers_cleaned = [h.strip() for h in headers]

    # Ensure all data rows have the same column count as headers
    expected_col_count = len(headers)
    cleaned_data_rows = []
    for r in data_rows:
        if len(r) < expected_col_count:
            cleaned_data_rows.append(r + [""] * (expected_col_count - len(r)))
        elif len(r) > expected_col_count:
            cleaned_data_rows.append(r[:expected_col_count])
        else:
            cleaned_data_rows.append(r)

    # 3. Validation Checks
    validation_failed = False
    
    if len(headers) != col_count:
        validation_failed = True
        
    if len(set(headers_cleaned)) <= 1:
        validation_failed = True
        
    if headers and max(len(h) for h in headers) >= 80:
        validation_failed = True
        
    if not cleaned_data_rows:
        validation_failed = True
        
    if table_title and headers_cleaned == [table_title.strip()] * len(headers):
        validation_failed = True

    if validation_failed:
        warning = "TABLE_HEADER_DETECTION_FAILED"
        
    # Return block
    block = {
        "type": "table",
        "table_title": table_title,
        "headers": headers,
        "rows": cleaned_data_rows
    }
    if warning:
        block["warning"] = warning
        block["warning_info"] = {
            "warning_type": warning,
            "table_title": table_title,
            "detected_headers": original_headers,
            "suggested_headers": headers
        }
        
    return block, consumed_title

def parse_docx(filepath: str) -> list[dict]:
    doc = Document(filepath)
    blocks = []
    raw_blocks = []

    for item in iter_document_blocks(doc):
        if isinstance(item, Paragraph):
            block = _paragraph_to_block(item)
            if block:
                raw_blocks.append(block)
        elif isinstance(item, Table):
            raw_rows = []
            for row in item.rows:
                cells = [clean_text(cell.text) for cell in row.cells]
                if any(cells):
                    raw_rows.append(cells)
            if raw_rows:
                raw_blocks.append({"type": "raw_table", "rows": raw_rows})

    # Process sequentially to consume titles
    for b in raw_blocks:
        if b["type"] == "raw_table":
            preceding_block = blocks[-1] if blocks else None
            processed_table, consumed_title = process_table_block(b["rows"], preceding_block)
            if consumed_title and blocks:
                blocks.pop()
            blocks.append(processed_table)
        else:
            blocks.append(b)

    return blocks
