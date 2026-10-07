"""Flask route handlers for the Student Result Analyser API.

All business logic lives in ResultService — these handlers are thin HTTP
adapters that extract request data, call the service, and return JSON.

API contract:
    GET  /                      → Serve the HTML shell
    GET  /api/subjects          → { "subjects": [...] }
    POST /api/subjects          → { "subjects": ["Math", ...] }  body: { "subjects": [...] }
    GET  /api/students          → { "students": [...] }
    POST /api/students          → { "student": {...} }           body: { "name", "roll_number", "marks" }
    DELETE /api/students        → { "message": "cleared" }
    GET  /api/stats             → { "average", "highest", "lowest", ... }

Non-2xx responses always include { "error": "human-readable message" }.
"""

from __future__ import annotations

from flask import Flask, current_app, jsonify, render_template, request

from utils.exceptions import (
    DuplicateRollError,
    NoStudentsError,
    NoSubjectsError,
    ValidationError,
)


def _service():
    """Retrieve the shared ResultService from the application config."""
    return current_app.config["SERVICE"]


def register_routes(app: Flask) -> None:
    """Register all routes on the Flask application."""

    # ------------------------------------------------------------------
    # HTML shell
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        """Serve the single-page HTML shell."""
        return render_template("index.html")

    # ------------------------------------------------------------------
    # Subject endpoints
    # ------------------------------------------------------------------

    @app.route("/api/subjects", methods=["GET"])
    def get_subjects():
        """Return the currently configured subject list."""
        subjects = [s.to_dict() for s in _service().get_subjects()]
        return jsonify({"subjects": subjects}), 200

    @app.route("/api/subjects", methods=["POST"])
    def set_subjects():
        """
        Configure subjects for the session.
        Body: { "subjects": ["Math", "Science", ...] }
        """
        data = request.get_json(silent=True) or {}
        subject_names = data.get("subjects", [])

        try:
            _service().set_subjects(subject_names)
        except (NoSubjectsError, ValidationError) as exc:
            return jsonify({"error": str(exc)}), 400

        subjects = [s.to_dict() for s in _service().get_subjects()]
        return jsonify({"subjects": subjects}), 200

    # ------------------------------------------------------------------
    # Student endpoints
    # ------------------------------------------------------------------

    @app.route("/api/students", methods=["GET"])
    def get_students():
        """Return all students with all computed fields."""
        students = _service().get_all_students()
        return jsonify({"students": students}), 200

    @app.route("/api/students", methods=["POST"])
    def add_student():
        """
        Add a new student.
        Body: { "name": "...", "roll_number": "...", "marks": { "Math": 80, ... } }
        """
        data = request.get_json(silent=True) or {}
        name = data.get("name", "")
        roll = data.get("roll_number", "")
        marks_raw = data.get("marks", {})

        # Coerce mark values to int; reject non-numeric strings here so the
        # Validator can produce a clear type error.
        marks: dict[str, int] = {}
        for subject, value in marks_raw.items():
            if isinstance(value, bool):
                marks[subject] = value   # let Validator reject bool
            elif isinstance(value, int):
                marks[subject] = value
            else:
                try:
                    marks[subject] = int(value)
                except (TypeError, ValueError):
                    return jsonify(
                        {"error": f"Marks for '{subject}' must be an integer."}
                    ), 400

        try:
            student = _service().add_student(name, roll, marks)
        except NoSubjectsError as exc:
            return jsonify({"error": str(exc)}), 400
        except (ValidationError, DuplicateRollError) as exc:
            return jsonify({"error": str(exc)}), 400

        subjects = _service().get_subjects()
        return jsonify({"student": student.to_dict(subjects)}), 201

    @app.route("/api/students", methods=["DELETE"])
    def clear_students():
        """Remove all student records (subjects configuration is kept)."""
        _service().clear_students()
        return jsonify({"message": "All student records have been cleared."}), 200

    # ------------------------------------------------------------------
    # Statistics endpoint
    # ------------------------------------------------------------------

    @app.route("/api/stats", methods=["GET"])
    def get_stats():
        """Return class-wide statistics."""
        try:
            stats = _service().get_class_stats()
        except NoStudentsError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify(stats), 200

    # ------------------------------------------------------------------
    # Generic error handlers
    # ------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(exc):
        return jsonify({"error": "The requested resource was not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return jsonify({"error": "HTTP method not allowed for this endpoint."}), 405

    @app.errorhandler(500)
    def internal_error(exc):
        return jsonify({"error": "An unexpected server error occurred."}), 500
