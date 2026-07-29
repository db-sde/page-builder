import base64
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image

from main import save_base64_image
from workspace.image_optimizer import optimize_images_pipeline, optimize_uploaded_image


class UploadImageOptimizationTests(unittest.TestCase):
    @staticmethod
    def png_bytes(width=3000, height=1500):
        image = Image.new("RGB", (width, height), "#6B4FC9")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_upload_is_resized_and_stored_as_webp(self):
        with tempfile.TemporaryDirectory() as directory:
            result = optimize_uploaded_image(
                self.png_bytes(), Path(directory), "hero", ".png"
            )
            with Image.open(result["path"]) as image:
                self.assertEqual(image.format, "WEBP")
                self.assertEqual(image.size, (1920, 960))

        self.assertTrue(result["optimized"])
        self.assertEqual(result["original_dimensions"], (3000, 1500))

    def test_base64_upload_uses_the_same_optimized_source_format(self):
        encoded = base64.b64encode(self.png_bytes()).decode("ascii")
        with tempfile.TemporaryDirectory() as directory:
            asset_path = save_base64_image(
                f"data:image/png;base64,{encoded}", Path(directory), "course-hero"
            )
            saved = Path(directory) / "course-hero.webp"
            self.assertEqual(asset_path, "/assets/images/course-hero.webp")
            self.assertTrue(saved.exists())

    def test_build_pipeline_generates_responsive_variants_from_webp_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            destination = root / "build"
            optimize_uploaded_image(self.png_bytes(), source, "hero", ".png")

            stats = optimize_images_pipeline(source, destination)

            self.assertIn("hero.webp", stats)
            for name in ("hero.webp", "hero-480.webp", "hero-768.webp", "hero-1200.webp"):
                self.assertTrue((destination / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
