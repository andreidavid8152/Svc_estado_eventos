import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

os.environ.setdefault("BACKEND_URL", "http://backend.test")

import main  # noqa: E402


class MainAppTests(unittest.TestCase):
    def test_root_and_health_endpoints(self):
        with mock.patch("main.init_scheduler") as init_scheduler, mock.patch(
            "main.shutdown_scheduler"
        ) as shutdown_scheduler:
            with TestClient(main.app) as client:
                response = client.get("/")
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data.get("status"), "running")
                self.assertIn("scheduler_interval_seconds", data)

                health_response = client.get("/health")
                self.assertEqual(health_response.status_code, 200)
                self.assertEqual(health_response.json(), {"status": "ok"})

            init_scheduler.assert_called_once()
            shutdown_scheduler.assert_called_once()
