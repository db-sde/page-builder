"""Workspace-derived Blog listing data with no demo-post fallback."""

from core.blog import reading_time_label
from transformers.base import BaseTransformer


class BlogListingTransformer(BaseTransformer):
    def transform(self) -> dict:
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
                "image": data.get("hero_image_url") or data.get("featured_image_url") or "",
                "href": self.public_route("blog", slug),
            })

        return {
            "site": self.site,
            "title": "Blog",
            "posts": posts,
            "featured_post": posts[0] if posts else None,
            "categories": sorted({post["tag"] for post in posts if post["tag"]}),
        }
