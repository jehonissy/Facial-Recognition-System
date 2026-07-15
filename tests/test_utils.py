import utils


def test_face_distance_confidence_high():
    confidence = utils.face_distance_to_confidence(0.2)
    assert confidence > 80


def test_face_distance_confidence_low():
    confidence = utils.face_distance_to_confidence(0.8)
    assert confidence < 50


def test_timestamp_format():
    ts = utils.timestamp_for_filename()
    assert "_" in ts
    assert "-" in ts


def test_today_str():
    assert len(utils.today_str()) == 10


def test_now_time_str():
    assert len(utils.now_time_str()) == 8
