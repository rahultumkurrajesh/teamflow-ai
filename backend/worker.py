"""Background worker entrypoint.

This script starts the RQ worker process. It should be run in a separate
container or process from the API. The worker listens to the Redis queue
and processes jobs as they are enqueued.

Usage:
    python worker.py

The worker can be configured with environment variables:
    - REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
    - RQ_WORKER_NAME: Name for this worker (optional, auto-generated if omitted)
"""
import logging
import sys

from rq import Queue, Worker
from redis import Redis

from app.core.config import get_settings

# Configure logging so we can see what the worker is doing
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the RQ worker."""
    settings = get_settings()
    logger.info(f"Starting worker, connecting to {settings.redis_url}")

    try:
        redis_conn = Redis.from_url(settings.redis_url, decode_responses=True)
        # Test the connection
        redis_conn.ping()
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)

    # Create queue and worker
    queue = Queue(connection=redis_conn)
    worker = Worker([queue], connection=redis_conn)

    logger.info("Worker starting, waiting for jobs...")
    try:
        worker.work()
    except KeyboardInterrupt:
        logger.info("Worker interrupted, shutting down")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Worker encountered an error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
