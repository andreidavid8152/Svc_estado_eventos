import os
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("BACKEND_URL", "http://backend.test")

from scheduler.jobs.process_events import process_events  # noqa: E402
from scheduler.jobs.process_events import process_events_sync  # noqa: E402


class ProcessEventsTests(unittest.IsolatedAsyncioTestCase):
    async def test_process_events_happy_path(self):
        with patch("scheduler.jobs.process_events.backend_client") as mock_client:
            mock_client.get_pending_start_events = AsyncMock(
                return_value=[{"id": 1, "start_date": "2025-01-01T00:00:00"}]
            )
            mock_client.start_event = AsyncMock(return_value=True)
            mock_client.get_pending_finish_events = AsyncMock(
                return_value=[{"id": 2, "end_date": "2025-01-01T01:00:00"}]
            )
            mock_client.finish_event = AsyncMock(return_value=True)
            mock_client.process_event_completion = AsyncMock(return_value=True)
            mock_client.cleanup_stale_monitoring_by_logs = AsyncMock(
                return_value={"success": True, "stale_count": 0}
            )

            await process_events()

            mock_client.start_event.assert_awaited_once_with(1)
            mock_client.finish_event.assert_awaited_once_with(2)
            mock_client.process_event_completion.assert_awaited_once_with(2)
            mock_client.cleanup_stale_monitoring_by_logs.assert_awaited_once_with(60)

    async def test_process_events_no_pending_events(self):
        with patch("scheduler.jobs.process_events.backend_client") as mock_client:
            mock_client.get_pending_start_events = AsyncMock(return_value=[])
            mock_client.get_pending_finish_events = AsyncMock(return_value=[])
            mock_client.cleanup_stale_monitoring_by_logs = AsyncMock(
                return_value={"success": True, "stale_count": 0}
            )

            await process_events()

            mock_client.start_event.assert_not_called()
            mock_client.finish_event.assert_not_called()
            mock_client.process_event_completion.assert_not_called()
            mock_client.cleanup_stale_monitoring_by_logs.assert_awaited_once_with(60)

    async def test_process_events_handles_start_exception(self):
        with patch("scheduler.jobs.process_events.backend_client") as mock_client:
            mock_client.get_pending_start_events = AsyncMock(
                side_effect=RuntimeError("boom")
            )
            mock_client.get_pending_finish_events = AsyncMock(return_value=[])
            mock_client.cleanup_stale_monitoring_by_logs = AsyncMock(
                return_value={"success": True, "stale_count": 0}
            )

            await process_events()

            mock_client.get_pending_finish_events.assert_awaited_once()
            mock_client.cleanup_stale_monitoring_by_logs.assert_awaited_once_with(60)

    async def test_process_events_handles_finish_exception(self):
        with patch("scheduler.jobs.process_events.backend_client") as mock_client:
            mock_client.get_pending_start_events = AsyncMock(return_value=[])
            mock_client.get_pending_finish_events = AsyncMock(
                side_effect=RuntimeError("boom")
            )
            mock_client.cleanup_stale_monitoring_by_logs = AsyncMock(
                return_value={"success": True, "stale_count": 0}
            )

            await process_events()

            mock_client.get_pending_start_events.assert_awaited_once()
            mock_client.cleanup_stale_monitoring_by_logs.assert_awaited_once_with(60)

    async def test_process_events_finish_processing_failure(self):
        with patch("scheduler.jobs.process_events.backend_client") as mock_client:
            mock_client.get_pending_start_events = AsyncMock(return_value=[])
            mock_client.get_pending_finish_events = AsyncMock(
                return_value=[{"id": 3, "end_date": "2025-01-01T01:00:00"}]
            )
            mock_client.finish_event = AsyncMock(return_value=True)
            mock_client.process_event_completion = AsyncMock(return_value=False)
            mock_client.cleanup_stale_monitoring_by_logs = AsyncMock(
                return_value={"success": True, "stale_count": 0}
            )

            await process_events()

            mock_client.finish_event.assert_awaited_once_with(3)
            mock_client.process_event_completion.assert_awaited_once_with(3)
            mock_client.cleanup_stale_monitoring_by_logs.assert_awaited_once_with(60)


class ProcessEventsSyncTests(unittest.TestCase):
    def test_process_events_sync_runs_coroutine(self):
        async def dummy():
            return "ok"

        with patch("scheduler.jobs.process_events.process_events", new=dummy):
            process_events_sync()
