"""Flask route tests using the Flask test client."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """Return a Flask test client with a fresh app instance per test."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def client_with_subjects(client):
    """Test client with subjects already configured."""
    client.post(
        "/api/subjects",
        json={"subjects": ["Math", "Science", "English"]},
    )
    return client


def _add_student(client, name, roll, math, sci, eng):
    return client.post(
        "/api/students",
        json={"name": name, "roll_number": roll, "marks": {"Math": math, "Science": sci, "English": eng}},
    )


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestIndexRoute:
    def test_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_returns_html(self, client):
        resp = client.get("/")
        assert b"<!DOCTYPE html>" in resp.data or b"<html" in resp.data


# ---------------------------------------------------------------------------
# GET /api/subjects — empty state
# ---------------------------------------------------------------------------

class TestGetSubjects:
    def test_returns_empty_list_initially(self, client):
        resp = client.get("/api/subjects")
        assert resp.status_code == 200
        assert resp.json["subjects"] == []


# ---------------------------------------------------------------------------
# POST /api/subjects
# ---------------------------------------------------------------------------

class TestSetSubjects:
    def test_sets_subjects_successfully(self, client):
        resp = client.post("/api/subjects", json={"subjects": ["Math", "Science"]})
        assert resp.status_code == 200
        names = [s["name"] for s in resp.json["subjects"]]
        assert names == ["Math", "Science"]

    def test_empty_list_returns_400(self, client):
        resp = client.post("/api/subjects", json={"subjects": []})
        assert resp.status_code == 400
        assert "error" in resp.json

    def test_missing_key_returns_400(self, client):
        resp = client.post("/api/subjects", json={})
        assert resp.status_code == 400
        assert "error" in resp.json

    def test_deduplication_applied(self, client):
        resp = client.post("/api/subjects", json={"subjects": ["Math", "Math", "Science"]})
        assert resp.status_code == 200
        names = [s["name"] for s in resp.json["subjects"]]
        assert names == ["Math", "Science"]

    def test_changing_subjects_clears_students(self, client_with_subjects):
        _add_student(client_with_subjects, "Alice", "R001", 80, 70, 60)
        client_with_subjects.post("/api/subjects", json={"subjects": ["Physics"]})
        resp = client_with_subjects.get("/api/students")
        assert resp.json["students"] == []


# ---------------------------------------------------------------------------
# POST /api/students
# ---------------------------------------------------------------------------

class TestAddStudent:
    def test_add_valid_student_returns_201(self, client_with_subjects):
        resp = _add_student(client_with_subjects, "Alice", "R001", 80, 75, 70)
        assert resp.status_code == 201
        data = resp.json["student"]
        assert data["name"] == "Alice"
        assert data["total"] == 225
        assert data["percentage"] == 75.0
        assert data["grade"] == "B"
        assert data["pass_fail"] == "Pass"

    def test_returned_student_has_all_fields(self, client_with_subjects):
        resp = _add_student(client_with_subjects, "Alice", "R001", 80, 75, 70)
        keys = set(resp.json["student"].keys())
        assert {"id", "name", "roll_number", "marks", "total", "percentage",
                "grade", "pass_fail", "failed_subjects", "subject_performance"}.issubset(keys)

    def test_duplicate_roll_returns_400(self, client_with_subjects):
        _add_student(client_with_subjects, "Alice", "R001", 80, 75, 70)
        resp = _add_student(client_with_subjects, "Bob", "R001", 60, 55, 50)
        assert resp.status_code == 400
        assert "error" in resp.json

    def test_empty_name_returns_400(self, client_with_subjects):
        resp = client_with_subjects.post(
            "/api/students",
            json={"name": "", "roll_number": "R002", "marks": {"Math": 80, "Science": 70, "English": 60}},
        )
        assert resp.status_code == 400
        assert "error" in resp.json

    def test_marks_above_100_returns_400(self, client_with_subjects):
        resp = client_with_subjects.post(
            "/api/students",
            json={"name": "Alice", "roll_number": "R003", "marks": {"Math": 110, "Science": 70, "English": 60}},
        )
        assert resp.status_code == 400

    def test_no_subjects_configured_returns_400(self, client):
        resp = client.post(
            "/api/students",
            json={"name": "Alice", "roll_number": "R001", "marks": {"Math": 80}},
        )
        assert resp.status_code == 400
        assert "error" in resp.json

    def test_fail_student_has_correct_pass_fail(self, client_with_subjects):
        # Science = 10 → below 33 → Fail
        resp = _add_student(client_with_subjects, "Bob", "R002", 90, 10, 80)
        assert resp.status_code == 201
        assert resp.json["student"]["pass_fail"] == "Fail"
        assert "Science" in resp.json["student"]["failed_subjects"]


# ---------------------------------------------------------------------------
# GET /api/students
# ---------------------------------------------------------------------------

class TestGetStudents:
    def test_returns_empty_list_initially(self, client_with_subjects):
        resp = client_with_subjects.get("/api/students")
        assert resp.status_code == 200
        assert resp.json["students"] == []

    def test_returns_all_added_students(self, client_with_subjects):
        _add_student(client_with_subjects, "Alice", "R001", 80, 75, 70)
        _add_student(client_with_subjects, "Bob",   "R002", 60, 55, 50)
        resp = client_with_subjects.get("/api/students")
        assert len(resp.json["students"]) == 2


# ---------------------------------------------------------------------------
# DELETE /api/students
# ---------------------------------------------------------------------------

class TestClearStudents:
    def test_clears_all_students(self, client_with_subjects):
        _add_student(client_with_subjects, "Alice", "R001", 80, 75, 70)
        resp = client_with_subjects.delete("/api/students")
        assert resp.status_code == 200
        remaining = client_with_subjects.get("/api/students")
        assert remaining.json["students"] == []

    def test_subjects_remain_after_clear(self, client_with_subjects):
        client_with_subjects.delete("/api/students")
        resp = client_with_subjects.get("/api/subjects")
        assert len(resp.json["subjects"]) == 3


# ---------------------------------------------------------------------------
# GET /api/stats
# ---------------------------------------------------------------------------

class TestGetStats:
    def test_empty_students_returns_400(self, client_with_subjects):
        resp = client_with_subjects.get("/api/stats")
        assert resp.status_code == 400
        assert "error" in resp.json

    def test_stats_keys_present(self, client_with_subjects):
        _add_student(client_with_subjects, "Alice", "R001", 80, 75, 70)
        resp = client_with_subjects.get("/api/stats")
        assert resp.status_code == 200
        assert set(resp.json.keys()) == {
            "average", "highest", "lowest",
            "total_students", "passed", "failed",
        }

    def test_correct_average(self, client_with_subjects):
        _add_student(client_with_subjects, "Alice", "R001", 90, 90, 90)  # 90%
        _add_student(client_with_subjects, "Bob",   "R002", 60, 60, 60)  # 60%
        resp = client_with_subjects.get("/api/stats")
        assert resp.json["average"] == 75.0

    def test_highest_and_lowest(self, client_with_subjects):
        _add_student(client_with_subjects, "Alice", "R001", 90, 90, 90)
        _add_student(client_with_subjects, "Bob",   "R002", 60, 60, 60)
        stats = client_with_subjects.get("/api/stats").json
        assert stats["highest"] == ["Alice"]
        assert stats["lowest"] == ["Bob"]

    def test_pass_fail_counts(self, client_with_subjects):
        _add_student(client_with_subjects, "Alice", "R001", 80, 80, 80)   # pass
        _add_student(client_with_subjects, "Bob",   "R002", 80, 10, 80)   # fail
        stats = client_with_subjects.get("/api/stats").json
        assert stats["passed"] == 1
        assert stats["failed"] == 1
