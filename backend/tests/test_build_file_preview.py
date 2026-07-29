import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import build_file_endpoint


class BuildFilePreviewTests(unittest.TestCase):
    def test_serving_a_built_preview_never_triggers_a_full_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build_dir = root / "alpha" / "build"
            build_dir.mkdir(parents=True)
            (build_dir / "index.html").write_text(
                "<html><body><a href=\"/programs\">Programs</a></body></html>",
                encoding="utf-8",
            )

            with patch("main.WORKSPACES_ROOT", root), patch(
                "main.compile_workspace", side_effect=AssertionError("preview compiled workspace")
            ), patch(
                "main.build_website", side_effect=AssertionError("preview exported workspace")
            ):
                response = asyncio.run(build_file_endpoint("alpha", "index.html"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Programs", response.body)
        self.assertIn(b"/build-file?university_slug=", response.body)
        self.assertIn(b"encodeURIComponent('alpha')", response.body)


if __name__ == "__main__":
    unittest.main()
