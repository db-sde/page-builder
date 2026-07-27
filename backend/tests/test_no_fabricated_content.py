"""Acceptance test for the Phase 3 fake-content removal.

NOTE: these render deliberately SPARSE pages. Markers must be strings that only
the removed hardcoded blocks contained — never generic subject names, recruiter
names or figures that can legitimately appear in real parsed content.

Renders a deliberately sparse page (only the few fields a thin DOCX would give)
and asserts that none of the previously hardcoded editorial content appears in
the output. See HARDCODED_CONTENT_AUDIT.md and memory/regressions.md REG-010.
"""

import unittest

from renderer.engine import render_resolved


# Strings that used to be injected when a field was empty.
FABRICATED = [
    # reviews
    "Sneha Kulkarni", "Rohit Verma", "Deepa Krishnan",
    # job profiles + salaries
    "HR Business Partner", "₹12.5 LPA", "₹9.8 LPA", "₹16.5 LPA",
    # recruiters
    "Indiamart", "Wockhardt", "Zalaris", "Milkbasket", "Shopx",
    # syllabus — markers unique to the removed hardcoded block. Do NOT add
    # generic subject names here ("Organisational Behaviour", "Capstone
    # Project"): those legitimately appear in real parsed syllabus content.
    "Information Systems for Managers", "Decision Science & Analytics",
    "Semester III (Specialization Electives)",
    "Semester IV (Specialization + Capstone)",
    # faqs
    "Is the Online MBA equivalent to a regular MBA?",
    "Term-end exams are online and remotely proctored",
    # fee plans
    "₹50,000 / semester", "₹96,000 / year", "₹1,80,000 once",
    # features / financing / banks
    "Industry-mentored capstone to apply your skills",
    "Defence scholarship", "Standard Chartered", "Kotak Mahindra", "₹8,334",
    # other specs comparison table (the invented fee figures are unique to it)
    "₹2,16,000", "₹2,08,000",
    # demo blog posts
    "How to choose the right MBA specialization",
    # university template claims
    "NIRF #24", "AIU Member", "WES Recognised",
    "one of India's most respected management institutions",
    "among India's highest-rated private universities",
    # specialization template claims
    "Most Popular Specialization", "₹14.2L", "Avg. salary after specialization",
    # misc
    "Highest Category Rating", "start with just ₹50,000",
    "Choose your specialization at the start of year two",
    "NMIMS Online. All rights reserved",
]


def _render(page_type, raw, **kw):
    resolved = {
        "slug": "test-page",
        "page_type": page_type,
        "university_slug": "test-uni",
        "parent_slug": kw.pop("parent_slug", None),
        "raw": raw,
    }
    return render_resolved(resolved, **kw)


class NoFabricatedContentTests(unittest.TestCase):
    def _assert_clean(self, html, page_type):
        for needle in FABRICATED:
            with self.subTest(page_type=page_type, needle=needle):
                self.assertNotIn(needle, html)

    def test_sparse_course_page_has_no_fabricated_content(self):
        html = _render("course", {
            "program_name": "Online MCA",
            "university_name": "Test University",
            "hero_description": "A postgraduate computer applications degree.",
        }, standalone=True)
        self._assert_clean(html, "course")
        # Real data still renders.
        self.assertIn("Online MCA", html)

    def test_sparse_specialization_page_has_no_fabricated_content(self):
        html = _render("specialization", {
            "spec_name": "Data Science",
            "university_name": "Test University",
            "about_content": "<p>Applied data science track.</p>",
        }, standalone=True, parent_slug="test-uni-online-mca")
        self._assert_clean(html, "specialization")
        self.assertIn("Applied data science track.", html)

    def test_sparse_university_page_has_no_fabricated_content(self):
        html = _render("university", {
            "university_name": "Test University",
            "hero_description": "An online university.",
        })
        self._assert_clean(html, "university")
        self.assertIn("Test University", html)

    def test_empty_sections_are_hidden_in_production(self):
        html = _render("course", {
            "program_name": "Online MCA",
            "university_name": "Test University",
        }, standalone=True)
        # Syllabus had no guard before; with no syllabus data it must not render.
        self.assertNotIn('<section id="syllabus"', html)
        self.assertNotIn("data-preview-placeholder", html)
        self.assertNotIn("data-preview-indicator", html)

    def test_preview_mode_marks_incomplete_sections(self):
        html = _render("course", {
            "program_name": "Online MCA",
            "university_name": "Test University",
        }, standalone=True, preview=True)
        # Preview adds indicators but still never fabricates content.
        self._assert_clean(html, "course-preview")
        self.assertIn("data-preview-indicator", html)
        self.assertIn("Preview — incomplete sections", html)

    def test_faq_structured_data_is_not_fabricated(self):
        html = _render("course", {
            "program_name": "Online MCA",
            "university_name": "Test University",
        }, standalone=True)
        # No FAQs supplied -> no FAQPage graph at all.
        self.assertNotIn('"FAQPage"', html)


if __name__ == "__main__":
    unittest.main()
