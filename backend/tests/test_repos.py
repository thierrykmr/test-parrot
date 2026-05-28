import os
from pathlib import Path
import pytest
import pytest_asyncio  # pyrefly: ignore [missing-import]
import aiosqlite  # pyrefly: ignore [missing-import]
import app.database
from app.repositories import event_repo
from app.services import event_service
from app.database import CREATE_TABLE, CREATE_INDEXES

TEST_DB_PATH = Path(__file__).parent / "test_telemetry.db"

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    # Override database path
    original_db_path = app.database.DB_PATH
    app.database.DB_PATH = TEST_DB_PATH

    # Ensure clean database
    if TEST_DB_PATH.exists():
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass

    # Initialize tables and indexes
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        await db.execute(CREATE_TABLE)
        for idx_sql in CREATE_INDEXES:
            await db.execute(idx_sql)

        # Seed specific events (some normal, and the three trap events)
        test_events = [
            # Normal events
            ("anafi", "flying", 50, "2026-01-10T12:00:00+00:00"),
            ("bebop", "idle", 75, "2026-01-12T10:00:00+00:00"),
            ("disco", "takeoff", 90, "2026-01-14T08:00:00+00:00"),
            ("skycontroller", "landing", 10, "2026-01-16T06:00:00+00:00"),
            # Traps
            ("anafi", "unknown", 78, "2026-01-01T09:00:00+00:00"),       # unknown status
            ("bebop", "idle", -5, "2026-01-03T08:00:00+00:00"),          # negative battery
            ("anafi", "flying", 100, "2025-12-31T23:59:00+00:00"),       # out-of-order timestamp
        ]

        await db.executemany(
            "INSERT INTO events (device, status, battery, timestamp) VALUES (?, ?, ?, ?)",
            test_events
        )
        await db.commit()

    yield

    # Teardown: Restore original DB path and delete test database file
    app.database.DB_PATH = original_db_path
    if TEST_DB_PATH.exists():
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass

@pytest.mark.asyncio
async def test_fetch_events():
    # fetch_events should return all items including anomalies (total count = 7)
    events, total = await event_repo.fetch_events(device=None, status=None, limit=10, offset=0, sort="asc")
    assert total == 7
    assert len(events) == 7
    # 2025-12-31 should be the first when sorted asc
    assert events[0]["timestamp"] == "2025-12-31T23:59:00+00:00"

@pytest.mark.asyncio
async def test_fetch_stats_excludes_anomalies():
    stats = await event_repo.fetch_stats()
    # total counts all events
    assert stats["total"] == 7

    # avg_battery should average [50, 75, 90, 10] => 225 / 4 = 56.25
    # anomalies like -5, status=unknown, or timestamp before 2026 are excluded
    assert stats["avg_battery"] == pytest.approx(56.25)

    # by_status should only contain valid statuses
    statuses = {item["status"]: item["count"] for item in stats["by_status"]}
    assert "unknown" not in statuses
    # verify counts of valid ones
    assert statuses.get("flying") == 1 # 1 valid flying (the anafi event is valid, the 2025 flying is excluded)
    assert statuses.get("idle") == 1   # 1 valid idle (the -5 battery idle is excluded)
    assert statuses.get("takeoff") == 1
    assert statuses.get("landing") == 1

@pytest.mark.asyncio
async def test_search_events_anomaly_only():
    res = await event_service.search_events(device=None, status=None, limit=10, offset=0, sort="asc", anomaly_only=True)
    assert res.total == 3
    assert len(res.items) == 3
    assert all(e.is_anomaly for e in res.items)

    res_page = await event_service.search_events(device=None, status=None, limit=1, offset=1, sort="asc", anomaly_only=True)
    assert res_page.total == 3
    assert len(res_page.items) == 1
    assert res_page.items[0].id == res.items[1].id
