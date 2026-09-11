"""Check the LLM queue bounds concurrency and sheds load instead of piling up.

Run: python -m tests.test_llm_queue
"""

import os
import threading
import time

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("LLM_CONCURRENCY", "3")
os.environ.setdefault("LLM_QUEUE_TIMEOUT", "1")

from fastapi import HTTPException  # noqa: E402

from app.core import llm  # noqa: E402


def test_concurrency_is_capped():
    """No more than LLM_CONCURRENCY callers hold a slot at the same time."""
    inside = 0
    peak = 0
    lock = threading.Lock()

    def worker():
        nonlocal inside, peak
        with llm.llm_slot():
            with lock:
                inside += 1
                peak = max(peak, inside)
            time.sleep(0.2)
            with lock:
                inside -= 1

    threads = [threading.Thread(target=worker) for _ in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert peak <= llm.LLM_CONCURRENCY, f"{peak} callers were inside at once"
    assert inside == 0


def test_full_queue_sheds_with_503():
    """A caller that cannot get a slot in time gets 503, not an endless wait."""
    release = threading.Event()

    def hog():
        with llm.llm_slot():
            release.wait(5)

    hogs = [threading.Thread(target=hog) for _ in range(llm.LLM_CONCURRENCY)]
    for t in hogs:
        t.start()
    time.sleep(0.2)  # let them all take a slot

    started = time.monotonic()
    try:
        with llm.llm_slot():
            raise AssertionError("expected the queue to shed this caller")
    except HTTPException as e:
        waited = time.monotonic() - started
        assert e.status_code == 503, e.status_code
        assert e.headers.get("Retry-After") == "5"
        assert waited < llm.LLM_QUEUE_TIMEOUT + 1, f"waited {waited:.1f}s"

    release.set()
    for t in hogs:
        t.join()


def test_slot_is_released_when_the_call_raises():
    """A failing OpenAI call must not leak its slot."""
    for _ in range(llm.LLM_CONCURRENCY + 2):
        try:
            with llm.llm_slot():
                raise RuntimeError("boom")
        except RuntimeError:
            pass

    with llm.llm_slot():  # would block and raise 503 if slots leaked
        pass


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("all passed")
