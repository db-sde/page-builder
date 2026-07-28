import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.utils import build_public_route
from renderer.engine import env, render_resolved
from transformers.contact import ContactTransformer
from workspace.builder import _build_route_map
from workspace.manager import SYSTEM_PAGE_SLUGS, SYSTEM_PAGE_TYPES


class ContactPageTests(unittest.TestCase):
    def test_contact_is_a_system_page_with_a_fixed_public_route(self):
        self.assertIn("contact", SYSTEM_PAGE_TYPES)
        self.assertEqual(SYSTEM_PAGE_SLUGS["contact"], "contact")
        self.assertEqual(build_public_route("contact"), "/contact")

    def test_contact_transformer_reads_only_its_workspace_webhook(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for slug, webhook in (("alpha", "https://webhook.example/alpha"), ("beta", "https://webhook.example/beta")):
                workspace = root / slug
                workspace.mkdir()
                (workspace / "metadata.json").write_text(json.dumps({
                    "contact_webhook": webhook,
                    "contact": {"phone": "1800 000 0000"},
                }), encoding="utf-8")

            with patch("transformers.contact.WORKSPACES_ROOT", root):
                alpha = ContactTransformer({"university_slug": "alpha", "raw": {"university_name": "Alpha"}}).transform()
                beta = ContactTransformer({"university_slug": "beta", "raw": {"university_name": "Beta"}}).transform()

        self.assertEqual(alpha["contact_webhook"], "https://webhook.example/alpha")
        self.assertEqual(beta["contact_webhook"], "https://webhook.example/beta")
        self.assertEqual(alpha["contact_phone"], "1800 000 0000")

    def test_contact_transformer_uses_published_workspace_courses_for_program_options(self):
        result = ContactTransformer({
            "university_slug": "alpha",
            "raw": {
                "university_name": "Alpha",
                "_workspace_courses": [
                    {"slug": "alpha-online-mca", "data": {"program_name": "Alpha Online MCA"}},
                    {"slug": "alpha-online-mba", "data": {"course_name": "Alpha Online MBA"}},
                ],
            },
        }).transform()

        self.assertEqual(result["contact_programs"], [
            {"name": "Alpha Online MBA", "slug": "alpha-online-mba"},
            {"name": "Alpha Online MCA", "slug": "alpha-online-mca"},
        ])

    def test_contact_page_without_webhook_keeps_the_form_visible_but_disables_submission(self):
        html = render_resolved({
            "page_type": "contact",
            "slug": "contact",
            "university_slug": "contact-test",
            "parent_slug": None,
            "raw": {"university_name": "Contact Test University"},
        })
        self.assertIn("Online enquiry submission is not configured", html)
        self.assertIn('class="contact-form"', html)
        self.assertNotIn("data-workspace-contact-form", html)
        self.assertIn("Submission Not Configured", html)

    def test_contact_template_keeps_the_configured_webhook_in_the_static_form(self):
        html = env.get_template("contact.html").render(
            seo_title="Contact Alpha",
            meta_description="Contact Alpha.",
            university_name="Alpha",
            university_letter="A",
            site={"topbar_text": "Admissions open", "footer_columns": [], "email": "", "address": "", "copyright": ""},
            contact_webhook="https://webhook.example/alpha",
            contact_phone="",
            contact_email="",
            contact_address="",
            contact_working_hours="",
            contact_whatsapp="",
            contact_programs=[{"name": "Alpha Online MBA", "slug": "alpha-online-mba"}],
            homepage_href="/",
            programs_listing_href="/programs",
            specs_listing_href="/specializations",
            blog_listing_href="/blog",
            contact_href="/contact",
            branding_logo="",
            branding_favicon="",
            canonical_url="https://alpha.example/contact",
        )
        self.assertIn('data-contact-webhook="https://webhook.example/alpha"', html)
        self.assertIn("data-workspace-contact-form", html)
        self.assertIn('value="Alpha Online MBA"', html)
        self.assertNotIn('value="MBA" selected', html)

    def test_build_route_map_includes_contact(self):
        index = {page_type: {} for page_type in (
            "university", "course", "specialization", "blog",
            "programs_listing", "specializations_listing", "blog_listing", "contact",
        )}
        index["university"]["alpha"] = {"slug": "alpha"}
        routes, errors = _build_route_map(index, "alpha")
        self.assertEqual(errors, [])
        self.assertEqual(routes["contact"], "/contact")


if __name__ == "__main__":
    unittest.main()
