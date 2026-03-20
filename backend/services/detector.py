"""
detector.py – Load a FastAI secrets-detection model and run inference on frames.

The model is expected to be a FastAI exported learner (.pkl) that classifies
images into two categories (e.g. "secret" / "no_secret") or similar.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded singleton for the FastAI learner
# ---------------------------------------------------------------------------
_learner: Any | None = None

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
DEFAULT_MODEL = MODEL_DIR / "fovea_model.pkl"

# Confidence threshold above which a frame is considered "flagged"
DEFAULT_THRESHOLD = 0.75


class DetectorError(Exception):
    """Raised when model loading or inference fails."""


def _load_model(model_path: Path | None = None) -> Any:
    """Load the FastAI learner (cached after first call)."""
    global _learner
    if _learner is not None:
        return _learner

    model_path = model_path or DEFAULT_MODEL
    if not model_path.exists():
        raise DetectorError(
            f"Model file not found at {model_path}. "
            "Download your model from Kaggle and place it in backend/models/"
        )

    try:
        import torch
        import pickle
        import fastai.vision.all  # noqa: F401 – ensure fastai classes are registered for unpickling

        logger.info("Loading model from %s …", model_path)

        # Bypass fastai's load_learner which has a bug in v2.8.x where an
        # ImportError during unpickling leaves `res` unbound. We replicate
        # what load_learner does, minus the buggy error handling.
        res = torch.load(
            model_path,
            map_location="cpu",
            pickle_module=pickle,
            weights_only=False,
        )
        res.dls.cpu()
        if hasattr(res, "channels_last"):
            res = res.to_contiguous(to_fp32=True)
        elif hasattr(res, "mixed_precision"):
            res = res.to_fp32()
        elif hasattr(res, "non_native_mixed_precision"):
            res = res.to_non_native_fp32()

        _learner = res
        logger.info("Model loaded successfully. Categories: %s", _learner.dls.vocab)
        return _learner
    except ImportError as exc:
        raise DetectorError(
            f"fastai import failed: {exc}"
        ) from exc
    except Exception as exc:
        raise DetectorError(f"Failed to load model: {exc}") from exc


def analyze_frame(
    frame_path: str | Path,
    threshold: float = DEFAULT_THRESHOLD,
    learner: Any | None = None,
) -> dict:
    """Run the secrets-detection model on a single frame.

    Returns
    -------
    dict with keys:
        - ``label``       : predicted class name (str)
        - ``confidence``  : probability of the predicted class (float, 0-1)
        - ``flagged``     : True if the model thinks this frame contains a secret
        - ``all_probs``   : dict mapping each class name to its probability
    """
    learner = learner or _load_model()
    frame_path = Path(frame_path)

    if not frame_path.exists():
        raise DetectorError(f"Frame not found: {frame_path}")

    try:
        img = Image.open(frame_path).convert("RGB")
        img.load()  # force full read into memory before PIL closes the file
        pred_class, pred_idx, probs = learner.predict(img)
    except Exception as exc:
        logger.exception("Inference failed on %s", frame_path.name)
        raise DetectorError(f"Inference failed on {frame_path.name}: {type(exc).__name__}: {exc}") from exc

    vocab = learner.dls.vocab
    all_probs = {str(vocab[i]): round(float(probs[i]), 4) for i in range(len(vocab))}
    confidence = float(probs[pred_idx])

    # invalid = probs[0]
    # valid = probs[1]
    valid_probability = float(probs[1])
    flagged = valid_probability >= threshold

    return {
        "label": str(pred_class),
        "confidence": round(confidence, 4),
        "flagged": flagged,
        "all_probs": all_probs,
    }


def analyze_frames(
    frame_list: list[dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> list[dict]:
    """Run the detector on a list of frames (as returned by frame_extractor).

    Each input dict is expected to have at least a ``path`` key.
    Returns a new list of dicts, each augmented with detection results.
    """
    learner = _load_model()
    results = []
    flagged_count = 0

    for frame_info in frame_list:
        detection = analyze_frame(
            frame_info["path"],
            threshold=threshold,
            learner=learner,
        )
        result = {**frame_info, **detection}
        results.append(result)
        if result["flagged"]:
            flagged_count += 1

    logger.info(
        "Analysis complete: %d/%d frames flagged (threshold=%.2f)",
        flagged_count,
        len(frame_list),
        threshold,
    )
    return results
