"""
downloader.py – Download a YouTube video to a temporary directory using yt-dlp.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import yt_dlp

logger = logging.getLogger(__name__)

# yt-dlp options: download best available quality, merge to mp4
_YDL_BASE_OPTS: dict = {
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "merge_output_format": "mp4",
    "quiet": True,
    "no_warnings": True,
    # Restrict filenames to ASCII to avoid path issues
    "restrictfilenames": True,
}


class DownloadError(Exception):
    """Raised when a video cannot be downloaded."""


def download_video(url: str, dest_dir: str | None = None) -> Path:
    """Download a YouTube video and return the path to the .mp4 file.

    Parameters
    ----------
    url:
        Full YouTube URL (e.g. https://www.youtube.com/watch?v=...).
    dest_dir:
        Directory to save the file in. A new temp directory is created if not
        provided.

    Returns
    -------
    Path to the downloaded mp4 file.

    Raises
    ------
    DownloadError
        If the download fails for any reason (private video, geo-block, bad URL, …).
    """
    if dest_dir is None:
        dest_dir = tempfile.mkdtemp(prefix="fovea_")

    output_template = os.path.join(dest_dir, "%(id)s.%(ext)s")

    opts = {
        **_YDL_BASE_OPTS,
        "outtmpl": output_template,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # yt-dlp fills in the final filename
            filename = ydl.prepare_filename(info)
            # After merge the extension may differ; prefer .mp4
            mp4_path = Path(filename).with_suffix(".mp4")
            if not mp4_path.exists():
                # Fallback: find whatever file was written
                candidates = list(Path(dest_dir).glob(f"{info['id']}.*"))
                if not candidates:
                    raise DownloadError(f"Download succeeded but no file found in {dest_dir}")
                mp4_path = candidates[0]
            logger.info("Downloaded %s → %s", url, mp4_path)
            return mp4_path
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(str(exc)) from exc
    except Exception as exc:
        raise DownloadError(f"Unexpected error downloading {url}: {exc}") from exc
