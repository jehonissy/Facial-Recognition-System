import csv
import attendance


def test_attendance_logger_creates_instance():
    logger = attendance.AttendanceLogger()
    assert logger is not None


def test_mark_present(tmp_path, monkeypatch):
    test_file = tmp_path / "attendance.csv"
    monkeypatch.setattr(attendance.config, "ATTENDANCE_FILE", str(test_file))
    monkeypatch.setattr(attendance.config, "ATTENDANCE_DIR", str(tmp_path))

    logger = attendance.AttendanceLogger()
    logger.mark_present("Alice")

    with open(test_file, newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["Name"] == "Alice"
