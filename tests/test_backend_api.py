import os
import unittest
from unittest import mock

import httpx

os.environ.setdefault("BACKEND_URL", "http://backend.test")

from clients.backend_api import BackendAPIClient  # noqa: E402


def make_http_error(status_code=500, json_data=None):
    request = httpx.Request("GET", "http://backend.test")
    response = httpx.Response(status_code, json=json_data or {}, request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


class StubResponse:
    def __init__(self, status_code=200, json_data=None, http_error=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.http_error = http_error

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.http_error is not None:
            raise self.http_error
        if self.status_code >= 400:
            raise httpx.HTTPError("error")


class StubAsyncClient:
    def __init__(self, response, get_exc=None, post_exc=None):
        self.response = response
        self.get_calls = []
        self.post_calls = []
        self.get_exc = get_exc
        self.post_exc = post_exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, headers=None):
        if self.get_exc is not None:
            raise self.get_exc
        self.get_calls.append((url, headers))
        return self.response

    async def post(self, url, headers=None, json=None):
        if self.post_exc is not None:
            raise self.post_exc
        self.post_calls.append((url, headers, json))
        return self.response


class BackendAPIClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_pending_start_events_success(self):
        client = BackendAPIClient()
        response = StubResponse(
            status_code=200, json_data={"results": [{"id": 1}]}
        )
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.get_pending_start_events()

        self.assertEqual(result, [{"id": 1}])
        self.assertTrue(stub_client.get_calls)

    async def test_get_pending_start_events_http_error(self):
        client = BackendAPIClient()
        response = StubResponse(status_code=500, json_data={})
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.get_pending_start_events()

        self.assertEqual(result, [])

    async def test_get_pending_finish_events_success(self):
        client = BackendAPIClient()
        response = StubResponse(
            status_code=200, json_data={"results": [{"id": 2}]}
        )
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.get_pending_finish_events()

        self.assertEqual(result, [{"id": 2}])
        self.assertTrue(stub_client.get_calls)

    async def test_get_pending_finish_events_exception(self):
        client = BackendAPIClient()
        response = StubResponse(status_code=200, json_data={})
        stub_client = StubAsyncClient(response, get_exc=RuntimeError("boom"))

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.get_pending_finish_events()

        self.assertEqual(result, [])

    async def test_start_event_success(self):
        client = BackendAPIClient()
        response = StubResponse(status_code=200, json_data={"success": True})
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.start_event(10)

        self.assertTrue(result)
        self.assertTrue(stub_client.post_calls)

    async def test_start_event_failure_no_success(self):
        client = BackendAPIClient()
        response = StubResponse(status_code=200, json_data={"success": False})
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.start_event(99)

        self.assertFalse(result)

    async def test_start_event_http_error_with_response(self):
        client = BackendAPIClient()
        http_error = make_http_error(status_code=500, json_data={"error": "bad"})
        response = StubResponse(status_code=500, json_data={"error": "bad"}, http_error=http_error)
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.start_event(11)

        self.assertFalse(result)

    async def test_finish_event_success(self):
        client = BackendAPIClient()
        response = StubResponse(status_code=200, json_data={"success": True})
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.finish_event(12)

        self.assertTrue(result)

    async def test_finish_event_failure(self):
        client = BackendAPIClient()
        response = StubResponse(status_code=200, json_data={"success": False})
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.finish_event(10)

        self.assertFalse(result)

    async def test_process_event_completion_success_with_failures(self):
        client = BackendAPIClient()
        response = StubResponse(
            status_code=200,
            json_data={
                "message": "ok",
                "total_participants": 2,
                "successful": 1,
                "failed": 1,
                "results": [
                    {"success": False, "participant_name": "P1", "error": "boom"}
                ],
            },
        )
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.process_event_completion(55)

        self.assertTrue(result)
        self.assertTrue(stub_client.post_calls)

    async def test_process_event_completion_missing_message(self):
        client = BackendAPIClient()
        response = StubResponse(status_code=200, json_data={"detail": "no message"})
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.process_event_completion(56)

        self.assertFalse(result)

    async def test_process_event_completion_http_error(self):
        client = BackendAPIClient()
        http_error = make_http_error(status_code=500, json_data={"error": "fail"})
        response = StubResponse(status_code=500, json_data={"error": "fail"}, http_error=http_error)
        stub_client = StubAsyncClient(response)

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.process_event_completion(57)

        self.assertFalse(result)

    async def test_process_event_completion_exception(self):
        client = BackendAPIClient()
        response = StubResponse(status_code=200, json_data={"message": "ok"})
        stub_client = StubAsyncClient(response, post_exc=RuntimeError("boom"))

        with mock.patch("clients.backend_api.httpx.AsyncClient", return_value=stub_client):
            result = await client.process_event_completion(58)

        self.assertFalse(result)
