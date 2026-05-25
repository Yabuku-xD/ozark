from backend import models


def test_iso_now_returns_iso_timestamp():
    timestamp = models.iso_now()

    assert "T" in timestamp
    assert timestamp.endswith("Z")
