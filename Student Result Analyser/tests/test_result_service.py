"""Unit tests for StudentRepository and ResultService."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from repository.student_repository import StudentRepository
from services.result_service import ResultService
from utils.exceptions import (
    DuplicateRollError,
    NoStudentsError,
    NoSubjectsError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def repo() -> StudentRepository:
    return StudentRepository()


@pytest.fixture()
def service() -> ResultService:
    """Fresh ResultService with subjects already configured."""
    svc = ResultService()
    svc.set_subjects(["Math", "Science", "English"])
    return svc


@pytest.fixture()
def empty_service() -> ResultService:
    """Fresh ResultService with NO subjects configured."""
    return ResultService()


def _add(svc: ResultService, name: str, roll: str, math: int, sci: int, eng: int):
    svc.add_student(name, roll, {"Math": math, "Science": sci, "English": eng})


# ---------------------------------------------------------------------------
# StudentRepository
# ---------------------------------------------------------------------------

class TestStudentRepository:
    def test_add_and_get_all(self, repo):
        from models.student import Student
        s = Student("Alice", "R001", {"Math": 80})
        repo.add(s)
        assert len(repo.get_all()) == 1

    def test_duplicate_roll_raises(self, repo):
        from models.student import Student
        s1 = Student("Alice", "R001", {"Math": 80})
        s2 = Student("Alice2", "R001", {"Math": 70})
        repo.add(s1)
        with pytest.raises(DuplicateRollError):
            repo.add(s2)

    def test_find_by_roll_returns_student(self, repo):
        from models.student import Student
        s = Student("Alice", "R001", {"Math": 80})
        repo.add(s)
        found = repo.find_by_roll("R001")
        assert found is s

    def test_find_by_roll_returns_none_if_missing(self, repo):
        assert repo.find_by_roll("X999") is None

    def test_clear_empties_repository(self, repo):
        from models.student import Student
        repo.add(Student("Alice", "R001", {"Math": 80}))
        repo.clear()
        assert repo.get_all() == []


# ---------------------------------------------------------------------------
# ResultService.set_subjects
# ---------------------------------------------------------------------------

class TestSetSubjects:
    def test_sets_subjects(self, empty_service):
        empty_service.set_subjects(["Math", "Science"])
        subjects = empty_service.get_subjects()
        assert [s.name for s in subjects] == ["Math", "Science"]

    def test_empty_list_raises(self, empty_service):
        with pytest.raises(NoSubjectsError):
            empty_service.set_subjects([])

    def test_deduplicates_subjects(self, empty_service):
        empty_service.set_subjects(["Math", "Math", "Science"])
        names = [s.name for s in empty_service.get_subjects()]
        assert names == ["Math", "Science"]

    def test_clears_existing_students(self, service):
        _add(service, "Alice", "R001", 80, 70, 60)
        service.set_subjects(["Physics"])   # reconfigure subjects
        assert service.get_all_students() == []


# ---------------------------------------------------------------------------
# ResultService.add_student
# ---------------------------------------------------------------------------

class TestAddStudent:
    def test_adds_student_successfully(self, service):
        _add(service, "Alice", "R001", 80, 75, 70)
        students = service.get_all_students()
        assert len(students) == 1
        assert students[0]["name"] == "Alice"

    def test_returned_dict_has_computed_fields(self, service):
        student = service.add_student("Alice", "R001", {"Math": 90, "Science": 90, "English": 90})
        d = student.to_dict(service.get_subjects())
        assert d["total"] == 270
        assert d["percentage"] == 90.0
        assert d["grade"] == "A"
        assert d["pass_fail"] == "Pass"

    def test_duplicate_roll_raises(self, service):
        _add(service, "Alice", "R001", 80, 75, 70)
        with pytest.raises(DuplicateRollError):
            _add(service, "Bob", "R001", 60, 65, 55)

    def test_invalid_name_raises(self, service):
        with pytest.raises(ValidationError):
            service.add_student("", "R002", {"Math": 80, "Science": 70, "English": 60})

    def test_marks_above_100_raises(self, service):
        with pytest.raises(ValidationError):
            service.add_student("Alice", "R002", {"Math": 110, "Science": 70, "English": 60})

    def test_no_subjects_configured_raises(self, empty_service):
        with pytest.raises(NoSubjectsError):
            empty_service.add_student("Alice", "R001", {"Math": 80})

    def test_missing_subject_in_marks_raises(self, service):
        with pytest.raises(ValidationError, match="missing"):
            service.add_student("Alice", "R002", {"Math": 80})  # Science + English missing


# ---------------------------------------------------------------------------
# ResultService.get_class_stats
# ---------------------------------------------------------------------------

class TestGetClassStats:
    def test_raises_when_no_students(self, service):
        with pytest.raises(NoStudentsError):
            service.get_class_stats()

    def test_average_single_student(self, service):
        _add(service, "Alice", "R001", 90, 90, 90)
        stats = service.get_class_stats()
        # 270/300 = 90.0
        assert stats["average"] == 90.0

    def test_average_multiple_students(self, service):
        _add(service, "Alice", "R001", 90, 90, 90)   # 90%
        _add(service, "Bob",   "R002", 60, 60, 60)   # 60%
        stats = service.get_class_stats()
        assert stats["average"] == 75.0

    def test_highest_scorer(self, service):
        _add(service, "Alice", "R001", 90, 90, 90)   # 270
        _add(service, "Bob",   "R002", 60, 60, 60)   # 180
        stats = service.get_class_stats()
        assert stats["highest"] == ["Alice"]

    def test_lowest_scorer(self, service):
        _add(service, "Alice", "R001", 90, 90, 90)
        _add(service, "Bob",   "R002", 60, 60, 60)
        stats = service.get_class_stats()
        assert stats["lowest"] == ["Bob"]

    def test_tie_all_same_score(self, service):
        _add(service, "Alice", "R001", 80, 80, 80)
        _add(service, "Bob",   "R002", 80, 80, 80)
        stats = service.get_class_stats()
        assert set(stats["highest"]) == {"Alice", "Bob"}
        assert set(stats["lowest"]) == {"Alice", "Bob"}

    def test_single_student_is_both_highest_and_lowest(self, service):
        _add(service, "Alice", "R001", 70, 70, 70)
        stats = service.get_class_stats()
        assert stats["highest"] == ["Alice"]
        assert stats["lowest"] == ["Alice"]

    def test_pass_fail_counts(self, service):
        _add(service, "Alice", "R001", 80, 80, 80)   # pass
        _add(service, "Bob",   "R002", 80, 10, 80)   # fail (Science < 33)
        stats = service.get_class_stats()
        assert stats["passed"] == 1
        assert stats["failed"] == 1

    def test_stats_keys(self, service):
        _add(service, "Alice", "R001", 80, 80, 80)
        stats = service.get_class_stats()
        assert set(stats.keys()) == {
            "average", "highest", "lowest",
            "total_students", "passed", "failed",
        }
