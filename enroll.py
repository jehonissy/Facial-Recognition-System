"""
enroll.py
=========
Handles registering a new person in the system.

Two ways to enroll:
1. From the webcam (default) — captures IMAGES_PER_PERSON photos in a row,
   asking the person to move slightly between shots for better coverage.
2. From an existing folder of photos — pass --image-dir to main.py enroll.

Either way, every photo is converted into a 128-d face encoding and all of
them are stored under the person's name, which makes matching more robust
than relying on a single photo.
"""

import glob
import logging
import os
import time

import cv2
import face_recognition

import config
import utils

logger = logging.getLogger(__name__)


class EnrollmentError(Exception):
    """Raised for expected, user-fixable enrollment problems."""


def _encode_image(image_path: str):
    """Return a single face encoding for one photo, or raise EnrollmentError."""
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)

    if not face_locations:
        raise EnrollmentError(f"No face detected in {os.path.basename(image_path)} — skipping it.")
    if len(face_locations) > 1:
        logger.warning("Multiple faces found in %s; using the largest one.", image_path)
        # Pick the largest bounding box, most likely to be the intended subject.
        face_locations = [max(face_locations, key=lambda box: (box[2] - box[0]) * (box[1] - box[3]))]

    encoding = face_recognition.face_encodings(image, known_face_locations=face_locations)[0]
    return encoding


def enroll_from_images(name: str, image_paths: list) -> int:
    """Encode each image in image_paths and store them under `name`.

    Returns the number of successfully-encoded images.
    """
    person_dir = os.path.join(config.KNOWN_FACES_DIR, name)
    os.makedirs(person_dir, exist_ok=True)

    encodings_db = utils.load_encodings()
    encodings_db.setdefault(name, [])

    success_count = 0
    for idx, path in enumerate(image_paths, start=1):
        try:
            encoding = _encode_image(path)
        except EnrollmentError as e:
            logger.warning(str(e))
            continue

        encodings_db[name].append(encoding)

        # Save a copy of the source photo inside known_faces/<name>/
        ext = os.path.splitext(path)[1] or ".jpg"
        dest = os.path.join(person_dir, f"{name}_{idx:02d}{ext}")
        img = cv2.imread(path)
        if img is not None:
            cv2.imwrite(dest, img)

        success_count += 1

    utils.save_encodings(encodings_db)
    return success_count


def enroll_from_directory(name: str, image_dir: str) -> int:
    """Enroll using every image file found in `image_dir`."""
    if not os.path.isdir(image_dir):
        raise EnrollmentError(f"Image directory not found: {image_dir}")

    patterns = ("*.jpg", "*.jpeg", "*.png")
    image_paths = []
    for pattern in patterns:
        image_paths.extend(glob.glob(os.path.join(image_dir, pattern)))

    if not image_paths:
        raise EnrollmentError(f"No .jpg/.jpeg/.png images found in {image_dir}")

    logger.info("Found %d images for '%s' in %s", len(image_paths), name, image_dir)
    return enroll_from_images(name, image_paths)


def enroll_from_webcam(name: str, num_images: int = config.IMAGES_PER_PERSON,
                        camera_index: int = config.CAMERA_INDEX) -> int:
    """Capture `num_images` photos of the person from the webcam.

    Shows a live preview and automatically captures a shot every
    CAPTURE_DELAY_SECONDS, so the person has time to turn their head
    slightly between captures for more varied encodings.
    """
    video = cv2.VideoCapture(camera_index)
    if not video.isOpened():
        raise EnrollmentError(
            "Could not open webcam. Check that a camera is connected and not in use by another app."
        )

    captured_paths = []
    person_dir = os.path.join(config.KNOWN_FACES_DIR, name)
    os.makedirs(person_dir, exist_ok=True)

    logger.info("Starting webcam enrollment for '%s'. Look at the camera and slowly turn your head "
                "between captures. Press 'q' to cancel early.", name)

    last_capture_time = 0.0
    try:
        while len(captured_paths) < num_images:
            ok, frame = video.read()
            if not ok:
                raise EnrollmentError("Lost connection to the webcam mid-capture.")

            remaining = num_images - len(captured_paths)
            display = frame.copy()
            cv2.putText(display, f"Captures left: {remaining}  (press q to cancel)",
                        (20, 30), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Enrollment - look at the camera", display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                logger.info("Enrollment cancelled by user after %d captures.", len(captured_paths))
                break

            now = time.time()
            if now - last_capture_time >= config.CAPTURE_DELAY_SECONDS:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb)

                if len(face_locations) == 1:
                    idx = len(captured_paths) + 1
                    path = os.path.join(person_dir, f"{name}_{idx:02d}.jpg")
                    cv2.imwrite(path, frame)
                    captured_paths.append(path)
                    last_capture_time = now
                    logger.info("Captured image %d/%d for '%s'.", idx, num_images, name)
                elif len(face_locations) == 0:
                    logger.debug("No face detected in frame, waiting...")
                else:
                    logger.debug("Multiple faces detected, waiting for a single clear face...")
    finally:
        video.release()
        cv2.destroyAllWindows()

    if not captured_paths:
        raise EnrollmentError("No images were captured — enrollment aborted.")

    return enroll_from_images(name, captured_paths)


def list_enrolled_people() -> list:
    """Return a sorted list of names currently in the encodings database."""
    encodings_db = utils.load_encodings()
    return sorted(encodings_db.keys())


def remove_person(name: str) -> bool:
    """Remove a person's encodings and stored photos. Returns True if removed."""
    encodings_db = utils.load_encodings()
    if name not in encodings_db:
        return False

    del encodings_db[name]
    utils.save_encodings(encodings_db)

    person_dir = os.path.join(config.KNOWN_FACES_DIR, name)
    if os.path.isdir(person_dir):
        import shutil
        shutil.rmtree(person_dir)

    return True
