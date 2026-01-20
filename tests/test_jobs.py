import os
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("BACKEND_URL", "http://backend.test")

from scheduler.jobs.start_events import (  # noqa: E402
    start_pending_events,
    start_pending_events_sync,
)
from scheduler.jobs.finish_events import (  # noqa: E402
    finish_pending_events,
    finish_pending_events_sync,
)


class StartPendingEventsTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_pending_events_no_pending(self):
        with patch("scheduler.jobs.start_events.backend_client") as mock_client:
            mock_client.get_pending_start_events = AsyncMock(return_value=[])

            await start_pending_events()

            mock_client.start_event.assert_not_called()

    async def test_start_pending_events_mixed_results(self):
        with patch("scheduler.jobs.start_events.backend_client") as mock_client:
            mock_client.get_pending_start_events = AsyncMock(
                return_value=[
                    {"id": 1, "start_date": "2025-01-01T00:00:00"},
                    {"id": 2, "start_date": "2025-01-01T00:10:00"},
                ]
            )
            mock_client.start_event = AsyncMock(side_effect=[True, False])

            await start_pending_events()

            self.assertEqual(mock_client.start_event.await_count, 2)

    async def test_start_pending_events_handles_exception(self):
        with patch("scheduler.jobs.start_events.backend_client") as mock_client:
            mock_client.get_pending_start_events = AsyncMock(
                side_effect=RuntimeError("boom")
            )

            await start_pending_events()

            mock_client.start_event.assert_not_called()


class FinishPendingEventsTests(unittest.IsolatedAsyncioTestCase):
    async def test_finish_pending_events_no_pending(self):
        with patch("scheduler.jobs.finish_events.backend_client") as mock_client:
            mock_client.get_pending_finish_events = AsyncMock(return_value=[])

            await finish_pending_events()

            mock_client.finish_event.assert_not_called()
            mock_client.process_event_completion.assert_not_called()

    async def test_finish_pending_events_success_triggers_processing(self):
        with patch("scheduler.jobs.finish_events.backend_client") as mock_client:
            mock_client.get_pending_finish_events = AsyncMock(
                return_value=[{"id": 3, "end_date": "2025-01-01T01:00:00"}]
            )
            mock_client.finish_event = AsyncMock(return_value=True)
            mock_client.process_event_completion = AsyncMock(return_value=True)

            await finish_pending_events()

            mock_client.finish_event.assert_awaited_once_with(3)
            mock_client.process_event_completion.assert_awaited_once_with(3)

    async def test_finish_pending_events_finish_failure_skips_processing(self):
        with patch("scheduler.jobs.finish_events.backend_client") as mock_client:
            mock_client.get_pending_finish_events = AsyncMock(
                return_value=[{"id": 4, "end_date": "2025-01-01T02:00:00"}]
            )
            mock_client.finish_event = AsyncMock(return_value=False)
            mock_client.process_event_completion = AsyncMock(return_value=True)

            await finish_pending_events()

            mock_client.finish_event.assert_awaited_once_with(4)
            mock_client.process_event_completion.assert_not_called()

    async def test_finish_pending_events_handles_exception(self):
        with patch("scheduler.jobs.finish_events.backend_client") as mock_client:
            mock_client.get_pending_finish_events = AsyncMock(
                side_effect=RuntimeError("boom")
            )

            await finish_pending_events()

            mock_client.finish_event.assert_not_called()


class JobSyncWrapperTests(unittest.TestCase):
    def test_start_pending_events_sync_runs_coroutine(self):
        async def dummy():
            return "ok"

        with patch("scheduler.jobs.start_events.start_pending_events", new=dummy):
            start_pending_events_sync()

    def test_finish_pending_events_sync_runs_coroutine(self):
        async def dummy():
            return "ok"

        with patch("scheduler.jobs.finish_events.finish_pending_events", new=dummy):
            finish_pending_events_sync()
