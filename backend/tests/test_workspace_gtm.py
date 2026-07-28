import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workspace.builder import _finalize_html


class WorkspaceGtmTests(unittest.TestCase):
    html = "<!doctype html><html><head><title>Page</title></head><body class=\"page\"><main>Content</main></body></html>"

    def render(self, gtm):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "metadata.json").write_text(
                json.dumps({"gtm": gtm}), encoding="utf-8"
            )
            with patch("workspace.builder._workspace_root", return_value=workspace):
                return _finalize_html(self.html, "test-workspace")

    def test_disabled_gtm_does_not_change_html(self):
        result = self.render({"enabled": False, "head": "<script>head</script>", "body_start": "<noscript>body</noscript>"})
        self.assertEqual(result, self.html)

    def test_enabled_gtm_injects_verbatim_at_head_and_body_start(self):
        head = "\n<!-- workspace head -->\n<script>window.example = true;</script>"
        body_start = "\n<noscript>workspace body</noscript>"
        result = self.render({"enabled": True, "head": head, "body_start": body_start})

        self.assertIn(head, result)
        self.assertIn(body_start, result)
        self.assertEqual(result.index(head), result.index("<head>") + len("<head>"))
        self.assertEqual(result.index(body_start), result.index('<body class="page">') + len('<body class="page">'))

    def test_workspaces_can_use_different_snippets(self):
        first = self.render({"enabled": True, "head": "<script>first</script>", "body_start": ""})
        second = self.render({"enabled": True, "head": "<script>second</script>", "body_start": ""})
        self.assertIn("<script>first</script>", first)
        self.assertNotIn("<script>second</script>", first)
        self.assertIn("<script>second</script>", second)
        self.assertNotIn("<script>first</script>", second)

    def test_missing_gtm_configuration_does_not_change_html(self):
        self.assertEqual(self.render({}), self.html)

