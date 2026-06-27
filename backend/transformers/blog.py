import json
from core.site_config import SITE_CONFIG

class BlogTransformer:
    def __init__(self, resolved: dict):
        self.site = SITE_CONFIG
        self.raw = resolved["raw"]

    def transform(self) -> dict:
        raw = self.raw
        
        # Core fields parsed from the DOCX
        title = raw.get("title") or raw.get("hero_title") or "Untitled Blog Post"
        excerpt = raw.get("excerpt") or raw.get("hero_description") or ""
        content_html = raw.get("content_html") or ""

        import re
        faqs = raw.get("faqs") or []
        if not faqs and content_html:
            pattern = re.compile(
                r'(<h[2-4][^>]*>(?:FAQ|FAQs|Frequently\s+Asked\s+Questions)(?:\s*\(FAQs?\))?</h[2-4]>)\s*(<(?:ul|ol)[^>]*>.*?</(?:ul|ol)>)',
                re.IGNORECASE | re.DOTALL
            )
            match = pattern.search(content_html)
            if match:
                list_block = match.group(2)
                li_pattern = re.compile(r'<li[^>]*>(.*?)</li>', re.IGNORECASE | re.DOTALL)
                li_items = li_pattern.findall(list_block)
                for i in range(0, len(li_items) - 1, 2):
                    q = li_items[i].strip()
                    a = li_items[i+1].strip()
                    faqs.append({
                        "question": q,
                        "answer": a
                    })
                content_html = pattern.sub('', content_html)
        
        # Metadata fields
        tag = raw.get("tag") or raw.get("category") or "Career"
        author = raw.get("author") or "Aditi Rao"
        
        # Author initials
        author_initials = ""
        if author:
            parts = author.split()
            if len(parts) >= 2:
                author_initials = (parts[0][0] + parts[1][0]).upper()
            elif len(parts) == 1:
                author_initials = parts[0][:2].upper()
        if not author_initials:
            author_initials = "AR"
            
        author_role = raw.get("author_role") or raw.get("author_title") or "Career Editor"
        read_time = raw.get("read_time") or raw.get("reading_time") or "8 min read"
        date = raw.get("date") or raw.get("published_date") or "Jan 12, 2026"
        author_bio = raw.get("author_bio") or "Aditi writes about careers, hiring and the economics of higher education. She has spent a decade advising working professionals on when — and whether — to go back to school."
        
        # Dynamic TOC from H2 and H3 blocks inside content_html
        toc = []
        if content_html:
            def replace_heading(m):
                tag = m.group(1)
                attrs = m.group(2)
                text = m.group(3)
                slug = text.lower()
                slug = re.sub(r'[^a-z0-9\s-]', '', slug)
                slug = re.sub(r'[\s-]+', '-', slug)
                slug = slug.strip('-')
                if slug:
                    href = f"#{slug}"
                    toc.append({"text": text, "href": href})
                    return f"<{tag}{attrs} id=\"{slug}\">{text}</{tag}>"
                return m.group(0)

            heading_pattern = re.compile(
                r'<(h[23])([^>]*)>(.*?)</\1>',
                re.IGNORECASE | re.DOTALL
            )
            content_html = heading_pattern.sub(replace_heading, content_html)

        if faqs:
            toc.append({"text": "FAQs", "href": "#faq"})

        if not toc:
            toc = [
                {"text": "The salary uplift is real", "href": "#the-salary-uplift-is-real"},
                {"text": "The real cost is time, not money", "href": "#the-real-cost-is-time-not-money"},
                {"text": "Recruiter perception has shifted", "href": "#recruiter-perception-has-shifted"},
                {"text": "When an online MBA wins", "href": "#when-an-online-mba-wins"},
                {"text": "The verdict", "href": "#the-verdict"}
            ]

        # Related posts fallback
        related = raw.get("related")
        if not related or not isinstance(related, list):
            related = [
                { "tag": 'Finance', "title": 'Online MBA fees & EMI options, fully explained', "meta": '5 min · Dec 2025' },
                { "tag": 'Career', "title": '8 high-growth roles after an online MBA', "meta": '9 min · Nov 2025' },
                { "tag": 'Guide', "title": 'How to choose the right MBA specialization', "meta": '6 min · Dec 2025' }
            ]

        hero_image_url = raw.get("hero_image_url") or raw.get("featured_image_url")

        return {
            "seo_title": raw.get("seo_title") or title,
            "meta_description": raw.get("meta_description") or excerpt,
            "site": self.site,
            "title": title,
            "excerpt": excerpt,
            "content_html": content_html,
            "tag": tag,
            "author": author,
            "author_initials": author_initials,
            "author_role": author_role,
            "read_time": read_time,
            "date": date,
            "author_bio": author_bio,
            "hero_image_url": hero_image_url,
            "toc": toc,
            "related": related,
            "toc_json": json.dumps(toc, ensure_ascii=False),
            "related_json": json.dumps(related, ensure_ascii=False),
            "faqs": faqs,
            "faqs_json": json.dumps(faqs, ensure_ascii=False),
        }
