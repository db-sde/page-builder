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
        
        # Dynamic TOC from H2 and H3 blocks
        blocks = raw.get("blocks", [])
        toc = []
        if isinstance(blocks, list):
            for b in blocks:
                if isinstance(b, dict) and b.get("type") in ("h2", "h3") and b.get("text"):
                    toc.append(b["text"])
        if not toc:
            toc = [
                'The salary uplift is real',
                'The real cost is time, not money',
                'Recruiter perception has shifted',
                'When an online MBA wins',
                'The verdict'
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
        }
