from typing import Literal
from fastapi import HTTPException
from app.models.event import EventListResponse, EventRaw, StatsOut, ByStatusEntry
from app.repositories import event_repo

MAX_LIMIT = 100


async def search_events(
    device: str | None,
    status: str | None,
    limit: int,
    offset: int,
    sort: Literal["asc", "desc"],
    anomaly_only: bool = False,
) -> EventListResponse:
    if limit < 1 or limit > MAX_LIMIT:
        raise HTTPException(
            status_code=422,
            detail=f"limit must be between 1 and {MAX_LIMIT}",
        )
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be >= 0")

    if anomaly_only:
        # Fetch all matching records to validate and filter anomalies in memory
        rows, _ = await event_repo.fetch_events(
            device=device,
            status=status,
            limit=-1,
            offset=0,
            sort=sort,
        )
        all_parsed = [EventRaw.model_validate(r).to_out() for r in rows]
        anomalies = [e for e in all_parsed if e.is_anomaly]
        
        total = len(anomalies)
        paginated = anomalies[offset : offset + limit]
        anomaly_count = len(paginated)
        items = paginated
    else:
        rows, total = await event_repo.fetch_events(
            device=device,
            status=status,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        items = [EventRaw.model_validate(r).to_out() for r in rows]
        anomaly_count = sum(1 for e in items if e.is_anomaly)

    return EventListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        anomaly_count=anomaly_count,
    )


async def get_stats() -> StatsOut:
    raw = await event_repo.fetch_stats()
    return StatsOut(
        total=raw["total"],
        avg_battery=round(raw["avg_battery"], 2),
        by_status=[ByStatusEntry(**entry) for entry in raw["by_status"]],
    )
