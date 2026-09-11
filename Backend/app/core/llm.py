"""Shared OpenAI client and the queue that fronts it.

Every request to /chat/next-question makes an OpenAI call that takes a second
or two. Left unbounded, a crowd puts every worker thread into a socket read at
once: the provider starts rate limiting us, and cheap requests (sign-in, status,
results) get no thread to run on because they are all parked on OpenAI.

So LLM calls get their own small pool of slots. Callers past that queue for a
slot, and if the queue does not clear in time they get 503 with Retry-After
rather than holding a worker thread indefinitely.
"""

import logging
import os
import threading
from contextlib import contextmanager

from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

# How many OpenAI calls may be in flight at once, out of THREADPOOL_SIZE
# workers. The rest stay free to serve requests that don't touch OpenAI.
LLM_CONCURRENCY = int(os.getenv("LLM_CONCURRENCY", "12"))
# How long a caller will wait for a slot before we shed the request.
LLM_QUEUE_TIMEOUT = float(os.getenv("LLM_QUEUE_TIMEOUT", "15"))
# Without this the SDK waits 10 minutes, so one stuck call costs a worker
# thread for 10 minutes.
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "20"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=LLM_TIMEOUT,
    max_retries=LLM_MAX_RETRIES,  # the SDK backs off and honours Retry-After
)

_slots = threading.BoundedSemaphore(LLM_CONCURRENCY)
_queue_depth = 0
_queue_lock = threading.Lock()


def queue_depth() -> int:
    """Callers currently waiting for a slot."""
    return _queue_depth


@contextmanager
def llm_slot():
    """Hold one of the LLM slots, or raise 503 if the queue does not clear.

    Only ever wrap a single leaf API call. Acquiring a slot while already
    holding one would deadlock the pool.
    """
    global _queue_depth

    with _queue_lock:
        _queue_depth += 1
    try:
        acquired = _slots.acquire(timeout=LLM_QUEUE_TIMEOUT)
    finally:
        with _queue_lock:
            _queue_depth -= 1

    if not acquired:
        logger.warning("LLM queue full, shedding request (depth=%s)", _queue_depth)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Server busy",
                "message": "We're handling a lot of people right now. Try again in a few seconds.",
                "retry_after": 5,
            },
            headers={"Retry-After": "5"},
        )

    try:
        yield
    finally:
        _slots.release()
