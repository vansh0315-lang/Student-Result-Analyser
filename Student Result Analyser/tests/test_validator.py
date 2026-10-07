"""Unit tests for Validator and custom exceptions."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from utils.exceptions import NoSubjectsError, ValidationError
from utils.validator import Validator


# ---------------------------------------------------------------------------
# validate_name
# ---------------------------------------------------------------------------

class TestValidateName:
    def test_valid_name_passes(self):
        Validator.validate_name("Alice Johnson")  # no exception

    def test_single_letter_passes(self):
        Validator.validate_name("A")

    def test_max_length_passes(self):
        Validator.validate_name("A" * 50)

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            Validator.validate_name("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            Validator.validate_name("   ")

    def test_digits_in_name_raises(self):
        with pytest.raises(ValidationError):
            Validator.validate_name("Alice1")

    def test_special_characters_raise(self):
        with pytest.raises(ValidationError):
            Validator.validate_name("Alice@School")

    def test_too_long_raises(self):
        with pytest.raises(ValidationError):
            Validator.validate_name("A" * 51)


# ---------------------------------------------------------------------------
# validate_roll_number
# ---------------------------------------------------------------------------

class TestValidateRollNumber:
    def test_valid_alphanumeric_passes(self):
        Validator.validate_roll_number("R001")

    def test_letters_only_passes(self):
        Validator.validate_roll_number("ROLL")

    def test_numbers_only_passes(self):
        Validator.validate_roll_number("12345")

    def test_max_length_passes(self):
        Validator.validate_roll_number("A" * 20)

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            Validator.validate_roll_number("")

    def test_special_char_raises(self):
        with pytest.raises(ValidationError):
            Validator.validate_roll_number("R-001")

    def test_too_long_raises(self):
        with pytest.raises(ValidationError):
            Validator.validate_roll_number("A" * 21)


# ---------------------------------------------------------------------------
# validate_marks
# ---------------------------------------------------------------------------

class TestValidateMarks:
    def test_valid_marks_pass(self):
        Validator.validate_marks({"Math": 80, "Science": 55})

    def test_zero_mark_passes(self):
        Validator.validate_marks({"Math": 0})

    def test_hundred_mark_passes(self):
        Validator.validate_marks({"Math": 100})

    def test_negative_mark_raises(self):
        with pytest.raises(ValidationError, match="0 or above"):
            Validator.validate_marks({"Math": -1})

    def test_above_hundred_raises(self):
        with pytest.raises(ValidationError, match="not exceed 100"):
            Validator.validate_marks({"Math": 101})

    def test_float_mark_raises(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            Validator.validate_marks({"Math": 75.5})

    def test_string_mark_raises(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            Validator.validate_marks({"Math": "eighty"})

    def test_bool_mark_raises(self):
        # bool is a subclass of int in Python; we explicitly reject it
        with pytest.raises(ValidationError, match="must be an integer"):
            Validator.validate_marks({"Math": True})

    def test_empty_dict_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            Validator.validate_marks({})


# ---------------------------------------------------------------------------
# validate_subjects_list
# ---------------------------------------------------------------------------

class TestValidateSubjectsList:
    def test_valid_list_passes(self):
        Validator.validate_subjects_list(["Math", "Science"])

    def test_single_subject_passes(self):
        Validator.validate_subjects_list(["Math"])

    def test_empty_list_raises(self):
        with pytest.raises(NoSubjectsError):
            Validator.validate_subjects_list([])

    def test_empty_string_subject_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            Validator.validate_subjects_list(["Math", ""])

    def test_whitespace_only_subject_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            Validator.validate_subjects_list(["  "])


# ---------------------------------------------------------------------------
# validate_marks_cover_subjects
# ---------------------------------------------------------------------------

class TestValidateMarksCoverSubjects:
    def test_all_subjects_covered_passes(self):
        Validator.validate_marks_cover_subjects(
            {"Math": 70, "Science": 60}, ["Math", "Science"]
        )

    def test_missing_subject_raises(self):
        with pytest.raises(ValidationError, match="missing"):
            Validator.validate_marks_cover_subjects(
                {"Math": 70}, ["Math", "Science"]
            )


# ---------------------------------------------------------------------------
# validate_student_input (composite)
# ---------------------------------------------------------------------------

class TestValidateStudentInput:
    def test_valid_input_passes(self):
        Validator.validate_student_input(
            "Alice", "R001", {"Math": 80, "Science": 70}, ["Math", "Science"]
        )

    def test_invalid_name_raises(self):
        with pytest.raises(ValidationError):
            Validator.validate_student_input(
                "", "R001", {"Math": 80}, ["Math"]
            )

    def test_invalid_roll_raises(self):
        with pytest.raises(ValidationError):
            Validator.validate_student_input(
                "Alice", "", {"Math": 80}, ["Math"]
            )

    def test_invalid_marks_raises(self):
        with pytest.raises(ValidationError):
            Validator.validate_student_input(
                "Alice", "R001", {"Math": 150}, ["Math"]
            )

    def test_missing_subject_raises(self):
        with pytest.raises(ValidationError):
            Validator.validate_student_input(
                "Alice", "R001", {"Math": 80}, ["Math", "Science"]
            )
