"""Workspace-derived Blog listing data with no demo-post fallback."""

import re

from core.blog import reading_time_label
from transformers.base import BaseTransformer


class BlogListingTransformer(BaseTransformer):
    def transform(self) -> dict:
        university_name = self.resolve("university_name") or self.university_slug.replace("-", " ").title()
        online_name = university_name if re.search(r"\bonline\b", university_name, re.IGNORECASE) else f"{university_name} Online"
        posts = []
        for record in self.raw.get("_workspace_blogs") or []:
            if not isinstance(record, dict):
                continue
            data = record.get("data") or {}
            slug = record.get("slug") or ""
            title = str(data.get("title") or "").strip()
            if not slug or not title:
                continue
            posts.append({
                "title": title,
                "excerpt": str(data.get("excerpt") or data.get("subtitle") or "").strip(),
                "tag": str(data.get("category") or "").strip(),
                "author": str(data.get("author") or "").strip(),
                "date": str(data.get("published_date") or data.get("date") or "").strip(),
                "read_time": reading_time_label(data.get("content_html"), data.get("read_time_override")),
                "hero_image_url": data.get("hero_image_url") or data.get("featured_image_url") or "",
                "href": self.public_route("blog", slug),
            })

        return {
            "site": self.site,
            "seo_title": f"{online_name} Blog",
            "meta_description": f"Read {online_name} guides, admissions information and program insights.",
            "university_name": university_name,
            "blog_posts": posts,
            # Keep these aliases for consumers that use the transformer
            # directly, while the static listing template uses blog_posts.
            "posts": posts,
            "featured_post": posts[0] if posts else None,
            "categories": sorted({post["tag"] for post in posts if post["tag"]}),
        }
