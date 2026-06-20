import json
from datetime import datetime

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
            all_posts.append({
                "slug": slug,
                "title": data.get("title") or slug.replace("-", " ").title(),
                "excerpt": data.get("excerpt") or "",
                "tag": data.get("tag") or "Guide",
                "author": data.get("author") or "Editorial Team",
                "read_time": data.get("read_time") or "5 min read",
                "date": data.get("date") or "",
                "meta": f"{data.get('read_time', '5 min')} · {data.get('date', '')}".strip(" ·"),
                "href": f"{slug}.html",
            })

        # Featured = most recent (first), rest go to grid
        featured = all_posts[0] if all_posts else None
        grid_posts = all_posts[1:] if len(all_posts) > 1 else []

        # Fallback posts when workspace has no blog content yet
        if not all_posts:
            fallback = [
                {"tag": "Guide", "title": "How to choose the right MBA specialization", "excerpt": "Marketing, finance, HR or analytics? A practical framework to match a track to your goals.", "meta": "6 min · Dec 2025", "href": "#"},
                {"tag": "Finance", "title": "Online MBA fees & EMI options, fully explained", "excerpt": "Semester-wise, annual and one-time plans compared — plus how no-cost EMI actually works.", "meta": "5 min · Dec 2025", "href": "#"},
                {"tag": "Admissions", "title": f"{uni_name} Online MBA eligibility & admission, step by step", "excerpt": "Documents, deadlines and the exact portal flow.", "meta": "7 min · Nov 2025", "href": "#"},
                {"tag": "Career", "title": "8 high-growth roles after an online MBA", "excerpt": "From brand manager to business analyst — salaries, skills and positioning.", "meta": "9 min · Nov 2025", "href": "#"},
                {"tag": "Student Life", "title": "Balancing a full-time job with an online MBA", "excerpt": "Real routines from working students on managing weekend classes and assignments.", "meta": "6 min · Oct 2025", "href": "#"},
                {"tag": "Guide", "title": "Is an online degree valid for government jobs?", "excerpt": "What UGC entitlement means in practice for employment and higher studies.", "meta": "4 min · Oct 2025", "href": "#"},
            ]
            featured = fallback[0]
            grid_posts = fallback[1:]

        cat_labels = ["All", "Career", "Admissions", "Guide", "Finance", "Student Life"]

        return {
            "seo_title": f"{uni_name} Blog — MBA Guides & Career Insights",
            "meta_description": f"Guides, career advice and program insights from {uni_name} to help you choose and complete your online MBA.",
            "university_name": uni_name,
            "featured_post": featured,
            "grid_posts": grid_posts,
            "all_posts": all_posts,
            "cat_labels": cat_labels,
            "cat_labels_json": json.dumps(cat_labels, ensure_ascii=False),
            "featured_json": json.dumps(featured, ensure_ascii=False) if featured else "null",
            "posts_json": json.dumps(all_posts if all_posts else grid_posts, ensure_ascii=False),
        }
