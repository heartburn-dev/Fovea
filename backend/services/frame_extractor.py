"""
frame_extractor.py – Extract frames from a video file at a given interval
using ffmpeg via subprocess.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when frame extraction fails."""


def extract_frames(
    video_path: str | Path,
    interval: float = 0.5,
    output_dir: str | Path | None = None,
    quality: int = 2,
) -> list[dict]:
    """Extract JPEG frames from *video_path* every *interval* seconds.

    Parameters
    ----------
    video_path:
        Path to the input video file.
    interval:
        Seconds between frames. E.g. 0.5 → 2 frames/s.
    output_dir:
        Where to write the frames. Defaults to a ``frames/`` subdirectory
        next to the video.
    quality:
        JPEG quality (ffmpeg -q:v flag, 2 = high, 31 = low).

    Returns
    -------
    List of dicts, each with keys ``path`` (str) and ``timestamp`` (float, seconds).
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise ExtractionError(f"Video file not found: {video_path}")

    if output_dir is None:
        output_dir = video_path.parent / "frames"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_pattern = str(output_dir / "frame_%05d.png")
    fps = 1 / interval

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-y",
        output_pattern,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            stderr = result.stderr[:500] if result.stderr else "unknown error"
            raise ExtractionError(f"ffmpeg failed (exit {result.returncode}): {stderr}")
    except FileNotFoundError:
        raise ExtractionError("ffmpeg binary not found. Install it with: brew install ffmpeg")
    except subprocess.TimeoutExpired:
        raise ExtractionError("ffmpeg timed out after 600 seconds")

    # Collect produced frames and compute timestamps
    frames = sorted(output_dir.glob("frame_*.png"))
    if not frames:
        raise ExtractionError("ffmpeg ran successfully but produced no frames")

    frame_list = []
    for idx, frame_path in enumerate(frames):
        frame_list.append({
            "path": str(frame_path),
            "filename": frame_path.name,
            "timestamp": round(idx * interval, 2),
        })

    logger.info("Extracted %d frames from %s (interval=%.2fs)", len(frame_list), video_path.name, interval)
    return frame_list
