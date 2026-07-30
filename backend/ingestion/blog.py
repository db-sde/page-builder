"""Structural DOCX extraction for Blog documents.

This module deliberately knows nothing about authoring, SEO, publication, or
site relationships.  It converts the local DOCX block stream into factual
article content only; the editor and renderer own enrichment.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from core.blog import article_excerpt, article_word_count
from ingestion.parser import _paragraph_to_block, clean_text, iter_document_blocks


def parse_blog_docx(filepath: str) -> list[dict[str, Any]]:
    """Read a Blog DOCX without applying page-parser table heuristics.

    Course and specialization extraction needs table classification and header
    normalisation.  Blog articles do not: their tables are article content, so
    this reader keeps their first row and cells exactly as authored.  A future
    inline-image extractor can append ``{"type": "image", "src": ...}``
    blocks here without changing the article serializer or editor contract.
    """
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    from docx.oxml.ns import qn

    document = Document(filepath)
    blocks: list[dict[str, Any]] = []
    for item in iter_document_blocks(document):
        if isinstance(item, Paragraph):
            block = _paragraph_to_block(item)
            if block:
                blocks.append(block)
        elif isinstance(item, Table):
            row_entries = [
                (row, [clean_text(cell.text) for cell in row.cells])
                for row in item.rows
            ]
            row_entries = [(row, cells) for row, cells in row_entries if any(cells)]
            rows = [cells for _, cells in row_entries]
            if rows:
                # Word marks an actual header row with ``w:tblHeader``. A
                # merged first row is an authored table title, not a guessed
                # heading; retain it as the HTML caption and continue to the
                # next real table row for headers.
                row_index = 0
                table_title = ""
                if len(rows) > 1 and len(set(rows[0])) == 1:
                    table_title = rows[0][0]
                    row_index = 1
                row_props = row_entries[row_index][0]._tr.trPr
                is_header = row_props is not None and row_props.find(qn("w:tblHeader")) is not None
                headers = rows[row_index] if is_header else []
                data_rows = rows[row_index + 1:] if is_header else rows[row_index:]
                blocks.append({
                    "type": "table",
                    "table_title": table_title,
                    "headers": headers,
                    "rows": data_rows,
                })
    return blocks


def _clean_filename(filename: str) -> str:
    value = Path(filename).stem
    value = re.sub(r"^Copy of\s+", "", value, flags=re.IGNORECASE)
    return re.sub(r"[_-]+", " ", value).strip()


def _text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _render_list(items: list[dict[str, Any]]) -> str:
    """Render a consecutive DOCX list run while preserving list kind/level."""
    roots: list[dict[str, Any]] = []
    stack: list[tuple[int, list[dict[str, Any]]]] = [(0, roots)]

    for raw in items:
        level = max(0, int(raw.get("list_level") or 0))
        kind = raw.get("list_kind") if raw.get("list_kind") in {"ol", "ul"} else "ul"
        while stack and level < stack[-1][0]:
            stack.pop()
        if level > stack[-1][0]:
            parent_nodes = stack[-1][1]
            if not parent_nodes:
                level = stack[-1][0]
            else:
                child_nodes: list[dict[str, Any]] = []
                parent_nodes[-1].setdefault("children", []).append((kind, child_nodes))
                stack.append((level, child_nodes))
        target = stack[-1][1]
        target.append({"text": _text(raw.get("text")), "kind": kind, "children": []})

    def render(nodes: list[dict[str, Any]], kind: str) -> str:
        body = []
        for node in nodes:
            children = "".join(render(child_nodes, child_kind) for child_kind, child_nodes in node["children"])
            body.append(f"<li>{html.escape(node['text'])}{children}</li>")
        return f"<{kind}>" + "".join(body) + f"</{kind}>"

    # Word generally gives one kind per level.  Splitting mixed roots keeps the
    # emitted HTML valid when a document switches from bullets to numbers.
    chunks: list[tuple[str, list[dict[str, Any]]]] = []
    for node in roots:
        if not chunks or chunks[-1][0] != node["kind"]:
            chunks.append((node["kind"], []))
        chunks[-1][1].append(node)
    return "".join(render(nodes, kind) for kind, nodes in chunks)


def _serialize_blocks(blocks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        if block.get("type") == "list_item":
            end = index
            while end < len(blocks) and blocks[end].get("type") == "list_item":
                end += 1
            parts.append(_render_list(blocks[index:end]))
            index = end
            continue

        kind = block.get("type")
        text = _text(block.get("text"))
        if kind in {"h1", "h2", "h3", "h4"} and text:
            # The page hero is the document H1.  Any later DOCX H1 remains a
            # structurally prominent section, but is rendered as H2 to retain a
            # valid single-H1 page document.
            level = "2" if kind == "h1" else kind[-1]
            parts.append(f"<h{level}>{html.escape(text)}</h{level}>")
        elif kind == "paragraph" and text:
            parts.append(f"<p>{html.escape(text)}</p>")
        elif kind == "bold_para" and text:
            parts.append(f"<p><strong>{html.escape(text)}</strong></p>")
        elif kind == "blockquote" and text:
            parts.append(f"<blockquote>{html.escape(text)}</blockquote>")
        elif kind == "callout" and text:
            parts.append(f'<aside class="article-callout">{html.escape(text)}</aside>')
        elif kind == "image" and block.get("src"):
            # Reserved for future DOCX-image extraction. The current authoring
            # flow adds body images through the rich-text editor.
            alt = _text(block.get("alt"))
            parts.append(f'<img src="{html.escape(str(block["src"]), quote=True)}" alt="{html.escape(alt)}">')
        elif kind == "table":
            title = _text(block.get("table_title"))
            headers = [_text(cell) for cell in block.get("headers") or []]
            rows = block.get("rows") or []
            caption = f"<caption>{html.escape(title)}</caption>" if title else ""
            head = ""
            if headers:
                head = "<thead><tr>" + "".join(f"<th scope=\"col\">{html.escape(cell)}</th>" for cell in headers) + "</tr></thead>"
            body = "<tbody>" + "".join(
                "<tr>" + "".join(f"<td>{html.escape(_text(cell))}</td>" for cell in row) + "</tr>"
                for row in rows
            ) + "</tbody>"
            parts.append(f"<table>{caption}{head}{body}</table>")
        index += 1
    return "\n".join(parts)


def _faq_pairs(blocks: list[dict[str, Any]]) -> tuple[list[dict[str, str]], set[int]]:
    """Detect only repeated structural question/answer pairs, never keywords."""
    candidates: list[tuple[int, int, dict[str, str]]] = []
    index = 0
    while index + 1 < len(blocks):
        question = _text(blocks[index].get("text"))
        answer = _text(blocks[index + 1].get("text"))
        question_kind = blocks[index].get("type")
        answer_kind = blocks[index + 1].get("type")
        is_question = question_kind in {"h2", "h3", "h4", "bold_para", "paragraph", "list_item"} and question.endswith("?")
        if is_question and answer_kind in {"paragraph", "bold_para", "list_item"} and len(answer) >= 16:
            candidates.append((index, index + 1, {"question": question, "answer": answer}))
            index += 2
        else:
            index += 1

    faqs: list[dict[str, str]] = []
    consumed: set[int] = set()
    run: list[tuple[int, int, dict[str, str]]] = []
    for candidate in candidates + [(-99, -99, {})]:
        if run and candidate[0] != run[-1][1] + 1:
            if len(run) >= 2:
                faqs.extend(item[2] for item in run)
                for start, end, _ in run:
                    consumed.update((start, end))
                preceding = run[0][0] - 1
                if preceding >= 0 and blocks[preceding].get("type") == "h2":
                    consumed.add(preceding)
            run = []
        if candidate[0] != -99:
            run.append(candidate)
    return faqs, consumed


def parse_blog_document(blocks: list[dict[str, Any]], filename: str) -> dict[str, Any]:
    """Extract the factual, editor-independent Blog payload from DOCX blocks."""
    normalized = [{**block, "text": _text(block.get("text"))} for block in blocks]
    title_index = next((i for i, block in enumerate(normalized) if block.get("type") == "h1" and block.get("text")), -1)
    if title_index < 0:
        title_index = next((i for i, block in enumerate(normalized) if block.get("type") in {"h2", "h3"} and block.get("text")), -1)
    title = normalized[title_index]["text"] if title_index >= 0 else _clean_filename(filename)

    body_blocks = [block for index, block in enumerate(normalized) if index != title_index]
    faqs, faq_indexes = _faq_pairs(body_blocks)
    rendered_blocks = [block for index, block in enumerate(body_blocks) if index not in faq_indexes]
    content_html = _serialize_blocks(rendered_blocks)

    first_paragraph = next(
        (block.get("text", "") for block in body_blocks if block.get("type") in {"paragraph", "bold_para"} and block.get("text")),
        "",
    )
    subtitle = ""
    if title_index >= 0 and title_index + 1 < len(normalized):
        candidate = normalized[title_index + 1]
        if candidate.get("type") == "paragraph":
            subtitle = candidate.get("text", "")

    return {
        "title": title,
        "subtitle": subtitle,
        "excerpt": first_paragraph or article_excerpt(content_html),
        "content_html": content_html,
        "article_blocks": normalized,
        "faqs": faqs,
        "word_count": article_word_count(content_html),
    }
