import types
import unittest
from unittest.mock import Mock, patch

from app.jobs.queues import VIDEO_OPS_QUEUE
from app.jobs.worker import build_worker, main, parse_queue_names


class RqWorkerTest(unittest.TestCase):
    def test_parse_queue_names_defaults_to_video_ops(self):
        self.assertEqual(parse_queue_names(None), [VIDEO_OPS_QUEUE])
        self.assertEqual(parse_queue_names(""), [VIDEO_OPS_QUEUE])
        self.assertEqual(parse_queue_names("  "), [VIDEO_OPS_QUEUE])

    def test_parse_queue_names_accepts_comma_separated_names(self):
        self.assertEqual(parse_queue_names("video_ops,high_priority"), ["video_ops", "high_priority"])
        self.assertEqual(parse_queue_names(" video_ops , high_priority "), ["video_ops", "high_priority"])

    def test_build_worker_uses_redis_url_and_queue_names(self):
        redis_conn = object()
        worker = object()

        with (
            patch("app.jobs.worker.Redis.from_url", return_value=redis_conn) as from_url,
            patch("app.jobs.worker.SimpleWorker", return_value=worker) as worker_cls,
        ):
            result = build_worker("redis://localhost:6379/0", ["video_ops"])

        self.assertIs(result, worker)
        from_url.assert_called_once_with("redis://localhost:6379/0")
        worker_cls.assert_called_once_with(["video_ops"], connection=redis_conn)

    def test_main_runs_worker_with_requested_queues(self):
        worker = Mock()
        settings = types.SimpleNamespace(redis_url="redis://localhost:6379/0")

        with (
            patch("app.jobs.worker.get_settings", return_value=settings),
            patch("app.jobs.worker.build_worker", return_value=worker) as builder,
        ):
            exit_code = main(["--queues", "video_ops,high_priority", "--burst"])

        self.assertEqual(exit_code, 0)
        builder.assert_called_once_with("redis://localhost:6379/0", ["video_ops", "high_priority"])
        worker.work.assert_called_once_with(burst=True)


if __name__ == "__main__":
    unittest.main()
