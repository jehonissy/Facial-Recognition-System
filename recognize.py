"""
recognize.py
============
Runs the live webcam loop: detect faces, match them against enrolled
encodings, draw labeled boxes with confidence percentages, optionally log
attendance, and automatically save snapshots of unrecognized people.
"""

import logging
import os
import time

import cv2
import face_recognition
import numpy as np

import config
import utils
from attendance import AttendanceLogger

logger = logging.getLogger(__name__)


class FaceRecognizer:
    """Wraps the enrolled-encodings database and does the distance matching."""

    def __init__(self):
        self.names = []
        self.encodings = []
        self.reload()

    def reload(self):
        """(Re)load the cached encodings from disk into memory."""
        db = utils.load_encodings()
        self.names = []
        self.encodings = []
        for name, enc_list in db.items():
            for enc in enc_list:
                self.names.append(name)
                self.encodings.append(enc)
        logger.info("Loaded %d face encodings for %d people.", len(self.encodings), len(set(self.names)))

    def match(self, face_encoding):
        """Return (name, confidence_percent) for one face encoding.

        name is "Unknown" if nothing is close enough under MATCH_THRESHOLD.
        """
        if not self.encodings:
            return "Unknown", 0.0

        distances = face_recognition.face_distance(self.encodings, face_encoding)
        best_idx = int(np.argmin(distances))
        best_distance = distances[best_idx]

        confidence = utils.face_distance_to_confidence(best_distance)

        if best_distance <= config.MATCH_THRESHOLD:
            return self.names[best_idx], confidence
        return "Unknown", confidence


def _save_unknown_face(frame, box, last_saved_at: float) -> float:
    """Save a snapshot of an unrecognized face, respecting a cooldown so we
    don't flood the folder with near-duplicate frames of the same stranger.
    Returns the (possibly updated) last_saved_at timestamp.
    """
    now = time.time()
    if now - last_saved_at < config.UNKNOWN_SAVE_COOLDOWN_SECONDS:
        return last_saved_at

    top, right, bottom, left = box
    os.makedirs(config.UNKNOWN_FACES_DIR, exist_ok=True)
    filename = f"unknown_{utils.timestamp_for_filename()}.jpg"
    path = os.path.join(config.UNKNOWN_FACES_DIR, filename)

    # Save the full frame (more context than a tight crop) with a small margin crop option.
    crop = frame[max(0, top - 20):bottom + 20, max(0, left - 20):right + 20]
    target = crop if crop.size > 0 else frame
    cv2.imwrite(path, target)
    logger.info("Saved unknown face snapshot: %s", filename)
    return now


def run(attendance: bool = False, camera_index: int = None):
    """Main live-recognition loop. Press 'q' in the video window to quit."""
    camera_index = config.CAMERA_INDEX if camera_index is None else camera_index

    recognizer = FaceRecognizer()
    if not recognizer.encodings:
        logger.warning("No enrolled faces found. Run 'python main.py enroll --name X' first.")

    attendance_logger = AttendanceLogger() if attendance else None

    video = cv2.VideoCapture(camera_index)
    if not video.isOpened():
        logger.error("Could not open webcam (index %s). Check the camera connection/permissions.", camera_index)
        return

    frame_count = 0
    last_boxes = []            # cached (top, right, bottom, left, name, confidence)
    last_unknown_saved_at = 0.0

    logger.info("Starting recognition. Press 'q' to quit.")

    try:
        while True:
            ok, frame = video.read()
            if not ok:
                logger.error("Failed to read frame from webcam — stopping.")
                break

            frame_count += 1

            # Only run the (expensive) detection+encoding every Nth frame;
            # reuse the previous frame's boxes in between for smooth video.
            if frame_count % config.PROCESS_EVERY_N_FRAMES == 0:
                small = cv2.resize(frame, (0, 0), fx=config.RESIZE_SCALE, fy=config.RESIZE_SCALE)
                rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

                face_locations = face_recognition.face_locations(rgb_small)
                face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

                last_boxes = []
                for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
                    name, confidence = recognizer.match(encoding)

                    # Scale coordinates back up to the original frame size.
                    scale = 1 / config.RESIZE_SCALE
                    box = (int(top * scale), int(right * scale), int(bottom * scale), int(left * scale))
                    last_boxes.append((*box, name, confidence))

                    if name != "Unknown" and attendance_logger:
                        attendance_logger.mark_present(name)
                    elif name == "Unknown" and config.SAVE_UNKNOWN_FACES:
                        last_unknown_saved_at = _save_unknown_face(frame, box, last_unknown_saved_at)

            # Draw whatever boxes we currently have (fresh or cached).
            for (top, right, bottom, left, name, confidence) in last_boxes:
                color = (0, 200, 0) if name != "Unknown" else (0, 0, 255)
                label = f"{name} ({confidence:.1f}%)" if name != "Unknown" else "Unknown"

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, label, (left + 6, bottom - 8),
                            cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1)

            cv2.imshow("Facial Recognition (press q to quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        video.release()
        cv2.destroyAllWindows()
        logger.info("Recognition stopped.")
