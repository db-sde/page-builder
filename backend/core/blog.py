"""Shared, deterministic helpers for the Blog content pipeline.

The parser owns document facts.  These helpers only derive presentation values
from those facts, so the parser and renderer never need competing TOC, excerpt,
or reading-time implementations.
"""

from __future__ import annotations

import html
import math
import re
from html.parser import HTMLParser
from typing import Any


class _TextCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_text(value: str | None) -> str:
    """Return readable text from editor/article HTML without altering HTML."""
    parser = _TextCollector()
    try:
        parser.feed(value or "")
        parser.close()
    except Exception:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value or "")).strip()
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def article_word_count(content_html: str | None) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", html_to_text(content_html)))


def reading_time_label(content_html: str | None, override: str | None = None) -> str:
    """Return a transparent, derived reading-time label at 200 words/minute."""
    if isinstance(override, str) and override.strip():
        return override.strip()
    words = article_word_count(content_html)
    return f"{max(1, math.ceil(words / 200))} min read" if words else ""


def article_excerpt(content_html: str | None) -> str:
    """Use the first authored paragraph as the deterministic excerpt fallback."""
    match = re.search(r"<p\b[^>]*>(.*?)</p>", content_html or "", re.IGNORECASE | re.DOTALL)
    return html_to_text(match.group(1)) if match else ""


def _heading_slug(value: str, seen: dict[str, int]) -> str:
    base = re.sub(r"[^a-z0-9\s-]", "", value.lower())
    base = re.sub(r"[\s-]+", "-", base).strip("-") or "section"
    seen[base] = seen.get(base, 0) + 1
    return base if seen[base] == 1 else f"{base}-{seen[base]}"


def article_toc_and_anchors(content_html: str | None) -> tuple[str, list[dict[str, Any]]]:
    """Add stable ids to authored H2–H4 tags and derive a hierarchical TOC."""
    toc: list[dict[str, Any]] = []
    seen: dict[str, int] = {}

    def replace(match: re.Match[str]) -> str:
        level, attributes, inner = match.group(1), match.group(2), match.group(3)
        text = html_to_text(inner)
        if not text:
            return match.group(0)
        existing = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', attributes, re.IGNORECASE)
        anchor = existing.group(1) if existing else _heading_slug(text, seen)
        attrs = attributes if existing else f'{attributes} id="{html.escape(anchor, quote=True)}"'
        toc.append({"text": text, "href": f"#{anchor}", "level": int(level)})
        return f"<h{level}{attrs}>{inner}</h{level}>"

    rendered = re.sub(
        r"<h([2-4])([^>]*)>(.*?)</h\1>",
        replace,
        content_html or "",
        flags=re.IGNORECASE | re.DOTALL,
    )
    return rendered, toc


def author_initials(author: str | None) -> str:
    words = [word for word in (author or "").split() if word]
    if len(words) > 1:
        return (words[0][0] + words[1][0]).upper()
    return words[0][:2].upper() if words else ""
