import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from workspace.manager import load_metadata
from main import upload_branding_endpoint


class WorkspaceContactWebhookTests(unittest.TestCase):
    def test_legacy_metadata_loads_with_an_empty_contact_webhook(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "alpha"
            workspace.mkdir()
            (workspace / "metadata.json").write_text(
                json.dumps({"university_slug": "alpha"}), encoding="utf-8"
            )
            with patch("workspace.manager.WORKSPACES_ROOT", root):
                metadata = load_metadata("alpha")

        self.assertEqual(metadata["contact_webhook"], "")

    def test_empty_and_valid_webhooks_save_without_a_logo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "alpha").mkdir()
            with patch("main.WORKSPACES_ROOT", root), patch(
                "workspace.manager.WORKSPACES_ROOT", root
            ), patch("main.compile_workspace", return_value={"pages_compiled": 0}), patch(
                "main.sync_workspace_after_change", new_callable=AsyncMock, return_value={"enabled": False}
            ):
                empty = asyncio.run(
                    upload_branding_endpoint(
                        "alpha", logo=None, favicon=None, primary_domain=None, default_og_image=None, contact_webhook=""
                    )
                )
                saved = asyncio.run(
                    upload_branding_endpoint(
                        "alpha",
                        logo=None,
                        favicon=None,
                        primary_domain=None,
                        default_og_image=None,
                        contact_webhook="https://connect.pabbly.com/webhook-listener/example",
                    )
                )

                self.assertEqual(empty["contact_webhook"], "")
                self.assertEqual(saved["contact_webhook"], "https://connect.pabbly.com/webhook-listener/example")
                self.assertEqual(
                    load_metadata("alpha")["contact_webhook"],
                    "https://connect.pabbly.com/webhook-listener/example",
                )

    def test_invalid_webhook_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "alpha").mkdir()
            with patch("main.WORKSPACES_ROOT", root), patch(
                "workspace.manager.WORKSPACES_ROOT", root
            ):
                with self.assertRaises(HTTPException) as error:
                    asyncio.run(
                        upload_branding_endpoint(
                            "alpha", logo=None, favicon=None, primary_domain=None, default_og_image=None, contact_webhook="webhook.example"
                        )
                    )

        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("http:// or https://", error.exception.detail)


if __name__ == "__main__":
    unittest.main()
