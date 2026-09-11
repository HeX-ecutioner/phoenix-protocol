"""Flask API package for Phoenix Protocol."""

from typing import Any, Dict, Optional
from flask import Flask, jsonify
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
        return (
            jsonify(
                {
                    "error": "Resource not found",
                    "detail": str(error.description if hasattr(error, "description") else error),
                }
            ),
            404,
        )

    @app.errorhandler(500)
    def handle_internal_error(error):
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
