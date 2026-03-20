"""
Fovea – YouTube Secrets Detection Tool
Flask application factory.
"""

from __future__ import annotations

import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)

    # Basic config
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit
    app.config["JSON_SORT_KEYS"] = False

    # CORS – allow the React dev server
    CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Register blueprints
    from backend.routes.scan import scan_bp
    from backend.routes.results import results_bp

    app.register_blueprint(scan_bp)
    app.register_blueprint(results_bp)

    # Health-check endpoint
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "fovea"})

    return app


# Allow running with `python -m backend.app`
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
