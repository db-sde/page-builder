import unittest
from pathlib import Path

from jinja2 import Environment, meta

from core.field_definitions import build_field_state
from core.page_requirements import (
    PAGE_REQUIREMENTS,
    build_page_state,
    build_page_state_from_values,
    template_field_usage,
)


class PageRequirementTests(unittest.TestCase):
    def test_requirements_defined_for_all_source_page_types(self):
        self.assertEqual(
            set(PAGE_REQUIREMENTS), {"university", "course", "specialization", "blog"}
        )
        for page_type, sections in PAGE_REQUIREMENTS.items():
            with self.subTest(page_type=page_type):
                self.assertTrue(sections)
                required = [s for s in sections if s["required"]]
                expected = ["hero", "article"] if page_type == "blog" else ["hero"]
                self.assertEqual([s["section"] for s in required], expected)

    def test_unused_schema_fields_do_not_warn(self):
        # A university page with only the hero fields present. Faculty and the
        # dropped content fields exist in the schema but no template renders them.
        state = build_page_state_from_values(
            "university",
            {
                "university_name": "IGNOU",
                "hero_description": "A public open university.",
                "faculty_members": [{"member_name": "Dr X"}],
                "about_content": "<p>About</p>",
                "why_choose_content": "<p>Why</p>",
                "about_heading": "About IGNOU",
            },
            {"page_type": "university", "slug": "ignou", "university_slug": "ignou"},
        )
        unused = set(state["unused_schema_fields"])
        # Present-but-unused schema fields must be flagged unused (never warn).
        self.assertIn("faculty_members", unused)
        self.assertIn("about_content", unused)
        self.assertIn("about_heading", unused)
        self.assertNotIn("why_choose_content", unused)
        self.assertNotIn("facts", unused)
        # And they are not marked used-by-template.
        self.assertFalse(state["field_usage"]["faculty_members"]["used_by_template"])
        # Hero fields are used by the template.
        self.assertTrue(state["field_usage"]["university_name"]["used_by_template"])

    def test_hero_renderable_but_optional_section_incomplete(self):
        state = build_page_state_from_values(
            "course",
            {
                "program_name": "Online MBA",
                "university_name": "IGNOU",
                # no eligibility_content, no highlights
            },
            {"page_type": "course", "slug": "ignou-online-mba", "university_slug": "ignou"},
        )
        by_id = {s["section"]: s for s in state["sections"]}

        # Required hero section renders from real data.
        self.assertTrue(by_id["hero"]["renderable"])
        self.assertNotIn("hero", state["summary"]["required_sections_incomplete"])

        # About renders because hero_description is absent AND about_content is
        # absent -> the any-of group is unsatisfied -> not renderable.
        self.assertFalse(by_id["about"]["renderable"])
        self.assertIn(["about_content", "hero_description"], by_id["about"]["missing_required"])

    def test_about_any_of_group_satisfied_by_hero_description(self):
        state = build_page_state_from_values(
            "course",
            {"program_name": "Online MBA", "hero_description": "Flexible MBA."},
            {"page_type": "course", "slug": "ignou-online-mba", "university_slug": "ignou"},
        )
        by_id = {s["section"]: s for s in state["sections"]}
        self.assertTrue(by_id["about"]["renderable"])

    def test_no_sections_claim_fabricated_fallbacks(self):
        state = build_page_state_from_values(
            "course",
            {"program_name": "Online MBA"},
            {"page_type": "course", "slug": "ignou-online-mba", "university_slug": "ignou"},
        )
        self.assertEqual(state["summary"]["fabricated_sections"], [])

    def test_external_template_fields_have_explicit_owners(self):
        from core.page_blueprint import build_page_blueprint

        blueprint = build_page_blueprint("university")
        self.assertEqual(blueprint["external_fields"]["programs"]["source"], "WORKSPACE")
        self.assertEqual(blueprint["external_fields"]["features"]["source"], "WORKSPACE")
        self.assertEqual(blueprint["external_fields"]["canonical_url"]["source"], "DERIVED")

    def test_every_direct_template_variable_has_exactly_one_owner(self):
        from core.page_blueprint import build_page_blueprint

        templates_dir = Path(__file__).resolve().parents[1] / "templates"
        environment = Environment()
        for page_type in ("university", "course", "specialization", "blog"):
            with self.subTest(page_type=page_type):
                source = (templates_dir / f"{page_type}.html").read_text(encoding="utf-8")
                referenced = meta.find_undeclared_variables(environment.parse(source))
                blueprint = build_page_blueprint(page_type)
                page_fields = set(blueprint["fields"])
                external_fields = set(blueprint["external_fields"])
                self.assertFalse(page_fields & external_fields)
                self.assertEqual(referenced - page_fields - external_fields, set())

    def test_infrastructure_fields_never_counted_as_unused(self):
        field_state = build_field_state(
            "specialization",
            {"spec_name": "Finance"},
            {"page_type": "specialization", "slug": "ignou-mba-finance",
             "university_slug": "ignou", "parent_slug": "ignou-online-mba"},
        )
        state = build_page_state("specialization", field_state)
        unused = set(state["unused_schema_fields"])
        for infra in ("_meta", "page_type", "slug", "university_slug", "parent_slug"):
            self.assertNotIn(infra, unused)
            self.assertIn(infra, state["infrastructure_fields"])

    def test_does_not_mutate_field_state(self):
        field_state = build_field_state(
            "course", {"program_name": "Online MBA"},
            {"page_type": "course", "slug": "x", "university_slug": "ignou"},
        )
        snapshot = {k: dict(v) for k, v in field_state.items()}
        build_page_state("course", field_state)
        self.assertEqual(field_state, snapshot)

    def test_blog_page_state_tracks_article_and_featured_image(self):
        field_state = build_field_state("blog", {
            "title": "Post",
            "content_html": "<p>Article body</p>",
            "hero_image_url": "/assets/images/blog.webp",
        }, {"page_type": "blog", "slug": "post", "university_slug": "ignou"})
        state = build_page_state("blog", field_state)
        self.assertTrue(next(section for section in state["sections"] if section["section"] == "article")["renderable"])
        self.assertEqual(state["summary"]["required_sections_incomplete"], [])

    def test_field_usage_map_matches_sections(self):
        usage = template_field_usage("specialization")
        self.assertIn("exam_content", usage)
        self.assertEqual(usage["exam_content"], ["exam"])
        # Workspace siblings are preferred, but the schema field is the real
        # fallback when no published sibling page exists.
        self.assertEqual(usage["other_specs"], ["other_specs"])


if __name__ == "__main__":
    unittest.main()
