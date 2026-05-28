from datetime import datetime, timezone
import pytest
from app.models.event import EventRaw

def test_valid_event():
    raw = EventRaw(
        id=1,
        device="anafi",
        status="flying",
        battery=50,
        timestamp=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    )
    out = raw.to_out()
    assert out.is_anomaly is False
    assert out.anomaly_reason is None

def test_invalid_battery_negative():
    raw = EventRaw(
        id=2,
        device="bebop",
        status="idle",
        battery=-5,
        timestamp=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    )
    out = raw.to_out()
    assert out.is_anomaly is True
    assert "battery out of range" in out.anomaly_reason

def test_invalid_battery_high():
    raw = EventRaw(
        id=3,
        device="bebop",
        status="idle",
        battery=105,
        timestamp=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    )
    out = raw.to_out()
    assert out.is_anomaly is True
    assert "battery out of range" in out.anomaly_reason

def test_unknown_status():
    raw = EventRaw(
        id=4,
        device="anafi",
        status="unknown",
        battery=80,
        timestamp=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    )
    out = raw.to_out()
    assert out.is_anomaly is True
    assert "unknown status" in out.anomaly_reason

def test_out_of_order_timestamp():
    raw = EventRaw(
        id=5,
        device="anafi",
        status="flying",
        battery=100,
        timestamp=datetime(2025, 12, 31, 23, 59, 0, tzinfo=timezone.utc)
    )
    out = raw.to_out()
    assert out.is_anomaly is True
    assert "timestamp out of order" in out.anomaly_reason

def test_multiple_anomalies():
    raw = EventRaw(
        id=6,
        device="anafi",
        status="unknown",
        battery=-10,
        timestamp=datetime(2025, 12, 31, 23, 59, 0, tzinfo=timezone.utc)
    )
    out = raw.to_out()
    assert out.is_anomaly is True
    assert "battery out of range" in out.anomaly_reason
    assert "unknown status" in out.anomaly_reason
    assert "timestamp out of order" in out.anomaly_reason
