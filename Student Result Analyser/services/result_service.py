"""Business logic orchestrator for the Student Result Analyser.

All grade, percentage, and pass/fail calculations are performed by the
Student model. This service coordinates validation, storage, and statistics.
JavaScript receives pre-computed results — it never recalculates anything.
"""

from __future__ import annotations

from typing import Any

from models.student import Student
from models.subject import Subject
from repository.student_repository import StudentRepository
from utils.exceptions import DuplicateRollError, NoStudentsError, NoSubjectsError
from utils.validator import Validator


class ResultService:
    """
    Orchestrates all student result operations.
    The Flask routes call only this class — they never touch models directly.
    """

    def __init__(self, repository: StudentRepository | None = None) -> None:
        self._repo = repository or StudentRepository()
        self._subjects: list[Subject] = []

    # ------------------------------------------------------------------
    # Subject configuration
    # ------------------------------------------------------------------

    def set_subjects(self, subject_names: list[str]) -> None:
        """
        Configure the subject list for this session.
        Clears all existing students when subjects change.
        Raises NoSubjectsError / ValidationError on invalid input.
        """
        Validator.validate_subjects_list(subject_names)
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_names: list[str] = []
        for name in subject_names:
            stripped = name.strip()
            if stripped not in seen:
                seen.add(stripped)
                unique_names.append(stripped)
        self._subjects = [Subject.from_name(n) for n in unique_names]
        self._repo.clear()

    def get_subjects(self) -> list[Subject]:
        """Return the configured subject list."""
        return list(self._subjects)

    # ------------------------------------------------------------------
    # Student management
    # ------------------------------------------------------------------

    def add_student(
        self,
        name: str,
        roll_number: str,
        marks: dict[str, int],
    ) -> Student:
        """
        Validate and add a new student.

        Raises:
            NoSubjectsError: subjects not yet configured.
            ValidationError: any input field is invalid.
            DuplicateRollError: roll number already used.
        """
        if not self._subjects:
            raise NoSubjectsError(
                "Subjects must be configured before adding students."
            )
        subject_names = [s.name for s in self._subjects]
        Validator.validate_student_input(name.strip(), roll_number.strip(), marks, subject_names)

        student = Student(
            name=name.strip(),
            roll_number=roll_number.strip(),
            marks=marks,
        )
        self._repo.add(student)   # raises DuplicateRollError if duplicate
        return student

    def get_all_students(self) -> list[dict[str, Any]]:
        """Return all students serialized with all computed fields."""
        return [s.to_dict(self._subjects) for s in self._repo.get_all()]

    def clear_students(self) -> None:
        """Remove all student records (subjects configuration is kept)."""
        self._repo.clear()

    # ------------------------------------------------------------------
    # Class statistics
    # ------------------------------------------------------------------

    def get_class_stats(self) -> dict[str, Any]:
        """
        Compute and return class-wide statistics.

        Returns a dict with:
            average       - mean percentage across all students (float)
            highest       - list of names of top-scoring students
            lowest        - list of names of lowest-scoring students
            total_students - int
            passed        - int (students who passed all subjects)
            failed        - int

        Raises NoStudentsError if no students have been added.
        """
        students = self._repo.get_all()
        if not students:
            raise NoStudentsError(
                "No students found. Add at least one student before viewing statistics."
            )

        totals = [s.compute_total() for s in students]
        percentages = [s.compute_percentage(self._subjects) for s in students]
        pass_flags = [s.is_pass(self._subjects) for s in students]

        average = round(sum(percentages) / len(percentages), 2)
        max_total = max(totals)
        min_total = min(totals)

        highest = [s.name for s, t in zip(students, totals) if t == max_total]
        lowest = [s.name for s, t in zip(students, totals) if t == min_total]

        passed = sum(1 for f in pass_flags if f)
        failed = len(students) - passed

        return {
            "average": average,
            "highest": highest,
            "lowest": lowest,
            "total_students": len(students),
            "passed": passed,
            "failed": failed,
        }
