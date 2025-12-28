import os
import unittest
from unittest import mock

os.environ.setdefault("BACKEND_URL", "http://backend.test")

from scheduler import bootstrap  # noqa: E402


class SchedulerBootstrapTests(unittest.TestCase):
    def setUp(self):
        bootstrap.scheduler = None

    def tearDown(self):
        bootstrap.scheduler = None

    def test_init_scheduler_adds_job_and_starts(self):
        fake_scheduler = mock.Mock()

        with mock.patch(
            "scheduler.bootstrap.BackgroundScheduler", return_value=fake_scheduler
        ):
            scheduler = bootstrap.init_scheduler()

        self.assertIs(scheduler, fake_scheduler)
        fake_scheduler.add_job.assert_called_once()
        fake_scheduler.start.assert_called_once()

        call_kwargs = fake_scheduler.add_job.call_args.kwargs
        self.assertEqual(call_kwargs.get("id"), "process_events")

    def test_init_scheduler_returns_existing_instance(self):
        fake_scheduler = mock.Mock()
        bootstrap.scheduler = fake_scheduler

        with mock.patch("scheduler.bootstrap.BackgroundScheduler") as mock_class:
            scheduler = bootstrap.init_scheduler()

        self.assertIs(scheduler, fake_scheduler)
        mock_class.assert_not_called()

    def test_shutdown_scheduler(self):
        fake_scheduler = mock.Mock()
        bootstrap.scheduler = fake_scheduler

        bootstrap.shutdown_scheduler()

        fake_scheduler.shutdown.assert_called_once()
        self.assertIsNone(bootstrap.scheduler)

    def test_shutdown_scheduler_without_instance(self):
        bootstrap.scheduler = None
        bootstrap.shutdown_scheduler()
        self.assertIsNone(bootstrap.scheduler)

    def test_get_scheduler_returns_current_instance(self):
        fake_scheduler = mock.Mock()
        bootstrap.scheduler = fake_scheduler

        self.assertIs(bootstrap.get_scheduler(), fake_scheduler)
