import unittest

from renderer.engine import fee_has_total_column, fee_third_column_heading, normalise_fee_plans, render_resolved


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
        self.assertEqual(fee_third_column_heading(totals), "Total Payable")
        self.assertEqual(fee_third_column_heading(semester_rows), "Academic Year")

    def test_semester_schedule_does_not_mislabel_academic_year_as_a_total(self):
        html = render_page("course", {
            "program_name": "Online MBA",
            "university_name": "Test University",
            "fee_plans": [
                {"plan_name": "Semester I", "plan_amount": "INR 7,083", "plan_total": "Year I"},
                {"plan_name": "Semester II", "plan_amount": "INR 7,083", "plan_total": "Year I"},
            ],
        })

        self.assertIn(">Academic Year<", html)
        self.assertNotIn(">Total Payable<", html)

    def test_repayment_labels_do_not_create_a_misleading_total_column(self):
        fees = normalise_fee_plans([
            {"plan_name": "No-cost EMI", "plan_amount": "INR 5,100/month", "plan_total": "24-month plan"},
            {"plan_name": "Semester Plan", "plan_amount": "INR 20,400/semester", "plan_total": "4 semesters"},
        ])

        self.assertEqual([fee["total"] for fee in fees], ["", ""])
        self.assertFalse(fee_has_total_column(fees))

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

    def test_reviewer_name_is_rendered_with_or_without_a_label(self):
        html = render_page("course", {
            "program_name": "Online MBA",
            "university_name": "Test University",
            "reviews": [
                {"review_text": "Helpful faculty.", "reviewer_name": "Rahul Verma", "reviewer_label": "MBA Student"},
                {"review_text": "Flexible learning.", "reviewer_name": "Priya Shah"},
            ],
        })

        self.assertIn("Rahul Verma, MBA Student", html)
        self.assertIn("Priya Shah", html)

    def test_specialization_hero_and_breadcrumb_hide_incomplete_parser_suffixes(self):
        html = render_page("specialization", {
            "program_name": "Online MBA",
            "spec_name": "Human Resource Management (Hrm",
            "university_name": "Test University",
        })

        self.assertIn("All Programs</a> › Human Resource Management", html)
        self.assertIn("Online MBA in<br>Human Resource Management</h1>", html)

    def test_fact_shaped_highlights_render_and_empty_rows_are_hidden(self):
        html = render_page("course", {
            "program_name": "Online MCA",
            "university_name": "Test University",
            "highlights": [
                {
                    "fact_title": "Industry tools",
                    "fact_description": "Learn commonly used development tools.",
                },
                {},
            ],
        })

        self.assertIn("Industry tools", html)
        self.assertIn("Learn commonly used development tools.", html)
        self.assertEqual(html.count("background:#FFE7E0"), 1)


if __name__ == "__main__":
    unittest.main()
