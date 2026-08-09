import pytest

from scripts.validate_crash_probability import validate


def test_probability_validation_accepts_valid_out_of_sample_rows():
    report = validate([
        {"probability": 0.10, "crash_event": 0},
        {"probability": 0.20, "crash_event": 0},
        {"probability": 0.30, "crash_event": 1},
    ])
    assert 0 <= report["brier_score"] <= 1
    assert report["status"] == "INSUFFICIENT_EVENTS"


def test_probability_validation_rejects_invalid_probability():
    with pytest.raises(ValueError):
        validate([{"probability": 1.2, "crash_event": 0}])


def test_probability_validation_rejects_invalid_event():
    with pytest.raises(ValueError):
        validate([{"probability": 0.2, "crash_event": 2}])
