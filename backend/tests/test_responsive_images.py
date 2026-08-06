"""Responsive image pipeline: srcset generation, aspect ratios, asset URLs.

These guard the rules that let a content writer upload any reasonable image
without touching CSS:

* the srcset must only ever list variants the static build actually produces,
* it must use width descriptors so the browser can account for device pixel
  ratio (the old `<source media>` markup could not),
* the hero container must adopt the image's own aspect ratio inside a clamp,
* asset URLs must survive a stray capital in the stored path.
"""

import unittest
from unittest.mock import patch

from renderer.engine import (
    HERO_FALLBACK_RATIO,
    HERO_MAX_RATIO,
    HERO_MIN_RATIO,
    asset_url_filter,
    image_ratio_filter,
    image_srcset_filter,
)
from workspace.image_optimizer import RESPONSIVE_WIDTHS


class _Ctx(dict):
    """Minimal stand-in for a Jinja context (only .get is used)."""


def _srcset(url, dims, preview=False):
    ctx = _Ctx({"university_slug": "uni", "preview_mode": preview})
    with patch("renderer.engine._source_image_dimensions", return_value=dims):
        return image_srcset_filter(ctx, url)


def _ratio(url, dims):
    ctx = _Ctx({"university_slug": "uni"})
    with patch("renderer.engine._source_image_dimensions", return_value=dims):
        return image_ratio_filter(ctx, url)


class SrcsetTests(unittest.TestCase):
    def test_lists_only_variants_the_build_will_generate(self):
        # 1000px source: the build skips any variant not smaller than the source,
        # so 1200w must not be advertised.
        out = _srcset("/assets/images/hero.webp", (1000, 600))
        self.assertIn("/assets/images/hero-480.webp 480w", out)
        self.assertIn("/assets/images/hero-768.webp 768w", out)
        self.assertNotIn("1200", out)
        self.assertTrue(out.endswith("/assets/images/hero.webp 1000w"))

    def test_small_source_advertises_itself_only(self):
        out = _srcset("/assets/images/small.webp", (400, 300))
        self.assertEqual(out, "/assets/images/small.webp 400w")

    def test_every_entry_uses_a_width_descriptor(self):
        out = _srcset("/assets/images/hero.webp", (1600, 900))
        entries = [e.strip() for e in out.split(",")]
        self.assertEqual(len(entries), len(RESPONSIVE_WIDTHS) + 1)
        for entry in entries:
            self.assertRegex(entry, r"^\S+ \d+w$")

    def test_preview_uses_the_source_asset_because_variants_do_not_exist_yet(self):
        out = _srcset("/assets/images/hero.webp", (1600, 900), preview=True)
        self.assertEqual(out, "/assets/images/hero.webp 1600w")

    def test_unknown_dimensions_and_empty_url_are_safe(self):
        self.assertEqual(_srcset("/assets/images/x.webp", (0, 0)), "")
        self.assertEqual(_srcset("", (100, 100)), "")

    def test_stray_capital_in_stored_path_is_normalised(self):
        out = _srcset("/Assets/images/hero.webp", (1000, 600))
        self.assertNotIn("/Assets/", out)
        self.assertIn("/assets/images/hero-480.webp 480w", out)


class HeroRatioTests(unittest.TestCase):
    def test_container_adopts_the_image_ratio(self):
        self.assertEqual(_ratio("/assets/images/h.webp", (1600, 900)), "1.7778")
        self.assertEqual(_ratio("/assets/images/h.webp", (1448, 1086)), "1.3333")
        self.assertEqual(_ratio("/assets/images/h.webp", (1000, 1000)), "1")

    def test_extreme_ratios_are_clamped_into_the_band(self):
        panorama = float(_ratio("/assets/images/h.webp", (3000, 700)))
        portrait = float(_ratio("/assets/images/h.webp", (700, 1600)))
        self.assertEqual(panorama, HERO_MAX_RATIO)
        self.assertEqual(portrait, HERO_MIN_RATIO)

    def test_missing_image_falls_back_without_breaking_css(self):
        self.assertEqual(_ratio("/assets/images/h.webp", (0, 0)), HERO_FALLBACK_RATIO)
        self.assertEqual(_ratio("", (100, 100)), HERO_FALLBACK_RATIO)


class AssetUrlTests(unittest.TestCase):
    def test_normalises_only_the_known_directory_segment(self):
        self.assertEqual(
            asset_url_filter("/Assets/images/Hero-Photo.webp"),
            "/assets/images/Hero-Photo.webp",
        )
        self.assertEqual(
            asset_url_filter("/ASSETS/downloads/Brochure.pdf"),
            "/assets/downloads/Brochure.pdf",
        )

    def test_leaves_other_urls_untouched(self):
        for url in ("https://cdn.example.com/Assets/images/x.webp", "/media/x.webp", "", None):
            self.assertEqual(asset_url_filter(url), url)


if __name__ == "__main__":
    unittest.main()
