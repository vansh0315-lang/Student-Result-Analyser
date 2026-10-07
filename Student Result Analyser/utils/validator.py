"""Input validation for student result data.

All methods raise a specific exception on failure and return None on success.
They never return True/False — callers rely on exceptions, not return values.
"""

from __future__ import annotations

import re

from utils.exceptions import NoSubjectsError, ValidationError

_NAME_PATTERN = re.compile(r"^[A-Za-z ]{1,50}$")
_ROLL_PATTERN = re.compile(r"^[A-Za-z0-9]{1,20}$")


class Validator:
    """Static validation methods for all student result inputs."""

    @staticmethod
    def validate_name(name: str) -> None:
        """Name must be 1–50 characters, letters and spaces only."""
        if not name or not name.strip():
            raise ValidationError("Student name must not be empty.")
        if not _NAME_PATTERN.match(name.strip()):
            raise ValidationError(
                "Student name must contain only letters and spaces "
                "(1–50 characters)."
            )

    @staticmethod
    def validate_roll_number(roll: str) -> None:
        """Roll number must be 1–20 alphanumeric characters."""
        if not roll or not roll.strip():
            raise ValidationError("Roll number must not be empty.")
        if not _ROLL_PATTERN.match(roll.strip()):
            raise ValidationError(
                "Roll number must be alphanumeric and at most 20 characters."
            )

    @staticmethod
    def validate_marks(marks: dict) -> None:
        """
        Each mark value must be an integer in the range 0–100 (inclusive).
        The marks dict must not be empty.
        """
        if not marks:
            raise ValidationError("Marks must not be empty.")
        for subject, value in marks.items():
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValidationError(
                    f"Marks for '{subject}' must be an integer, got {type(value).__name__}."
                )
            if value < 0:
                raise ValidationError(
                    f"Marks for '{subject}' must be 0 or above, got {value}."
                )
            if value > 100:
                raise ValidationError(
                    f"Marks for '{subject}' must not exceed 100, got {value}."
                )

    @staticmethod
    def validate_subjects_list(subjects: list) -> None:
        """The subjects list must have at least one entry with a non-empty name."""
        if not subjects:
            raise NoSubjectsError("At least one subject must be configured.")
        for item in subjects:
            name = item.strip() if isinstance(item, str) else ""
            if not name:
                raise ValidationError("Subject name must not be empty.")

    @staticmethod
    def validate_marks_cover_subjects(marks: dict, subject_names: list[str]) -> None:
        """Every configured subject must have a corresponding marks entry."""
        for subject in subject_names:
            if subject not in marks:
                raise ValidationError(
                    f"Marks for subject '{subject}' are missing."
                )

    @classmethod
    def validate_student_input(
        cls,
        name: str,
        roll: str,
        marks: dict,
        subject_names: list[str],
    ) -> None:
        """
        Composite validator: runs all field-level validations in order.
        Raises the first ValidationError encountered.
        """
        cls.validate_name(name)
        cls.validate_roll_number(roll)
        cls.validate_marks(marks)
        cls.validate_marks_cover_subjects(marks, subject_names)
