"""Student model with all business calculations in the Python layer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from models.subject import Subject


# ---------------------------------------------------------------------------
# Grade bands (percentage thresholds, upper-inclusive)
# ---------------------------------------------------------------------------
_GRADE_BANDS: list[tuple[int, str]] = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (40, "D"),
    (0,  "F"),
]


def _assign_grade(percentage: float) -> str:
    """Return the letter grade for a given percentage (0–100)."""
    for threshold, grade in _GRADE_BANDS:
        if percentage >= threshold:
            return grade
    return "F"


@dataclass
class Student:
    """
    Represents a single student's record.

    All business computations (total, percentage, grade, pass/fail) are
    performed here in the Python layer — never in JavaScript.
    """

    name: str
    roll_number: str
    marks: dict[str, int]                   # subject_name → marks obtained
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    def compute_total(self) -> int:
        """Return the sum of marks across all subjects."""
        return sum(self.marks.values())

    def compute_percentage(self, subjects: list[Subject]) -> float:
        """
        Return percentage as (total obtained / total possible) * 100,
        rounded to two decimal places.
        """
        total_max = sum(s.max_marks for s in subjects)
        if total_max == 0:
            return 0.0
        return round((self.compute_total() / total_max) * 100, 2)

    def assign_grade(self, subjects: list[Subject]) -> str:
        """Return the letter grade based on the overall percentage."""
        return _assign_grade(self.compute_percentage(subjects))

    def is_pass(self, subjects: list[Subject]) -> bool:
        """
        Return True only if the student passes every subject individually
        AND the overall percentage meets the minimum threshold.

        Passing rule: marks in each subject >= subject.passing_marks
        AND overall percentage >= 33.
        """
        for subject in subjects:
            obtained = self.marks.get(subject.name, 0)
            if obtained < subject.passing_marks:
                return False
        overall = self.compute_percentage(subjects)
        return overall >= 33.0

    def get_failed_subjects(self, subjects: list[Subject]) -> list[str]:
        """Return names of subjects where the student scored below passing_marks."""
        return [
            s.name
            for s in subjects
            if self.marks.get(s.name, 0) < s.passing_marks
        ]

    def subject_performance(self, subjects: list[Subject]) -> list[dict[str, Any]]:
        """
        Return a list of per-subject dicts with marks, max, passing, and pass flag.
        """
        return [
            {
                "subject": s.name,
                "marks": self.marks.get(s.name, 0),
                "max_marks": s.max_marks,
                "passing_marks": s.passing_marks,
                "passed": self.marks.get(s.name, 0) >= s.passing_marks,
            }
            for s in subjects
        ]

    def to_dict(self, subjects: list[Subject]) -> dict[str, Any]:
        """
        Serialize to a plain dict with all computed fields included.
        JavaScript receives computed results — it never recalculates them.
        """
        percentage = self.compute_percentage(subjects)
        return {
            "id": self.id,
            "name": self.name,
            "roll_number": self.roll_number,
            "marks": self.marks,
            "total": self.compute_total(),
            "max_total": sum(s.max_marks for s in subjects),
            "percentage": percentage,
            "grade": self.assign_grade(subjects),
            "pass_fail": "Pass" if self.is_pass(subjects) else "Fail",
            "failed_subjects": self.get_failed_subjects(subjects),
            "subject_performance": self.subject_performance(subjects),
        }
