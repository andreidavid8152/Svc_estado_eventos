import json
import os
import unittest
from unittest import mock

import httpx
import logging

os.environ.setdefault("BACKEND_URL", "http://backend.test")
os.environ.setdefault("BACKEND_SUPERADMIN_EMAIL", "superadmin@example.com")
os.environ.setdefault("BACKEND_SUPERADMIN_PASSWORD", "superadmin")

from scheduler.jobs.process_events import process_events  # noqa: E402
from clients.backend_api import backend_client  # noqa: E402


BASE_URL = "http://backend.test"
ORIGINAL_ASYNC_CLIENT = httpx.AsyncClient


class RecordingHandler:
    def __init__(self, pending_start, pending_finish, finish_success=True):
        self.pending_start = pending_start
        self.pending_finish = pending_finish
        self.finish_success = finish_success
        self.calls = []

    def __call__(self, request):
        self.calls.append((request.method, request.url.path, request.content))
        path = request.url.path

        if request.method == "GET" and path.endswith("/pending-start/"):
            return httpx.Response(
                200, json={"results": self.pending_start}, request=request
            )

        if request.method == "GET" and path.endswith("/pending-finish/"):
            return httpx.Response(
                200, json={"results": self.pending_finish}, request=request
            )

        if request.method == "POST" and path.endswith("/start/"):
            return httpx.Response(
                200, json={"success": True, "status": "en_progreso"}, request=request
            )

        if request.method == "POST" and path.endswith("/finish/"):
            return httpx.Response(
                200,
                json={"success": self.finish_success, "status": "completado"},
                request=request,
            )

        if request.method == "POST" and path.endswith(
            "/analysis/process-event-completion/"
        ):
            payload = json.loads(request.content.decode("utf-8") or "{}")
            return httpx.Response(
                200,
                json={"message": "ok", "event_id": payload.get("event_id")},
                request=request,
            )

        if request.method == "POST" and path.endswith("/auth/login/"):
            return httpx.Response(
                200, json={"token": "test-token"}, request=request
            )

        if request.method == "POST" and path.endswith(
            "/events/api/monitoring/cleanup-stale-logs/"
        ):
            return httpx.Response(
                200, json={"success": True, "stale_count": 0}, request=request
            )

        return httpx.Response(404, json={"error": "not found"}, request=request)


def build_async_client(transport):
    def _factory(*args, **kwargs):
        mock_transport = httpx.MockTransport(transport)
        return ORIGINAL_ASYNC_CLIENT(
            transport=mock_transport,
            base_url=BASE_URL,
            timeout=kwargs.get("timeout"),
        )

    return _factory


class ProcessEventsIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        backend_client._token = ""

    def tearDown(self):
        logging.disable(logging.NOTSET)

    async def test_process_events_full_flow(self):
        handler = RecordingHandler(
            pending_start=[
                {"id": 101, "start_date": "2025-01-01T00:00:00"},
                {"id": 102, "start_date": "2025-01-01T00:10:00"},
            ],
            pending_finish=[{"id": 201, "end_date": "2025-01-01T01:00:00"}],
            finish_success=True,
        )
        async_client_factory = build_async_client(handler)

        with mock.patch(
            "clients.backend_api.httpx.AsyncClient", new=async_client_factory
        ):
            await process_events()

        paths = [call[1] for call in handler.calls]
        expected_paths = [
            "/events/api/events-status/pending-start/",
            "/events/api/events-status/101/start/",
            "/events/api/events-status/102/start/",
            "/events/api/events-status/pending-finish/",
            "/events/api/events-status/201/finish/",
            "/analysis/process-event-completion/",
            "/auth/login/",
            "/events/api/monitoring/cleanup-stale-logs/",
        ]
        self.assertEqual(paths, expected_paths)

        completion_calls = [
            call for call in handler.calls
            if call[1] == "/analysis/process-event-completion/"
        ]
        self.assertEqual(len(completion_calls), 1)
        completion_payload = json.loads(completion_calls[0][2].decode("utf-8") or "{}")
        self.assertEqual(completion_payload.get("event_id"), 201)

    async def test_process_events_finish_failure_skips_processing(self):
        handler = RecordingHandler(
            pending_start=[],
            pending_finish=[{"id": 301, "end_date": "2025-01-01T02:00:00"}],
            finish_success=False,
        )
        async_client_factory = build_async_client(handler)

        with mock.patch(
            "clients.backend_api.httpx.AsyncClient", new=async_client_factory
        ):
            await process_events()

        paths = [call[1] for call in handler.calls]
        self.assertIn("/events/api/events-status/pending-start/", paths)
        self.assertIn("/events/api/events-status/pending-finish/", paths)
        self.assertIn("/events/api/events-status/301/finish/", paths)
        self.assertNotIn("/analysis/process-event-completion/", paths)
