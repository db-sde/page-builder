import base64
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image

from main import save_base64_image
from renderer.engine import webp_variant_filter
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

    def test_identical_uploads_share_one_physical_source_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            image = self.png_bytes(800, 400)
            first = optimize_uploaded_image(image, Path(directory), "hero", ".png")
            second = optimize_uploaded_image(image, Path(directory), "certificate", ".png")

            self.assertTrue(second["deduplicated"])
            self.assertNotEqual(first["path"], second["path"])
            self.assertTrue(first["path"].samefile(second["path"]))

    def test_upload_deduplicates_against_an_unindexed_legacy_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            image = self.png_bytes(800, 400)
            legacy = Path(directory) / "legacy.png"
            legacy.write_bytes(image)

            result = optimize_uploaded_image(image, Path(directory), "hero", ".png")

            self.assertTrue(result["deduplicated"])
            self.assertEqual(result["path"], legacy)
            self.assertFalse((Path(directory) / "hero.webp").exists())

    def test_small_sources_only_receive_useful_responsive_variants(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            destination = root / "build"
            optimize_uploaded_image(self.png_bytes(600, 300), source, "hero", ".png")

            stats = optimize_images_pipeline(source, destination)

            self.assertTrue((destination / "hero-480.webp").exists())
            self.assertFalse((destination / "hero-768.webp").exists())
            self.assertFalse((destination / "hero-1200.webp").exists())
            self.assertEqual([item["width"] for item in stats["hero.webp"]["variants"]], [480])

    def test_build_links_identical_legacy_sources_instead_of_reprocessing_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            destination = root / "build"
            source.mkdir()
            content = self.png_bytes(800, 400)
            (source / "hero-a.png").write_bytes(content)
            (source / "hero-b.png").write_bytes(content)

            optimize_images_pipeline(source, destination)

            self.assertTrue((destination / "hero-a-480.webp").samefile(destination / "hero-b-480.webp"))

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

    def test_preview_uses_uploaded_webp_source_before_static_variants_exist(self):
        image_url = "/assets/images/course-hero.webp"

        self.assertEqual(webp_variant_filter({"preview_mode": True}, image_url, 1200), image_url)
        self.assertEqual(webp_variant_filter({"preview_mode": True}, image_url), image_url)

    def test_preview_falls_back_to_legacy_non_webp_image(self):
        self.assertEqual(
            webp_variant_filter({"preview_mode": True}, "/assets/images/legacy-hero.jpg", 1200),
            "",
        )


if __name__ == "__main__":
    unittest.main()
