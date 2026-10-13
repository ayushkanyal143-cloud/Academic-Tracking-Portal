"""
SE_PROJECT — Academic Tracking Portal (Flask application factory).

Key features:
- Semester-wise subject mark tracking from a CSV/Excel-style dataset
- Backend reads the marks dataset on each request (instant updates without code changes)
- Automatic SGPA/CGPA computation and semester-to-semester comparison
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask, make_response, request

from backend.ml import init_model
from backend.routes import api_bp, auth_bp, pages_bp

ROOT_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    logging.basicConfig(level=logging.INFO)
    app = Flask(
        __name__,
        static_folder=str(ROOT_DIR / "frontend" / "static"),
        template_folder=str(ROOT_DIR / "frontend" / "templates"),
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # Train sklearn classifier on data/students.csv once per worker.
    init_model()

    CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "*")

    @app.before_request
    def handle_cors_preflight():
        if request.method == "OPTIONS":
            r = make_response("", 204)
            r.headers["Access-Control-Allow-Origin"] = CORS_ORIGIN
            r.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            r.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return r

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = CORS_ORIGIN
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    # Auth first so /login and /logout are registered alongside pages.
    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)

    return app


app = create_app()

PORT = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=PORT, debug=debug)
