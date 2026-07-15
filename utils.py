"""
utils.py
========
Small, reusable helpers shared across the project:
- logging setup
- folder creation / validation
- saving & loading cached face encodings
- converting a face-distance score into a human-friendly confidence %
"""

import logging
import os
import pickle
from datetime import datetime

import config


def setup_logging():
    """Configure logging to both console and a rotating-ish log file.

    Call this once, near the start of main.py.
    """
    os.makedirs(config.LOGS_DIR, exist_ok=True)
    level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config.APP_LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def ensure_project_dirs():
    """Create every folder the project expects, if it doesn't already exist."""
    for directory in config.ALL_DIRS:
        os.makedirs(directory, exist_ok=True)


def load_encodings():
    """Load cached {name: [encoding, encoding, ...]} dict from disk.

    Returns an empty dict if no encodings have been saved yet. This is what
    lets the app start instantly instead of re-processing every enrolled
    photo on every launch.
    """
    if not os.path.exists(config.ENCODINGS_FILE):
        return {}
    try:
        with open(config.ENCODINGS_FILE, "rb") as f:
            return pickle.load(f)
    except (pickle.PickleError, EOFError) as e:
        logging.getLogger(__name__).error("Failed to load encodings file, starting fresh: %s", e)
        return {}


def save_encodings(data: dict):
    """Persist the {name: [encodings]} dict to disk."""
    os.makedirs(config.ENCODINGS_DIR, exist_ok=True)
    with open(config.ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)


def face_distance_to_confidence(distance: float, threshold: float = config.MATCH_THRESHOLD) -> float:
    """Convert a face-distance value into an intuitive 0-100% confidence score.

    face_recognition gives us a *distance* (lower = more similar), not a
    percentage. This maps distance -> confidence so smaller distances near 0
    read as high confidence, and distances near/above the match threshold
    read as low confidence. It's a heuristic, not a calibrated probability.
    """
    if distance >= threshold:
        # Still show something meaningful for near-misses, capped low.
        confidence = max(0.0, (1.0 - distance)) * 100
        return min(confidence, 49.9)

    # Scale the "good" range (0 -> threshold) onto (50 -> 100)
    confidence = (1.0 - (distance / threshold)) * 50 + 50
    return round(min(confidence, 100.0), 1)


def timestamp_for_filename() -> str:
    """A filesystem-safe timestamp string, e.g. 2026-07-14_15-30-02."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_time_str() -> str:
    return datetime.now().strftime("%H:%M:%S")
