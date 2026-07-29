import asyncio
from io import BytesIO
import unittest
from unittest.mock import patch

from docx import Document
from fastapi import HTTPException, UploadFile

from main import IngestRequest, ingest_acf, parse_docx_endpoint, validate_blueprint_content
from renderer.engine import clean_spec_name, parse_admission_html


class PostParserPipelineTests(unittest.TestCase):
    def test_endpoint_validation_reports_all_blueprint_required_fields(self):
        with self.assertRaises(HTTPException) as context:
            validate_blueprint_content(
                "course",
                {"program_name": "Online MBA"},
                slug="ignou-online-mba",
                university_slug="ignou",
                parent_slug=None,
            )

        self.assertEqual(context.exception.status_code, 422)
        missing = {
            entry["field"] for entry in context.exception.detail["missing_fields"]
        }
        self.assertIn("hero_description", missing)
        self.assertIn("duration", missing)
        self.assertIn("total_fee", missing)
        self.assertIn("hero_image_url", missing)
        self.assertIn("certificate_image_url", missing)

    def test_legacy_blog_image_requirement_is_preserved(self):
        with self.assertRaises(HTTPException) as context:
            validate_blueprint_content(
                "blog",
                {"title": "An article"},
                slug="an-article",
                university_slug="ignou",
                parent_slug=None,
            )

        self.assertEqual(context.exception.status_code, 422)
        self.assertEqual(
            context.exception.detail["missing_fields"],
            [{"field": "hero_image_url", "label": "Article Hero Image"}],
        )

    def test_ingest_response_carries_field_state_without_changing_acf_data(self):
        payload = {
            "page_type": "university",
            "slug": "ignou",
            "university_slug": "ignou",
            "university_name": "IGNOU",
            "hero_description": "A public open university.",
        }

        result = asyncio.run(ingest_acf(IngestRequest(acf_data=payload)))

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["acf_data"]["hero_description"], payload["hero_description"])
        self.assertEqual(result["field_state"]["slug"]["value"], "ignou")
        self.assertTrue(result["field_state"]["hero_image_url"]["missing"])
        self.assertTrue(result["field_state"]["hero_image_url"]["manual"])

        # Phase 2: page_state rides alongside field_state without touching acf_data.
        page_state = result["page_state"]
        self.assertEqual(page_state["page_type"], "university")
        hero = next(s for s in page_state["sections"] if s["section"] == "hero")
        self.assertTrue(hero["renderable"])  # name + description present
        # hero_image_url is required by the builder but optional to the template.
        self.assertIn("hero_image_url", hero["missing_optional"])

    def test_course_docx_response_builds_state_after_parser_result(self):
        document = Document()
        document.add_heading("Online MBA", level=1)
        document.add_paragraph("A flexible management programme.")
        buffer = BytesIO()
        document.save(buffer)
        buffer.seek(0)
        upload = UploadFile(filename="online-mba.docx", file=buffer)
        micro_result = {
            "filename": "online-mba.docx",
            "payload": {
                "program_name": "Online MBA",
                "university_name": "IGNOU",
                "hero_description": "A flexible management programme.",
                "reviews": [],
            },
        }

        with patch("main.forward_to_micro_pipeline", return_value=micro_result):
            result = asyncio.run(
                parse_docx_endpoint(
                    file=upload,
                    page_type="course",
                    university_slug="ignou",
                )
            )

        self.assertEqual(result["payload"]["program_name"], "Online MBA")
        self.assertEqual(result["field_state"]["university_slug"]["value"], "ignou")
        self.assertEqual(result["field_state"]["slug"]["value"], "ignou-online-mba")
        self.assertEqual(result["field_state"]["reviews"]["source"], "MANUAL")
        self.assertEqual(result["table_warnings"], [])

    def test_explicit_identity_marker_overrides_conflicting_micro_value(self):
        document = Document()
        document.add_heading("[university_name] LPU Online", level=1)
        document.add_paragraph("University Full Name: Lovely Professional University Online")
        document.add_paragraph("NAAC Grade: A++")
        buffer = BytesIO()
        document.save(buffer)
        buffer.seek(0)
        upload = UploadFile(filename="lpu.docx", file=buffer)
        micro_result = {
            "filename": "lpu.docx",
            "payload": {
                "university_name": "Lovely Professional Online",
                "hero_description": "Online learning programmes.",
                "naac_grade": "A++",
                "ugc_approved": "Entitled",
            },
        }

        with patch("main.forward_to_micro_pipeline", return_value=micro_result):
            result = asyncio.run(
                parse_docx_endpoint(
                    file=upload,
                    page_type="university",
                    university_slug="lpu",
                )
            )

        self.assertEqual(result["payload"]["university_name"], "LPU Online")

    def test_admission_note_sections_do_not_become_numbered_steps(self):
        steps = parse_admission_html(
            "<p>Step 1. Register online.</p>"
            "<p>Step 2. Submit the application.</p>"
            "<h4>Important Notes:</h4>"
            "<ul><li>The registration fee is non-refundable.</li></ul>"
        )

        self.assertEqual([step["t"] for step in steps], [
            "Register online.",
            "Submit the application.",
        ])

    def test_specialization_display_name_omits_parenthetical_parser_suffixes(self):
        self.assertEqual(clean_spec_name("Finance (Fin"), "Finance")
        self.assertEqual(clean_spec_name("Information Technology (IT)"), "Information Technology")


if __name__ == "__main__":
    unittest.main()
