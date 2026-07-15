"""
main.py
=======
Command-line entry point.

Usage:
    python main.py enroll --name "Person Name"                  (webcam capture)
    python main.py enroll --name "Person Name" --image-dir DIR  (from existing photos)
    python main.py run
    python main.py run --attendance
    python main.py list
    python main.py remove --name "Person Name"
"""

import argparse
import logging
import sys

import config
import utils
import enroll
import recognize

logger = logging.getLogger(__name__)


def cmd_enroll(args):
    try:
        if args.image_dir:
            count = enroll.enroll_from_directory(args.name, args.image_dir)
        else:
            count = enroll.enroll_from_webcam(args.name, num_images=args.num_images)

        if count:
            print(f"Enrolled '{args.name}' with {count} face image(s).")
        else:
            print(f"Enrollment for '{args.name}' failed — no usable face images.")
            sys.exit(1)
    except enroll.EnrollmentError as e:
        logger.error(str(e))
        print(f"Error: {e}")
        sys.exit(1)


def cmd_run(args):
    recognize.run(attendance=args.attendance, camera_index=args.camera_index)


def cmd_list(_args):
    people = enroll.list_enrolled_people()
    if not people:
        print("No one is enrolled yet. Try: python main.py enroll --name \"Your Name\"")
        return
    print(f"Enrolled people ({len(people)}):")
    for name in people:
        print(f"  - {name}")


def cmd_remove(args):
    removed = enroll.remove_person(args.name)
    if removed:
        print(f"Removed '{args.name}' from the system.")
    else:
        print(f"No enrolled person named '{args.name}' was found.")
        sys.exit(1)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Facial Recognition System — enroll people and recognize them via webcam."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_enroll = sub.add_parser("enroll", help="Register a new person")
    p_enroll.add_argument("--name", required=True, help="Person's name/label")
    p_enroll.add_argument("--image-dir", default=None,
                           help="Optional folder of existing photos instead of webcam capture")
    p_enroll.add_argument("--num-images", type=int, default=config.IMAGES_PER_PERSON,
                           help=f"Number of webcam captures (default {config.IMAGES_PER_PERSON})")
    p_enroll.set_defaults(func=cmd_enroll)

    p_run = sub.add_parser("run", help="Start live webcam recognition")
    p_run.add_argument("--attendance", action="store_true", help="Log attendance for recognized people")
    p_run.add_argument("--camera-index", type=int, default=config.CAMERA_INDEX, help="Webcam index")
    p_run.set_defaults(func=cmd_run)

    p_list = sub.add_parser("list", help="List all enrolled people")
    p_list.set_defaults(func=cmd_list)

    p_remove = sub.add_parser("remove", help="Remove an enrolled person")
    p_remove.add_argument("--name", required=True, help="Person's name/label to remove")
    p_remove.set_defaults(func=cmd_remove)

    return parser


def main():
    utils.ensure_project_dirs()
    utils.setup_logging()

    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
