import unittest

from core.field_definitions import (
    AUTO,
    DERIVED,
    MANUAL,
    PAGE_FIELD_DEFINITIONS,
    build_field_state,
)
from ingestion.adapter import adapt_schema


class FieldDefinitionTests(unittest.TestCase):
    def test_every_definition_has_complete_ownership_metadata(self):
        for page_type, fields in PAGE_FIELD_DEFINITIONS.items():
            with self.subTest(page_type=page_type):
                self.assertTrue(fields)
            for name, definition in fields.items():
                with self.subTest(page_type=page_type, field=name):
                    self.assertIn(definition["source"], {AUTO, MANUAL, DERIVED})
                    self.assertEqual(definition["optional"], not definition["required"])
                    self.assertEqual(definition["manual"], definition["source"] == MANUAL)
                    self.assertEqual(definition["derived"], definition["source"] == DERIVED)

    def test_micro_app_schema_fields_are_defined(self):
        expected = {
            "university": {
                "_meta", "university_name", "university_full_name", "hero_description",
                "established_year", "naac_grade", "ugc_approved", "mode_of_learning",
                "starting_fee", "num_programs", "about_heading", "why_choose_heading",
                "facts_heading", "accreditations_heading", "programs_heading",
                "admission_heading", "emi_heading", "exam_heading", "faculty_heading",
                "placement_heading", "reviews_heading", "faqs_heading", "about_content",
                "why_choose_content", "admission_steps", "admission_fee_note", "emi_content",
                "exam_content", "faculty_intro", "placement_content", "facts",
                "accreditations", "programs_table", "faculty_members", "reviews", "faqs",
                "seo_title", "meta_description", "programs_intro",
            },
            "course": {
                "_meta", "program_name", "university_name", "linked_university",
                "hero_description", "duration", "mode", "naac_grade", "ugc_status",
                "total_fee", "num_specializations", "about_heading", "highlights_heading",
                "accreditations_heading", "specializations_heading", "fee_heading",
                "eligibility_heading", "admission_heading", "syllabus_heading",
                "placement_heading", "jobs_heading", "faqs_heading", "about_content",
                "specializations_intro", "eligibility_content", "admission_steps",
                "admission_fee_note", "syllabus_content", "placement_content",
                "certificate_description", "validity", "emi_amount", "highlights",
                "fee_plans", "job_profiles", "reviews", "faqs", "seo_title",
                "meta_description", "starting_fee", "eligibility_summary",
            },
            "specialization": {
                "_meta", "spec_name", "university_name", "linked_university",
                "linked_course", "duration", "mode", "naac_grade", "ugc_status",
                "total_fee", "about_heading", "highlights_heading", "eligibility_heading",
                "fee_heading", "other_specs_heading", "syllabus_heading", "exam_heading",
                "admission_heading", "placement_heading", "jobs_heading",
                "certificate_heading", "faqs_heading", "about_content",
                "eligibility_content", "syllabus_content", "exam_content",
                "admission_steps", "admission_fee_note", "placement_content",
                "certificate_description", "emi_amount", "highlights", "other_specs",
                "job_profiles", "reviews", "faqs", "seo_title", "meta_description",
                "eligibility_summary",
            },
        }

        for page_type, fields in expected.items():
            with self.subTest(page_type=page_type):
                self.assertTrue(fields.issubset(PAGE_FIELD_DEFINITIONS[page_type]))

    def test_state_reports_missing_manual_and_derived_fields(self):
        state = build_field_state(
            "course",
            {
                "program_name": "Online MBA",
                "reviews": [],
                "parser_extension": "retained",
            },
            {
                "page_type": "course",
                "slug": "ignou-online-mba",
                "university_slug": "ignou",
                "parent_slug": None,
            },
        )

        self.assertFalse(state["program_name"]["missing"])
        self.assertTrue(state["hero_description"]["missing"])
        self.assertTrue(state["hero_description"]["required"])
        self.assertEqual(state["reviews"]["source"], MANUAL)
        self.assertTrue(state["reviews"]["manual"])
        self.assertTrue(state["reviews"]["optional"])
        self.assertEqual(state["slug"]["value"], "ignou-online-mba")
        self.assertTrue(state["slug"]["derived"])
        self.assertEqual(state["parser_extension"]["source"], AUTO)
        self.assertEqual(state["parser_extension"]["value"], "retained")

    def test_state_does_not_mutate_structured_values(self):
        reviews = [{"review_text": "Useful course"}]
        values = {"reviews": reviews}

        state = build_field_state("specialization", values)

        self.assertIs(state["reviews"]["value"], reviews)
        self.assertEqual(values, {"reviews": reviews})

    def test_unsupported_page_type_has_no_field_contract(self):
        self.assertEqual(build_field_state("blog", {"title": "Post"}), {})

    def test_university_ugc_alias_normalizes_to_canonical_field(self):
        adapted = adapt_schema({"ugc_status": "UGC-DEB Entitled"}, "university")
        self.assertEqual(adapted["ugc_approved"], "UGC-DEB Entitled")
        self.assertNotIn("ugc_status", adapted)


if __name__ == "__main__":
    unittest.main()
