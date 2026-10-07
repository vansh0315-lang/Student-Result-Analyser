"""In-memory repository for Student records."""

from __future__ import annotations

from models.student import Student
from utils.exceptions import DuplicateRollError, StudentNotFoundError


class StudentRepository:
    """
    Stores Student objects in a plain Python list.
    No file I/O — data lives only for the duration of the session.
    """

    def __init__(self) -> None:
        self._students: list[Student] = []

    def add(self, student: Student) -> None:
        """
        Append a student record.
        Raises DuplicateRollError if the roll number already exists.
        """
        if self.find_by_roll(student.roll_number) is not None:
            raise DuplicateRollError(
                f"A student with roll number '{student.roll_number}' already exists."
            )
        self._students.append(student)

    def get_all(self) -> list[Student]:
        """Return all stored students (in insertion order)."""
        return list(self._students)

    def find_by_roll(self, roll_number: str) -> Student | None:
        """Return the student with the given roll number, or None if not found."""
        for student in self._students:
            if student.roll_number == roll_number.strip():
                return student
        return None

    def clear(self) -> None:
        """Remove all student records from the repository."""
        self._students.clear()
