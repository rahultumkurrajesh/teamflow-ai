"""Redis queue and job configuration.

RQ (Redis Queue) provides a simple, lightweight job queue backed by Redis.
Jobs are enqueued from the API layer and processed by a separate worker
process. This keeps the API responsive and moves heavy lifting offline.

The queue connection is initialized once and reused across the app.
"""
from redis import Redis
from rq import Queue

from app.core.config import get_settings

settings = get_settings()

# Redis connection: configured via REDIS_URL env var or default
redis_conn = Redis.from_url(settings.redis_url, decode_responses=True)

# Default queue for all background jobs
queue = Queue(connection=redis_conn)


def enqueue_job(func, *args, **kwargs):
    """Enqueue a job to the default queue.

    Args:
        func: The function to call when the job is processed.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The RQ Job object (includes job.id for tracking).
    """
    return queue.enqueue(func, *args, **kwargs)
