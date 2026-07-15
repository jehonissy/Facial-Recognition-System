"""
config.py
=========
Single source of truth for paths, tunable parameters, and constants.
Change values here rather than hunting through the other modules.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

KNOWN_FACES_DIR = os.path.join(BASE_DIR, "known_faces")       # per-person photo folders
UNKNOWN_FACES_DIR = os.path.join(BASE_DIR, "unknown_faces")   # auto-saved snapshots of strangers
ENCODINGS_DIR = os.path.join(BASE_DIR, "encodings")           # cached face encodings (.pkl)
ATTENDANCE_DIR = os.path.join(BASE_DIR, "attendance")         # attendance CSV logs
LOGS_DIR = os.path.join(BASE_DIR, "logs")                     # application log files

ENCODINGS_FILE = os.path.join(ENCODINGS_DIR, "encodings.pkl")
ATTENDANCE_FILE = os.path.join(ATTENDANCE_DIR, "attendance.csv")
APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")

ALL_DIRS = [KNOWN_FACES_DIR, UNKNOWN_FACES_DIR, ENCODINGS_DIR, ATTENDANCE_DIR, LOGS_DIR]

# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------
IMAGES_PER_PERSON = 6          # how many webcam captures per enrollment (5-10 recommended)
CAPTURE_DELAY_SECONDS = 1.2    # pause between automatic captures, gives the user time to vary pose

# ---------------------------------------------------------------------------
# Recognition
# ---------------------------------------------------------------------------
MATCH_THRESHOLD = 0.6          # lower = stricter matching (face_recognition library default)
RESIZE_SCALE = 0.25            # frame is shrunk to this fraction before detection (speed)
PROCESS_EVERY_N_FRAMES = 2     # only run detection on every Nth frame; reuse boxes in between
CAMERA_INDEX = 0

# ---------------------------------------------------------------------------
# Unknown face handling
# ---------------------------------------------------------------------------
SAVE_UNKNOWN_FACES = True
UNKNOWN_SAVE_COOLDOWN_SECONDS = 10  # avoid saving 30 photos of the same stranger per second

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
