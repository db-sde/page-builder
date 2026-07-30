"""Renderer context for factual Blog content plus editor-owned enrichment."""

from __future__ import annotations

import json
import html
import re
from typing import Any

from core.blog import article_toc_and_anchors, author_initials, reading_time_label
from transformers.base import BaseTransformer


def _slug_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


class BlogTransformer(BaseTransformer):
    """Build display data only; no author, category, date, or article defaults."""

    def _cards(self, records: list[dict], selected_slugs: list[str], page_type: str) -> list[dict]:
        by_slug = {record.get("slug"): record for record in records if isinstance(record, dict)}
        cards: list[dict] = []
        for selected in selected_slugs:
            record = by_slug.get(selected)
            if not record:
                continue
            data = record.get("data") or {}
            if page_type == "course":
                title = data.get("program_name") or data.get("course_name") or selected.replace("-", " ").title()
                excerpt = data.get("hero_description") or ""
                meta = " · ".join(value for value in (data.get("duration"), data.get("mode"), data.get("total_fee")) if value)
            elif page_type == "specialization":
                title = data.get("spec_name") or selected.replace("-", " ").title()
                excerpt = data.get("hero_description") or ""
                meta = data.get("total_fee") or ""
            else:
                title = data.get("title") or selected.replace("-", " ").title()
                excerpt = data.get("excerpt") or ""
                meta = data.get("category") or ""
            cards.append({
                "title": title,
                "excerpt": excerpt,
                "meta": meta,
                "image": data.get("hero_image_url") or "",
                "href": self.public_route(page_type, selected),
            })
        return cards

    def _inline_component_html(self, content: str, raw: dict) -> str:
        """Resolve editor-authored reference blocks from the workspace index.

        The editor persists only a component name and slugs in article HTML.  Page
        data is deliberately resolved during rendering, so fee, title and URL
        changes remain single-source-of-truth in their published pages.
        """
        records = {
            "course": raw.get("_workspace_courses") or [],
            "specialization": raw.get("_workspace_specs") or [],
            "blog": raw.get("_workspace_blogs") or [],
        }

        def cards(items: list[dict], kind: str) -> str:
            if not items:
                return ""
            rendered = []
            for item in items:
                title = html.escape(str(item.get("title") or ""))
                excerpt = html.escape(str(item.get("excerpt") or ""))
                meta = html.escape(str(item.get("meta") or ""))
                href = html.escape(str(item.get("href") or "#"), quote=True)
                rendered.append(f'<a class="blog-inline-card" href="{href}"><strong>{title}</strong>{f"<span>{excerpt}</span>" if excerpt else ""}{f"<small>{meta}</small>" if meta else ""}<b>Explore →</b></a>')
            return f'<section class="blog-inline-component blog-inline-component--cards">{"".join(rendered)}</section>'

        def replace(match: re.Match[str]) -> str:
            attributes = match.group(1)
            component_match = re.search(r'data-degreebaba-component="([a-z-]+)"', attributes)
            if not component_match:
                return match.group(0)
            kind = component_match.group(1)
            slugs_match = re.search(r'data-degreebaba-slugs="([^"]*)"', attributes)
            selected = [slug for slug in (slugs_match.group(1) if slugs_match else "").split(",") if slug]
            title_match = re.search(r'data-degreebaba-title="([^"]*)"', attributes)
            display_title = html.escape(title_match.group(1)) if title_match and title_match.group(1) else ""
            style_match = re.search(r'data-degreebaba-style="([a-z-]+)"', attributes)
            display_style = style_match.group(1) if style_match else "buttons"
            if kind == "course-cards":
                return cards(self._cards(records["course"], selected, "course"), "course")
            if kind == "related-blogs":
                return cards(self._cards(records["blog"], selected, "blog"), "blog")
            if kind == "specialization-buttons":
                selected_specs = self._cards([item for item in records["specialization"] if item.get("parent_slug") in selected], [item.get("slug") for item in records["specialization"] if item.get("parent_slug") in selected], "specialization")
                if not selected_specs:
                    return ""
                classes = "blog-inline-component--buttons" if display_style == "buttons" else f"blog-inline-component--{display_style}"
                heading = f"<h3>{display_title}</h3>" if display_title else ""
                return f'<section class="blog-inline-component {classes}">{heading}' + "".join(f'<a href="{html.escape(item["href"], quote=True)}">{html.escape(item["title"])}</a>' for item in selected_specs) + '</section>'
            if kind in {"fee-table", "syllabus"}:
                source = next((item for item in records["course"] + records["specialization"] if item.get("slug") in selected), None)
                data = (source or {}).get("data") or {}
                if kind == "syllabus":
                    syllabus = str(data.get("syllabus_content") or "").strip()
                    return f'<section class="blog-inline-component blog-inline-component--syllabus">{syllabus}</section>' if syllabus else ""
                plans = [plan for plan in data.get("fee_plans") or [] if isinstance(plan, dict) and plan.get("plan_name") and plan.get("plan_amount")]
                if not plans:
                    return ""
                rows = "".join(f'<tr><td>{html.escape(str(plan["plan_name"]))}</td><td>{html.escape(str(plan["plan_amount"]))}</td></tr>' for plan in plans)
                return f'<section class="blog-inline-component"><table><thead><tr><th>Payment plan</th><th>Amount</th></tr></thead><tbody>{rows}</tbody></table></section>'
            if kind == "cta":
                return '<aside class="blog-inline-component blog-inline-component--cta"><strong>Ready to learn more?</strong><a href="/contact">Contact admissions →</a></aside>'
            return ""

        return re.sub(r'<div\b([^>]*)></div>', replace, content)

    def _resolve_text_references(self, content: str) -> str:
        """Turn invisible editor references into ordinary production links."""
        route_type = {"course": "course", "specialization": "specialization", "blog": "blog"}

        def replace(match: re.Match[str]) -> str:
            attrs, inner = match.group(1), match.group(2)
            reference = re.search(r'data-degreebaba-reference="([a-z-]+)"', attrs)
            slug = re.search(r'data-degreebaba-slug="([^"]+)"', attrs)
            if not reference:
                return match.group(0)
            kind = reference.group(1)
            if kind == "cta":
                href = self.public_route("contact")
            elif kind in {"fee-table", "syllabus"} and slug:
                href = f'{self.public_route("course", slug.group(1))}#{"fees" if kind == "fee-table" else "syllabus"}'
            elif kind in route_type and slug:
                href = self.public_route(route_type[kind], slug.group(1))
            else:
                return inner
            return f'<a href="{html.escape(href, quote=True)}">{inner}</a>'

        return re.sub(r'<a\b([^>]*)>(.*?)</a>', replace, content, flags=re.DOTALL)

    @staticmethod
    def _render_markdown_links(content: str) -> str:
        """Support parser/imported Markdown links embedded in article paragraphs."""
        def replace(match: re.Match[str]) -> str:
            label, href = match.group(1).strip(), match.group(2).strip()
            if not label or not href or not re.match(r"^(https?://|/)", href):
                return match.group(0)
            return f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'
        return re.sub(r'\[([^\]\n]+)\]\(([^\s)]+)\)', replace, content)

    @staticmethod
    def _table_cell_text(markup: str) -> str:
        """Return comparable text without changing the authored cell markup."""
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))).strip()

    @classmethod
    def _normalise_article_table(cls, table: str) -> str:
        """Repair a couple of structural DOCX/table-editor artifacts safely.

        Some source tables put their title in the second cell of an otherwise
        empty first row, and repeat a year label in every column instead of
        merging the row.  Both are presentation artifacts: make the title a
        semantic caption and make only repeated academic section labels span
        the table.  Cell contents themselves are deliberately left untouched.
        """
        cell_row = re.compile(
            r"<tr\b(?P<row_attrs>[^>]*)>\s*"
            r"<(?P<left_tag>td|th)\b[^>]*>(?P<left>.*?)</(?P=left_tag)>\s*"
            r"<(?P<right_tag>td|th)\b[^>]*>(?P<right>.*?)</(?P=right_tag)>\s*"
            r"</tr>",
            flags=re.IGNORECASE | re.DOTALL,
        )

        caption = ""

        def extract_sparse_title(match: re.Match[str]) -> str:
            nonlocal caption
            if caption or re.search(r"<caption\b", table, flags=re.IGNORECASE):
                return match.group(0)
            left = cls._table_cell_text(match.group("left"))
            right = cls._table_cell_text(match.group("right"))
            if not left and right:
                caption = match.group("right").strip()
                return ""
            return match.group(0)

        # A sparse first body row is a title only when it immediately follows
        # the tbody opening tag; normal content rows are never removed.
        normalised = re.sub(
            r"(<tbody\b[^>]*>\s*)" + cell_row.pattern,
            lambda match: match.group(1) + extract_sparse_title(match),
            table,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if caption:
            normalised = re.sub(
                r"(<table\b[^>]*>)",
                lambda match: f"{match.group(1)}<caption>{caption}</caption>",
                normalised,
                count=1,
                flags=re.IGNORECASE,
            )

        def merge_section_row(match: re.Match[str]) -> str:
            left = cls._table_cell_text(match.group("left"))
            right = cls._table_cell_text(match.group("right"))
            if left != right or not re.match(r"^(?:year|term|phase|part|level)\b", left, flags=re.IGNORECASE):
                return match.group(0)
            return f'<tr class="blog-table-section-row"><th colspan="2">{match.group("left").strip()}</th></tr>'

        return cell_row.sub(merge_section_row, normalised)

    @classmethod
    def _normalise_article_tables(cls, content: str) -> str:
        """Normalize only the structural table artifacts the renderer can prove."""
        return re.sub(
            r"<table\b[\s\S]*?</table>",
            lambda match: cls._normalise_article_table(match.group(0)),
            content,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _wrap_article_tables(content: str) -> str:
        """Keep semantic tables intact while providing one responsive wrapper."""
        return re.sub(
            r'(?<!blog-table-wrapper">)(<table\b[\s\S]*?</table>)',
            r'<div class="blog-table-wrapper">\1</div>',
            content,
            flags=re.IGNORECASE,
        )

    def transform(self) -> dict:
        raw = self.raw
        title = str(raw.get("title") or "").strip()
        resolved_article = self._wrap_article_tables(self._normalise_article_tables(self._render_markdown_links(self._resolve_text_references(self._inline_component_html(raw.get("content_html") or "", raw)))))
        content_html, toc = article_toc_and_anchors(resolved_article)
        faqs = [
            {"q": item.get("question", ""), "a": item.get("answer", ""), "sign": "+", "disp": "none"}
            for item in raw.get("faqs") or []
            if isinstance(item, dict) and item.get("question") and item.get("answer")
        ]
        if faqs:
            toc.append({"text": "FAQs", "href": "#faq", "level": 2})

        related_course_slugs = _slug_list(raw.get("primary_course_slug")) + _slug_list(raw.get("related_course_slugs"))
        related_spec_slugs = _slug_list(raw.get("primary_specialization_slug")) + _slug_list(raw.get("related_specialization_slugs"))
        related_blog_slugs = [slug for slug in _slug_list(raw.get("related_blog_slugs")) if slug != self.slug]

        related_courses = self._cards(raw.get("_workspace_courses") or [], list(dict.fromkeys(related_course_slugs)), "course")
        related_specializations = self._cards(raw.get("_workspace_specs") or [], list(dict.fromkeys(related_spec_slugs)), "specialization")
        related_blogs = self._cards(raw.get("_workspace_blogs") or [], list(dict.fromkeys(related_blog_slugs)), "blog")

        requested_universities = _slug_list(raw.get("mentioned_university_slugs"))
        mentioned_universities = []
        if self.university_slug in requested_universities:
            mentioned_universities.append({
                "title": raw.get("university_name") or self.university_slug.replace("-", " ").title(),
                "href": self.public_route("university", self.university_slug),
            })

        cta_title = str(raw.get("cta_title") or "").strip()
        cta_description = str(raw.get("cta_description") or "").strip()
        cta_label = str(raw.get("cta_label") or "").strip()
        blog_cta = {
            "title": cta_title,
            "description": cta_description,
            "label": cta_label,
            "href": self.public_route("contact"),
        } if cta_title or cta_description or cta_label else None

        author = str(raw.get("author") or "").strip()
        published_date = str(raw.get("published_date") or raw.get("date") or "").strip()
        category = str(raw.get("category") or raw.get("tag") or "").strip()
        hero_image_url = raw.get("hero_image_url") or raw.get("featured_image_url") or ""
        excerpt = str(raw.get("excerpt") or raw.get("subtitle") or "").strip()

        return {
            "seo_title": str(raw.get("seo_title") or title).strip(),
            "meta_description": str(raw.get("meta_description") or excerpt).strip(),
            "site": self.site,
            "title": title,
            "subtitle": str(raw.get("subtitle") or "").strip(),
            "excerpt": excerpt,
            "content_html": content_html,
            "category": category,
            "tags": _slug_list(raw.get("tags")),
            "author": author,
            "author_initials": author_initials(author),
            "author_role": str(raw.get("author_role") or "").strip(),
            "published_date": published_date,
            "read_time": reading_time_label(content_html, raw.get("read_time_override")),
            "word_count": raw.get("word_count") or 0,
            "hero_image_url": hero_image_url,
            "hero_image_alt": raw.get("hero_image_alt") or title,
            "toc": toc,
            "toc_json": json.dumps(toc, ensure_ascii=False),
            "faqs": faqs,
            "faqs_json": json.dumps(faqs, ensure_ascii=False),
            "related_courses": related_courses,
            "related_specializations": related_specializations,
            "related_blogs": related_blogs,
            "mentioned_universities": mentioned_universities,
            "blog_cta": blog_cta,
        }
