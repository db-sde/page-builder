import unittest

from renderer.engine import fee_has_total_column, normalise_fee_plans, render_resolved


def render_page(page_type, raw):
    return render_resolved({
        "slug": "test-page",
        "page_type": page_type,
        "university_slug": "test-uni",
        "parent_slug": "test-course" if page_type == "specialization" else None,
        "raw": raw,
    }, standalone=True)


class EmiRenderingTests(unittest.TestCase):
    def test_two_column_fee_data_does_not_render_a_synthetic_total_column(self):
        rows = normalise_fee_plans([
            {"plan_name": "Finance", "plan_amount": "INR 180,000", "plan_total": "Complete Course"},
            {"plan_name": "Marketing", "plan_amount": "INR 180,000", "plan_total": "Complete Course"},
        ])
        self.assertFalse(fee_has_total_column(rows))

        html = render_page("specialization", {
            "spec_name": "Business Analytics",
            "university_name": "Test University",
            "fee_plans": [
                {"plan_name": "Finance", "plan_amount": "INR 180,000", "plan_total": "Complete Course"},
                {"plan_name": "Marketing", "plan_amount": "INR 180,000", "plan_total": "Complete Course"},
            ],
        })
        self.assertNotIn("Total Payable", html)
        self.assertNotIn("Complete Course", html)

    def test_independent_fee_totals_and_semester_years_keep_the_third_column(self):
        totals = normalise_fee_plans([
            {"plan_name": "Annual Plan", "plan_amount": "INR 100,000", "plan_total": "INR 200,000"},
        ])
        semester_rows = normalise_fee_plans([
            {"plan_name": "Semester III", "plan_amount": "INR 50,000", "plan_total": "Year I"},
        ])

        self.assertTrue(fee_has_total_column(totals))
        self.assertTrue(fee_has_total_column(semester_rows))

    def test_empty_currency_placeholder_is_hidden_on_course_pages(self):
        html = render_page("course", {
            "program_name": "Online MBA",
            "university_name": "Test University",
            "total_fee": "INR 100,000",
            "fee_plans": [{"plan_name": "Semester I", "plan_amount": "INR 50,000"}],
            "emi_amount": "INR /-",
        })

        self.assertNotIn("EMI: INR /-", html)

    def test_valid_emi_is_rendered_on_course_and_specialization_pages(self):
        base_raw = {
            "university_name": "Test University",
            "total_fee": "INR 100,000",
            "fee_plans": [{"plan_name": "Semester I", "plan_amount": "INR 50,000"}],
            "emi_amount": "INR 5,000",
        }

        course_html = render_page("course", {**base_raw, "program_name": "Online MBA"})
        specialization_html = render_page("specialization", {**base_raw, "spec_name": "Finance"})

        self.assertIn("EMI: INR 5,000", course_html)
        self.assertIn("EMI: INR 5,000", specialization_html)


if __name__ == "__main__":
    unittest.main()
