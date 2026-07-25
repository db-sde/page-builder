import unittest

from core.field_definitions import build_field_state
from core.page_requirements import (
    PAGE_REQUIREMENTS,
    build_page_state,
    build_page_state_from_values,
    template_field_usage,
)


class PageRequirementTests(unittest.TestCase):
    def test_requirements_defined_for_the_three_page_types(self):
        self.assertEqual(
            set(PAGE_REQUIREMENTS), {"university", "course", "specialization"}
        )
        for page_type, sections in PAGE_REQUIREMENTS.items():
            with self.subTest(page_type=page_type):
                self.assertTrue(sections)
                # Exactly one essential section per page: the hero.
                required = [s for s in sections if s["required"]]
                self.assertEqual([s["section"] for s in required], ["hero"])

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
        self.assertIn("why_choose_content", unused)
        self.assertIn("about_heading", unused)
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

    def test_fabricated_sections_are_flagged_for_next_phase(self):
        state = build_page_state_from_values(
            "course",
            {"program_name": "Online MBA"},
            {"page_type": "course", "slug": "ignou-online-mba", "university_slug": "ignou"},
        )
        fabricated = set(state["summary"]["fabricated_sections"])
        # These render fabricated content when their real fields are empty.
        for section_id in ("fees", "syllabus", "jobs", "reviews", "faqs", "admission"):
            self.assertIn(section_id, fabricated)

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

    def test_unsupported_page_type_has_no_page_contract(self):
        field_state = build_field_state("blog", {"title": "Post"})
        self.assertEqual(build_page_state("blog", field_state), {})

    def test_field_usage_map_matches_sections(self):
        usage = template_field_usage("specialization")
        self.assertIn("exam_content", usage)
        self.assertEqual(usage["exam_content"], ["exam"])
        # other_specs is workspace-driven; the schema field is not template-used.
        self.assertNotIn("other_specs", usage)


if __name__ == "__main__":
    unittest.main()
