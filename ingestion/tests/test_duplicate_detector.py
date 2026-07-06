import time
import pytest
from ingestion.duplicate_detector import SlidingWindowDuplicateDetector
from ingestion.exceptions import DuplicatePayloadException


def test_duplicate_detector_unique_messages():
    detector = SlidingWindowDuplicateDetector(window_sec=10.0)
    msg1 = {"message_id": "guid-1"}
    msg2 = {"message_id": "guid-2"}
    assert detector.process(msg1) == msg1
    assert detector.process(msg2) == msg2


def test_duplicate_detector_duplicate_exception():
    detector = SlidingWindowDuplicateDetector(window_sec=10.0)
    msg = {"message_id": "guid-dup"}
    detector.process(msg)
    with pytest.raises(DuplicatePayloadException) as exc_info:
        detector.process(msg)
    assert "Duplicate" in str(exc_info.value)


def test_duplicate_detector_window_expiry():
    detector = SlidingWindowDuplicateDetector(window_sec=0.1)
    msg = {"message_id": "guid-exp"}
    detector.process(msg)
    time.sleep(0.15)
    assert detector.process(msg) == msg
