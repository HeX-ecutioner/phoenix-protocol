import os
from typing import Any, Dict, Optional
from flask import Flask, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

from app.api.routes import api_bp
from app.database.connection import get_connection
from app.database.schema import init_db


def create_app(
    db_path: Optional[str] = None, test_config: Optional[Dict[str, Any]] = None
) -> Flask:
    """Application factory for the Phoenix Protocol Flask API."""
    app = Flask(__name__)

    # Default configuration
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB max payload
    if db_path:
        app.config["DATABASE_PATH"] = db_path

    if test_config:
        app.config.update(test_config)

    if "KNOWLEDGE_DB_PATH" not in app.config:
        if app.config.get("TESTING"):
            app.config["KNOWLEDGE_DB_PATH"] = ":memory:"
        elif db_path and db_path != "phoenix_protocol.db":
            app.config["KNOWLEDGE_DB_PATH"] = db_path.replace(".db", "_knowledge.db")
        else:
            app.config["KNOWLEDGE_DB_PATH"] = os.environ.get(
                "KNOWLEDGE_DB_PATH", "phoenix_knowledge.db"
            )

    # Initialize schema on startup
    target_db = app.config.get("DATABASE_PATH")
    conn = get_connection(target_db)
    init_db(conn)
    conn.close()

    # Register blueprints
    app.register_blueprint(api_bp)

    # Global error handlers
    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_payload(error):
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "data": None,
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": "Uploaded file or total request payload exceeds size limits.",
                            "details": [],
                        },
                        "request_id": f"req-err",
                    }
                ),
                413,
            )
        return (
            jsonify(
                {
                    "error": "Payload too large",
                    "detail": "Uploaded file or total request payload exceeds size limits.",
                }
            ),
            413,
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "data": None,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": str(
                                error.description if hasattr(error, "description") else error
                            ),
                            "details": [],
                        },
                        "request_id": f"req-err",
                    }
                ),
                404,
            )
        return (
            jsonify(
                {
                    "error": "Resource not found",
                    "detail": str(
                        error.description if hasattr(error, "description") else error
                    ),
                }
            ),
            404,
        )

    @app.errorhandler(500)
    def handle_internal_error(error):
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "data": None,
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "An unexpected server error occurred.",
                            "details": [],
                        },
                        "request_id": f"req-err",
                    }
                ),
                500,
            )
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "detail": "An unexpected server error occurred.",
                }
            ),
            500,
        )

    return app
