import unittest

from core.editing_state import apply_auto_population, build_editing_state
from core.page_blueprint import SUPPORTED_PAGE_TYPES, build_page_blueprint


DERIVED = {
    "page_type": "course",
    "slug": "ignou-online-mba",
    "university_slug": "ignou",
    "parent_slug": None,
}


class PageBlueprintTests(unittest.TestCase):
    def test_blueprint_exists_for_supported_page_types(self):
        for page_type in SUPPORTED_PAGE_TYPES:
            with self.subTest(page_type=page_type):
                bp = build_page_blueprint(page_type)
                self.assertTrue(bp["sections"])
                self.assertTrue(bp["fields"])
                # Sections carry an explicit order.
                self.assertEqual(
                    [s["order"] for s in bp["sections"]],
                    list(range(len(bp["sections"]))),
                )

    def test_blueprint_classifies_image_manual_and_derived_fields(self):
        bp = build_page_blueprint("course")
        self.assertEqual(bp["image_fields"], ["certificate_image_url", "hero_image_url"])
        self.assertIn("hero_image_url", bp["manual_fields"])
        self.assertIn("reviews", bp["manual_fields"])
        self.assertIn("slug", bp["derived_fields"])
        # Image fields carry upload metadata for the editor.
        self.assertEqual(bp["fields"]["hero_image_url"]["label"], "Hero Image")

    def test_blueprint_marks_template_usage_without_dropping_schema_fields(self):
        bp = build_page_blueprint("university")
        # Schema keeps faculty; the template does not use it.
        self.assertIn("faculty_members", bp["fields"])
        self.assertFalse(bp["fields"]["faculty_members"]["used_by_template"])
        self.assertNotIn("faculty_members", bp["template_fields"])

    def test_unsupported_page_type(self):
        self.assertEqual(build_page_blueprint("blog"), {})


class AutoPopulationTests(unittest.TestCase):
    def test_declared_defaults_are_applied_without_mutating_input(self):
        values = {"program_name": "Online MBA"}
        populated, auto_filled = apply_auto_population("course", values)
        self.assertEqual(populated["mode"], "100% Online")
        self.assertEqual(auto_filled, ["mode"])
        self.assertNotIn("mode", values)

    def test_parser_value_wins_over_default(self):
        populated, auto_filled = apply_auto_population("course", {"mode": "Hybrid"})
        self.assertEqual(populated["mode"], "Hybrid")
        self.assertEqual(auto_filled, [])

    def test_no_editorial_content_is_ever_auto_filled(self):
        populated, _ = apply_auto_population("course", {})
        for fabricated in ("reviews", "faqs", "job_profiles", "syllabus_content", "fee_plans"):
            self.assertNotIn(fabricated, populated)


class EditingStateTests(unittest.TestCase):
    def test_editor_only_sees_fields_that_need_attention(self):
        state = build_editing_state("course", {
            "program_name": "Online MBA",
            "university_name": "IGNOU",
            "hero_description": "Flexible management degree.",
            "duration": "2 Years",
            "naac_grade": "A++",
            "ugc_status": "UGC-DEB approved",
            "total_fee": "INR 1,65,000",
        }, DERIVED)

        # Only the two uploaded images remain.
        self.assertEqual(state["needs_attention"], ["certificate_image_url", "hero_image_url"])
        self.assertEqual(state["missing_images"], ["certificate_image_url", "hero_image_url"])
        self.assertFalse(state["summary"]["ready"])
        # mode was auto-filled, so the operator is never asked for it.
        self.assertIn("mode", state["auto_filled"])
        self.assertFalse(state["fields"]["mode"]["missing"])

    def test_page_is_ready_once_images_are_supplied(self):
        state = build_editing_state("course", {
            "program_name": "Online MBA",
            "university_name": "IGNOU",
            "hero_description": "Flexible management degree.",
            "duration": "2 Years",
            "naac_grade": "A++",
            "ugc_status": "UGC-DEB approved",
            "total_fee": "INR 1,65,000",
            "hero_image_url": "/assets/images/hero.jpg",
            "certificate_image_url": "/assets/images/cert.jpg",
        }, DERIVED)
        self.assertEqual(state["needs_attention"], [])
        self.assertTrue(state["summary"]["ready"])

    def test_unused_schema_fields_never_need_attention(self):
        state = build_editing_state("university", {
            "university_name": "IGNOU",
            "hero_description": "A public open university.",
            "hero_image_url": "/assets/images/hero.jpg",
            "naac_grade": "A++",
            "ugc_approved": "Entitled",
        }, {"page_type": "university", "slug": "ignou", "university_slug": "ignou"})

        self.assertTrue(state["summary"]["ready"])
        # Faculty is unused by the template: reported, never demanded.
        self.assertIn("faculty_members", state["unused_schema_fields"])
        self.assertNotIn("faculty_members", state["needs_attention"])
        self.assertFalse(state["fields"]["faculty_members"]["needs_attention"])

    def test_manual_optional_fields_are_suggestions_not_warnings(self):
        state = build_editing_state("specialization", {
            "spec_name": "Finance",
            "university_name": "IGNOU",
            "hero_description": "Applied finance track.",
            "duration": "2 Years",
            "naac_grade": "A++",
            "ugc_status": "Approved",
            "total_fee": "INR 1,00,000",
            "hero_image_url": "/assets/images/hero.jpg",
        }, {"page_type": "specialization", "slug": "s", "university_slug": "ignou",
            "parent_slug": "ignou-online-mba"})
        self.assertIn("reviews", state["optional_suggestions"])
        self.assertNotIn("reviews", state["needs_attention"])
        self.assertTrue(state["summary"]["ready"])

    def test_sections_report_completion_and_renderability(self):
        state = build_editing_state("course", {"program_name": "Online MBA"}, DERIVED)
        by_id = {s["section"]: s for s in state["sections"]}
        self.assertTrue(by_id["hero"]["renderable"])
        self.assertFalse(by_id["about"]["renderable"])
        self.assertIsNotNone(by_id["hero"]["completion"])
        self.assertIn("program_name", by_id["hero"]["filled_fields"])

    def test_unsupported_page_type(self):
        self.assertEqual(build_editing_state("blog", {"title": "Post"}), {})


if __name__ == "__main__":
    unittest.main()
