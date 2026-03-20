"""
results.py – Serve scan results and frame images.
"""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Blueprint, jsonify, send_file, abort

from backend.routes.scan import get_jobs_store

logger = logging.getLogger(__name__)

results_bp = Blueprint("results", __name__)


@results_bp.route("/api/results/<job_id>", methods=["GET"])
def get_results(job_id: str):
    """Return the stored results for a completed scan job."""
    jobs = get_jobs_store()
    job = jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found."}), 404
    return jsonify(job), 200


@results_bp.route("/api/frames/<job_id>/<path:filename>", methods=["GET"])
def serve_frame(job_id: str, filename: str):
    """Serve a frame image from a job's temp directory.

    The frontend uses this to display flagged frames via <img> tags.
    """
    jobs = get_jobs_store()
    job = jobs.get(job_id)
    if job is None:
        abort(404, "Job not found")

    job_dir = Path(job["job_dir"])
    # Search for the file recursively under the job directory
    matches = list(job_dir.rglob(filename))
    if not matches:
        abort(404, "Frame not found")

    frame_path = matches[0]
    # Security: ensure we're not serving files outside the job dir
    if not str(frame_path.resolve()).startswith(str(job_dir.resolve())):
        abort(403, "Access denied")

    # Determine mimetype from extension
    mimetype = "image/png" if frame_path.suffix == ".png" else "image/jpeg"
    return send_file(str(frame_path), mimetype=mimetype)
