"""
scan.py – POST /api/scan endpoint.

Accepts a list of YouTube URLs and a frame interval, then:
  1. Downloads each video
  2. Extracts frames at the specified interval
  3. Runs the secrets-detection model on every frame
  4. Returns results grouped by video
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request

from backend.services.downloader import download_video, DownloadError
from backend.services.frame_extractor import extract_frames, ExtractionError
from backend.services.detector import analyze_frames, DetectorError

logger = logging.getLogger(__name__)

scan_bp = Blueprint("scan", __name__)

# In-memory store: job_id → results dict.
# For a single-user local tool this is fine.
_jobs: dict[str, dict] = {}


def get_jobs_store() -> dict[str, dict]:
    """Expose jobs store so other blueprints can read results."""
    return _jobs


@scan_bp.route("/api/scan", methods=["POST"])
def start_scan():
    """Kick off a scan.

    Request JSON
    -------------
    {
        "urls": ["https://youtube.com/watch?v=..."],
        "interval": 0.5,       // seconds between frames (0.1 – 2.0)
        "threshold": 0.5       // optional confidence threshold
    }

    Response JSON
    -------------
    {
        "job_id": "...",
        "videos": [
            {
                "url": "...",
                "status": "ok" | "error",
                "error": "..." | null,
                "total_frames": 12,
                "flagged_frames": 2,
                "frames": [ ... ]       // only flagged frames
            }
        ],
        "summary": {
            "total_videos": 1,
            "total_frames": 12,
            "total_flagged": 2
        }
    }
    """
    data = request.get_json(silent=True) or {}

    urls = data.get("urls")
    if not urls or not isinstance(urls, list):
        return jsonify({"error": "Provide a non-empty 'urls' array."}), 400

    interval = float(data.get("interval", 0.5))
    if not (0.1 <= interval <= 2.0):
        return jsonify({"error": "interval must be between 0.1 and 2.0 seconds."}), 400

    threshold = float(data.get("threshold", 0.75))

    job_id = str(uuid.uuid4())
    job_dir = Path(tempfile.mkdtemp(prefix=f"fovea_{job_id[:8]}_"))
    videos_results = []
    total_frames_all = 0
    total_flagged_all = 0

    for url in urls:
        video_result: dict = {"url": url, "status": "ok", "error": None}
        try:
            # 1. Download
            logger.info("[%s] Downloading %s", job_id[:8], url)
            video_dir = job_dir / uuid.uuid4().hex[:8]
            video_dir.mkdir()
            video_path = download_video(url, dest_dir=str(video_dir))

            # 2. Extract frames
            logger.info("[%s] Extracting frames (interval=%.2fs)", job_id[:8], interval)
            frames_dir = video_dir / "frames"
            frame_list = extract_frames(video_path, interval=interval, output_dir=frames_dir)

            # 3. Run detector
            logger.info("[%s] Analyzing %d frames", job_id[:8], len(frame_list))
            results = analyze_frames(frame_list, threshold=threshold)

            flagged = [r for r in results if r["flagged"]]
            # Strip absolute paths – expose only filename for the API
            for r in results:
                r["path"] = str(r["path"])  # keep full path for serving

            video_result["total_frames"] = len(results)
            video_result["flagged_frames"] = len(flagged)
            video_result["frames"] = flagged  # only return flagged frames
            total_frames_all += len(results)
            total_flagged_all += len(flagged)

        except (DownloadError, ExtractionError, DetectorError) as exc:
            logger.warning("[%s] Pipeline error for %s: %s", job_id[:8], url, exc)
            video_result["status"] = "error"
            video_result["error"] = str(exc)
            video_result["total_frames"] = 0
            video_result["flagged_frames"] = 0
            video_result["frames"] = []

        videos_results.append(video_result)

    job_data = {
        "job_id": job_id,
        "job_dir": str(job_dir),
        "videos": videos_results,
        "summary": {
            "total_videos": len(urls),
            "total_frames": total_frames_all,
            "total_flagged": total_flagged_all,
        },
    }
    _jobs[job_id] = job_data

    return jsonify(job_data), 200


@scan_bp.route("/api/jobs/<job_id>", methods=["DELETE"])
def cleanup_job(job_id: str):
    """Delete temp files for a job."""
    job = _jobs.pop(job_id, None)
    if job is None:
        return jsonify({"error": "Job not found."}), 404
    job_dir = job.get("job_dir")
    if job_dir and Path(job_dir).exists():
        shutil.rmtree(job_dir, ignore_errors=True)
        logger.info("Cleaned up job %s", job_id[:8])
    return jsonify({"status": "deleted"}), 200
