import os
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("BACKEND_URL", "http://backend.test")

from scheduler.jobs.cleanup_events import cleanup_expired_events  # noqa: E402


class CleanupExpiredEventsTests(unittest.IsolatedAsyncioTestCase):
    async def test_cleanup_expired_events_no_results(self):
        with patch("scheduler.jobs.cleanup_events.backend_client") as mock_client:
            mock_client.ensure_superadmin_token = AsyncMock(return_value=True)
            mock_client.get_expired_events = AsyncMock(return_value=[])

            await cleanup_expired_events()

            mock_client.ensure_superadmin_token.assert_awaited_once()
            mock_client.delete_event.assert_not_called()

    async def test_cleanup_expired_events_mixed_results(self):
        with patch("scheduler.jobs.cleanup_events.backend_client") as mock_client:
            mock_client.ensure_superadmin_token = AsyncMock(return_value=True)
            mock_client.get_expired_events = AsyncMock(
                return_value=[{"id": 1, "start_date": "2024-01-01"}, {"id": 2}]
            )
            mock_client.delete_event = AsyncMock(side_effect=[True, False])

            await cleanup_expired_events()

            mock_client.ensure_superadmin_token.assert_awaited_once()
            self.assertEqual(mock_client.delete_event.await_count, 2)
