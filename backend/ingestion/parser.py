import re
from docx import Document
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

def parse_docx(filepath: str) -> list[dict]:
    doc = Document(filepath)
    blocks = []

    for para in doc.paragraphs:
        text = clean_text(para.text)
        if not text:
            continue

        style_name = para.style.name or ""
        pPr = para._p.pPr
        is_list = False
        if pPr is not None:
            numPr = pPr.find(qn('w:numPr'))
            if numPr is not None:
                is_list = True

        if "Heading" in style_name:
            level = int(style_name.split()[-1]) if style_name.split()[-1].isdigit() else 1
            blocks.append({
                "type": HEADING_MAP.get(level, "h2"),
                "text": text
            })
        elif is_list or "List" in style_name or text.startswith(("•", "▪", "●", "○", "■", "- ", "* ")):
            blocks.append({"type": "list_item", "text": text})
        elif para.runs and any(r.bold for r in para.runs if r.text.strip()):
            blocks.append({"type": "bold_para", "text": text})
        else:
            blocks.append({"type": "paragraph", "text": text})

    for table in doc.tables:
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                rows.append(cells)
        if rows:
            blocks.append({"type": "table", "rows": rows})

    return blocks
