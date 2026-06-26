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

        if "Heading" in style_name:
            level = int(style_name.split()[-1]) if style_name.split()[-1].isdigit() else 1
            return {
                "type": HEADING_MAP.get(level, "h2"),
                "text": text
            }
        elif is_list or "List" in style_name or text.startswith(("•", "▪", "●", "○", "■", "- ", "* ")):
            return {"type": "list_item", "text": text}
        elif para.runs and any(r.bold for r in para.runs if r.text.strip()):
            return {"type": "bold_para", "text": text}
        else:
            return {"type": "paragraph", "text": text}


def _table_to_block(table) -> dict | None:
    rows = []
    for row in table.rows:
        cells = [clean_text(cell.text) for cell in row.cells]
        if any(cells):
            rows.append(cells)
    if rows:
        return {"type": "table", "rows": rows}
    return None


def parse_docx(filepath: str) -> list[dict]:
    doc = Document(filepath)
    blocks = []

    for item in iter_document_blocks(doc):
        if isinstance(item, Paragraph):
            block = _paragraph_to_block(item)
        elif isinstance(item, Table):
            block = _table_to_block(item)
        else:
            block = None

        if block:
            blocks.append(block)

    return blocks
