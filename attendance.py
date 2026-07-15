"""
attendance.py
=============
Handles writing attendance records to a CSV file, with Name / Date / Time
columns, and prevents logging the same person twice on the same day.
"""

import csv
import logging
import os

import config
import utils

logger = logging.getLogger(__name__)


class AttendanceLogger:
    """Tracks who has already been marked present today to avoid duplicates."""

    def __init__(self):
        os.makedirs(config.ATTENDANCE_DIR, exist_ok=True)
        self._ensure_file_has_header()
        self._marked_today = self._load_todays_names()

    def _ensure_file_has_header(self):
        if not os.path.exists(config.ATTENDANCE_FILE):
            with open(config.ATTENDANCE_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Date", "Time"])

    def _load_todays_names(self) -> set:
        """Read the CSV once at startup so we know who's already logged today,
        even if the app was restarted.
        """
        today = utils.today_str()
        names = set()
        try:
            with open(config.ATTENDANCE_FILE, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Date") == today:
                        names.add(row.get("Name"))
        except FileNotFoundError:
            pass
        return names

    def mark_present(self, name: str):
        """Log `name` as present now, unless already logged today."""
        if name in self._marked_today or name == "Unknown":
            return

        date_str = utils.today_str()
        time_str = utils.now_time_str()

        with open(config.ATTENDANCE_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([name, date_str, time_str])

        self._marked_today.add(name)
        logger.info("Attendance marked: %s at %s on %s", name, time_str, date_str)

    def read_all(self) -> list:
        """Return all attendance rows as a list of dicts (for GUI/reporting)."""
        if not os.path.exists(config.ATTENDANCE_FILE):
            return []
        with open(config.ATTENDANCE_FILE, "r", newline="") as f:
            return list(csv.DictReader(f))
