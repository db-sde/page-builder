import json
from datetime import datetime
from core.utils import build_public_route

class BlogListingTransformer:
    """
    Transformer for the auto-generated Blog Listing page.
    Reads `_workspace_blogs` injected by the compiler.
    """
    def __init__(self, resolved: dict):
        self.raw = resolved.get("raw") or {}
        self.university_slug = resolved.get("university_slug", "")

    def transform(self) -> dict:
        raw = self.raw
        uni_name = raw.get("university_name") or self.university_slug.replace("-", " ").title()

        blogs = raw.get("_workspace_blogs") or []

        all_posts = []
        for b in blogs:
            if not isinstance(b, dict):
                continue
            data = b.get("data", {})
            slug = b.get("slug", "")
            author_name = data.get("author") or "Editorial Team"
            all_posts.append({
                "slug": slug,
                "title": data.get("title") or slug.replace("-", " ").title(),
                "excerpt": data.get("excerpt") or "",
                "tag": data.get("tag") or "Guide",
                "author": author_name,
                "author_initial": author_name[0].upper() if author_name else "A",
                "read_time": data.get("read_time") or "5 min read",
                "date": data.get("date") or "",
                "meta": f"{data.get('read_time', '5 min')} · {data.get('date', '')}".strip(" ·"),
                "href": build_public_route("blog", slug, self.university_slug),
                "hero_image_url": data.get("hero_image_url") or "",
            })

        # All posts go directly to the grid, no separate featured layout
        featured = None
        blog_posts = all_posts

        cat_labels = ["All", "Career", "Admissions", "Guide", "Finance", "Student Life"]

        return {
            "seo_title": f"{uni_name} Blog — MBA Guides & Career Insights",
            "meta_description": f"Read {uni_name} online degree guides covering fees, admissions, program comparisons and career choices to make a confident higher-education decision.",
            "university_name": uni_name,
            "featured_post": featured,
            "blog_posts": blog_posts,
            "all_posts": all_posts,
            "cat_labels": cat_labels,
        }
