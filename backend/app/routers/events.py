import json
import logging
import time
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response
from app.models.event import EventListResponse
from app.services import event_service

logger = logging.getLogger("telemetry.events")
router = APIRouter()


@router.get("/events", response_model=EventListResponse)
async def search_events(
    response: Response,
    device: Annotated[str | None, Query(description="Filter by device name")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Max results per page")] = 20,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    sort: Annotated[Literal["asc", "desc"], Query(description="Sort order by timestamp")] = "desc",
    anomaly_only: Annotated[bool, Query(description="Only show events flagged as anomalies")] = False,
) -> EventListResponse:
    start = time.perf_counter()

    result = await event_service.search_events(
        device=device,
        status=status,
        limit=limit,
        offset=offset,
        sort=sort,
        anomaly_only=anomaly_only,
    )

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Response-Time"] = f"{elapsed_ms}ms"

    logger.info(
        json.dumps(
            {
                "endpoint": "GET /events",
                "params": {
                    "device": device,
                    "status": status,
                    "limit": limit,
                    "offset": offset,
                    "sort": sort,
                    "anomaly_only": anomaly_only,
                },
                "results_count": result.total,
                "page_count": len(result.items),
                "anomaly_count": result.anomaly_count,
                "elapsed_ms": elapsed_ms,
            }
        )
    )

    return result
