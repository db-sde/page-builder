import asyncio
from io import BytesIO
import unittest
from unittest.mock import patch

from docx import Document
from fastapi import UploadFile

from main import IngestRequest, ingest_acf, parse_docx_endpoint


class PostParserPipelineTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
