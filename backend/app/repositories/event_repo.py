from typing import Literal
# pyrefly: ignore [missing-import]
import aiosqlite
from app.database import get_db_path


async def fetch_events(
    device: str | None,
    status: str | None,
    limit: int,
    offset: int,
    sort: Literal["asc", "desc"],
) -> tuple[list[dict], int]:
    """
    Returns (rows, total_count).
    Uses a single query with COUNT(*) OVER() to avoid a second round-trip.
    Parameterized queries only — no f-string interpolation of user input.
    The ORDER BY direction is safe because it comes from a validated Literal.
    """
    conditions: list[str] = []
    params: list[object] = []

    if device:
        conditions.append("device = ?")
        params.append(device)
    if status:
        conditions.append("status = ?")
        params.append(status)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    # COUNT(*) OVER() computes the total without a second query
    order = "ASC" if sort == "asc" else "DESC"
    sql = f"""
        SELECT id, device, status, battery, timestamp,
               COUNT(*) OVER() AS _total
        FROM events
        {where}
        ORDER BY timestamp {order}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return [], 0

    total = rows[0]["_total"]
    dicts = [
        {
            "id": r["id"],
            "device": r["device"],
            "status": r["status"],
            "battery": r["battery"],
            "timestamp": r["timestamp"],
        }
        for r in rows
    ]
    return dicts, total


async def fetch_stats() -> dict:
    """
    Aggregation done entirely in SQL — no Python loop over rows.
    Returns raw dict with total, avg_battery, and per-status breakdown.
    Filters out anomalous data from averages and breakdown counts.
    """
    sql_global = """
        SELECT 
            COUNT(*) AS total,
            AVG(CASE 
                WHEN battery BETWEEN 0 AND 100 
                     AND status IN ('flying', 'landing', 'idle', 'takeoff')
                     AND timestamp >= '2026-01-01' 
                THEN battery 
            END) AS avg_battery
        FROM events
    """
    sql_by_status = """
        SELECT status, COUNT(*) AS count 
        FROM events 
        WHERE status IN ('flying', 'landing', 'idle', 'takeoff')
          AND battery BETWEEN 0 AND 100
          AND timestamp >= '2026-01-01'
        GROUP BY status 
        ORDER BY count DESC
    """

    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(sql_global) as cur:
            global_row = await cur.fetchone()

        async with db.execute(sql_by_status) as cur:
            status_rows = await cur.fetchall()

    return {
        "total": global_row["total"],
        "avg_battery": global_row["avg_battery"] or 0.0,
        "by_status": [
            {"status": r["status"], "count": r["count"]} for r in status_rows
        ],
    }
