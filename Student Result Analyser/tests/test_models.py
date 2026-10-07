"""Unit tests for Student and Subject models."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models.subject import Subject
from models.student import Student


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def subjects() -> list[Subject]:
    return [
        Subject("Math"),
        Subject("Science"),
        Subject("English"),
    ]


@pytest.fixture()
def passing_student(subjects) -> Student:
    """Student who passes all subjects with a B grade."""
    return Student(
        name="Alice",
        roll_number="R001",
        marks={"Math": 80, "Science": 75, "English": 70},
    )


@pytest.fixture()
def failing_student(subjects) -> Student:
    """Student who fails Science (below passing threshold of 33)."""
    return Student(
        name="Bob",
        roll_number="R002",
        marks={"Math": 90, "Science": 20, "English": 80},
    )


@pytest.fixture()
def zero_student(subjects) -> Student:
    """Student who scores 0 in everything."""
    return Student(
        name="Charlie",
        roll_number="R003",
        marks={"Math": 0, "Science": 0, "English": 0},
    )


# ---------------------------------------------------------------------------
# Subject tests
# ---------------------------------------------------------------------------

class TestSubject:
    def test_defaults(self):
        s = Subject("Math")
        assert s.max_marks == 100
        assert s.passing_marks == 33

    def test_from_name_strips_whitespace(self):
        s = Subject.from_name("  Physics  ")
        assert s.name == "Physics"

    def test_to_dict_shape(self):
        s = Subject("Chemistry", max_marks=100, passing_marks=33)
        d = s.to_dict()
        assert d == {"name": "Chemistry", "max_marks": 100, "passing_marks": 33}


# ---------------------------------------------------------------------------
# Student.compute_total
# ---------------------------------------------------------------------------

class TestComputeTotal:
    def test_sums_all_marks(self, passing_student):
        assert passing_student.compute_total() == 225   # 80+75+70

    def test_zero_marks(self, zero_student):
        assert zero_student.compute_total() == 0

    def test_full_marks(self, subjects):
        s = Student("Max", "R099", {"Math": 100, "Science": 100, "English": 100})
        assert s.compute_total() == 300


# ---------------------------------------------------------------------------
# Student.compute_percentage
# ---------------------------------------------------------------------------

class TestComputePercentage:
    def test_correct_percentage(self, passing_student, subjects):
        # 225 / 300 * 100 = 75.0
        assert passing_student.compute_percentage(subjects) == 75.0

    def test_zero_percentage(self, zero_student, subjects):
        assert zero_student.compute_percentage(subjects) == 0.0

    def test_hundred_percentage(self, subjects):
        s = Student("Perfect", "R100", {"Math": 100, "Science": 100, "English": 100})
        assert s.compute_percentage(subjects) == 100.0

    def test_rounds_to_two_decimals(self, subjects):
        # 170 / 300 = 56.666... → 56.67
        s = Student("Rnd", "R200", {"Math": 60, "Science": 55, "English": 55})
        pct = s.compute_percentage(subjects)
        assert pct == round(170 / 300 * 100, 2)


# ---------------------------------------------------------------------------
# Student.assign_grade — boundary conditions
# ---------------------------------------------------------------------------

class TestAssignGrade:
    def _make(self, math, science, english) -> Student:
        return Student("Test", "R0", {"Math": math, "Science": science, "English": english})

    def test_grade_A_at_90(self, subjects):
        # 270/300 = 90.0 → A
        assert self._make(90, 90, 90).assign_grade(subjects) == "A"

    def test_grade_A_above_90(self, subjects):
        assert self._make(100, 100, 100).assign_grade(subjects) == "A"

    def test_grade_B_at_75(self, subjects):
        # 225/300 = 75.0 → B
        assert self._make(80, 75, 70).assign_grade(subjects) == "B"

    def test_grade_B_just_below_A(self, subjects):
        # 269/300 = 89.67 → B
        assert self._make(90, 90, 89).assign_grade(subjects) == "B"

    def test_grade_C_at_60(self, subjects):
        # 180/300 = 60.0 → C
        assert self._make(60, 60, 60).assign_grade(subjects) == "C"

    def test_grade_D_at_40(self, subjects):
        # 120/300 = 40.0 → D
        assert self._make(40, 40, 40).assign_grade(subjects) == "D"

    def test_grade_F_below_40(self, subjects):
        # 99/300 = 33.0 → D  — need lower
        assert self._make(30, 30, 30).assign_grade(subjects) == "F"

    def test_grade_F_at_zero(self, subjects, zero_student):
        assert zero_student.assign_grade(subjects) == "F"


# ---------------------------------------------------------------------------
# Student.is_pass
# ---------------------------------------------------------------------------

class TestIsPass:
    def test_pass_when_all_subjects_pass(self, passing_student, subjects):
        assert passing_student.is_pass(subjects) is True

    def test_fail_when_one_subject_below_threshold(self, failing_student, subjects):
        # Science = 20 < 33
        assert failing_student.is_pass(subjects) is False

    def test_fail_when_all_zero(self, zero_student, subjects):
        assert zero_student.is_pass(subjects) is False

    def test_pass_at_exact_boundary(self, subjects):
        # Exactly 33 in every subject → should pass
        s = Student("Boundary", "R300", {"Math": 33, "Science": 33, "English": 33})
        assert s.is_pass(subjects) is True


# ---------------------------------------------------------------------------
# Student.get_failed_subjects
# ---------------------------------------------------------------------------

class TestGetFailedSubjects:
    def test_returns_empty_when_all_pass(self, passing_student, subjects):
        assert passing_student.get_failed_subjects(subjects) == []

    def test_returns_failed_subject_name(self, failing_student, subjects):
        failed = failing_student.get_failed_subjects(subjects)
        assert "Science" in failed
        assert len(failed) == 1


# ---------------------------------------------------------------------------
# Student.subject_performance
# ---------------------------------------------------------------------------

class TestSubjectPerformance:
    def test_returns_one_entry_per_subject(self, passing_student, subjects):
        perf = passing_student.subject_performance(subjects)
        assert len(perf) == 3

    def test_entry_shape(self, passing_student, subjects):
        perf = passing_student.subject_performance(subjects)
        entry = perf[0]
        assert set(entry.keys()) == {"subject", "marks", "max_marks", "passing_marks", "passed"}

    def test_passed_flag_correct(self, failing_student, subjects):
        perf = {p["subject"]: p for p in failing_student.subject_performance(subjects)}
        assert perf["Science"]["passed"] is False
        assert perf["Math"]["passed"] is True


# ---------------------------------------------------------------------------
# Student.to_dict
# ---------------------------------------------------------------------------

class TestToDict:
    def test_all_keys_present(self, passing_student, subjects):
        d = passing_student.to_dict(subjects)
        expected_keys = {
            "id", "name", "roll_number", "marks", "total", "max_total",
            "percentage", "grade", "pass_fail", "failed_subjects", "subject_performance",
        }
        assert expected_keys == set(d.keys())

    def test_computed_values_match_methods(self, passing_student, subjects):
        d = passing_student.to_dict(subjects)
        assert d["total"] == passing_student.compute_total()
        assert d["percentage"] == passing_student.compute_percentage(subjects)
        assert d["grade"] == passing_student.assign_grade(subjects)
        assert d["pass_fail"] == "Pass"

    def test_pass_fail_string_for_failing_student(self, failing_student, subjects):
        d = failing_student.to_dict(subjects)
        assert d["pass_fail"] == "Fail"
        assert "Science" in d["failed_subjects"]
