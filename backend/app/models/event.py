from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

KNOWN_STATUSES = {"flying", "landing", "idle", "takeoff"}


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device: str
    status: str
    battery: int
    timestamp: datetime
    is_anomaly: bool = False
    anomaly_reason: str | None = None


class EventRaw(BaseModel):
    """Used internally when reading rows from SQLite — validates and flags anomalies."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device: str
    status: str
    battery: int
    timestamp: datetime

    @field_validator("battery", mode="before")
    @classmethod
    def battery_range(cls, v: Any) -> int:
        val = int(v)
        if val < 0 or val > 100:
            # We don't raise here — we tag the anomaly in model_validator
            pass
        return val

    @model_validator(mode="after")
    def flag_anomalies(self) -> "EventRaw":
        reasons = []
        if self.battery < 0 or self.battery > 100:
            reasons.append(f"battery out of range ({self.battery})")
        if self.status not in KNOWN_STATUSES:
            reasons.append(f"unknown status '{self.status}'")
        
        # Check for out-of-order timestamp (before 2026-01-01)
        from datetime import timezone
        baseline = datetime(2026, 1, 1, tzinfo=timezone.utc)
        ts = self.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts < baseline:
            reasons.append(f"timestamp out of order ({self.timestamp.isoformat()})")

        self._anomaly_reasons = reasons
        return self

    def to_out(self) -> EventOut:
        reasons = getattr(self, "_anomaly_reasons", [])
        return EventOut(
            id=self.id,
            device=self.device,
            status=self.status,
            battery=self.battery,
            timestamp=self.timestamp,
            is_anomaly=bool(reasons),
            anomaly_reason="; ".join(reasons) if reasons else None,
        )


class EventListResponse(BaseModel):
    items: list[EventOut]
    total: int
    limit: int
    offset: int
    anomaly_count: int = 0


class ByStatusEntry(BaseModel):
    status: str
    count: int


class StatsOut(BaseModel):
    total: int
    avg_battery: float
    by_status: list[ByStatusEntry]
