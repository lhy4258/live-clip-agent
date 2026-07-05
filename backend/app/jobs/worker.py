from __future__ import annotations

import argparse
from collections.abc import Sequence

from redis import Redis
from rq import SimpleWorker

from app.core.config import get_settings
from app.jobs.queues import VIDEO_OPS_QUEUE


def parse_queue_names(raw_queues: str | None) -> list[str]:
    if raw_queues is None:
        return [VIDEO_OPS_QUEUE]

    queue_names = [queue_name.strip() for queue_name in raw_queues.split(",") if queue_name.strip()]
    return queue_names or [VIDEO_OPS_QUEUE]


def build_worker(redis_url: str, queue_names: Sequence[str]) -> SimpleWorker:
    redis_conn = Redis.from_url(redis_url)
    return SimpleWorker(list(queue_names), connection=redis_conn)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the live stream clip agent RQ worker.")
    parser.add_argument(
        "--queues",
        default=VIDEO_OPS_QUEUE,
        help="Comma-separated RQ queue names. Default: video_ops.",
    )
    parser.add_argument(
        "--burst",
        action="store_true",
        help="Process currently queued jobs and exit.",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    worker = build_worker(settings.redis_url, parse_queue_names(args.queues))
    worker.work(burst=args.burst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
