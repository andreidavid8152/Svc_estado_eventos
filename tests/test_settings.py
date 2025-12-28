import os
import unittest

os.environ.setdefault("BACKEND_URL", "http://backend.test")

from settings import Settings  # noqa: E402


class SettingsTests(unittest.TestCase):
    def test_defaults_and_env_values(self):
        config = Settings(BACKEND_URL="http://override.test")

        self.assertEqual(config.BACKEND_URL, "http://override.test")
        self.assertEqual(config.SCHEDULER_INTERVAL_SECONDS, 60)
        self.assertEqual(config.SCHEDULER_MISFIRE_GRACE_SECONDS, 5)
        self.assertTrue(config.SCHEDULER_COALESCE)
        self.assertEqual(config.HOST, "0.0.0.0")
        self.assertEqual(config.PORT, 8001)
        self.assertEqual(config.HTTP_TIMEOUT, 30)
        self.assertEqual(config.LOG_LEVEL, "INFO")
