import unittest

from renderer.engine import normalise_fee_plans, parse_syllabus_html


class AcademicYearGroupingTests(unittest.TestCase):
    def test_unmarked_later_years_are_derived_from_semester_numbers(self):
        syllabus = """
            <h4>Year I</h4>
            <h4>Semester I</h4><ul><li>Subject 1</li></ul>
            <h4>Semester II</h4><ul><li>Subject 2</li></ul>
            <h4>Semester III</h4><ul><li>Subject 3</li></ul>
            <h4>Semester IV</h4><ul><li>Subject 4</li></ul>
        """

        years = parse_syllabus_html(syllabus)

        self.assertEqual([year["label"] for year in years], ["Year I", "Year II"])
        self.assertEqual(
            [[semester["title"] for semester in year["semesters"]] for year in years],
            [["Semester I", "Semester II"], ["Semester III", "Semester IV"]],
        )

    def test_three_year_syllabus_creates_a_tab_for_each_pair_of_semesters(self):
        syllabus = "".join(f"<h4>Semester {number}</h4><ul><li>Subject</li></ul>" for number in range(1, 7))

        years = parse_syllabus_html(syllabus)

        self.assertEqual([year["label"] for year in years], ["Year I", "Year II", "Year III"])
        self.assertEqual([len(year["semesters"]) for year in years], [2, 2, 2])

    def test_semester_fee_rows_use_their_derived_academic_year(self):
        rows = normalise_fee_plans([
            {"plan_name": "Semester I", "plan_amount": "INR 7,083", "plan_total": "Year I"},
            {"plan_name": "Semester II", "plan_amount": "INR 7,083", "plan_total": "Year I"},
            {"plan_name": "Semester III", "plan_amount": "INR 7,083", "plan_total": "Year I"},
            {"plan_name": "Semester IV", "plan_amount": "INR 7,083", "plan_total": "Year I"},
        ])

        self.assertEqual([row["total"] for row in rows], ["Year I", "Year I", "Year II", "Year II"])


if __name__ == "__main__":
    unittest.main()
