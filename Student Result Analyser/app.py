"""
Student Result Analyser — Flask application factory.

Usage:
    python app.py

The app uses an in-memory store; all data is lost when the server restarts.
No database or authentication is required for this classroom-scale tool.
"""

from __future__ import annotations

from flask import Flask

from routes import register_routes
from services.result_service import ResultService


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Single service instance shared across all requests in this session.
    # In-memory: data lives only while the server is running.
    service = ResultService()
    app.config["SERVICE"] = service

    register_routes(app)
    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True, port=5000)
