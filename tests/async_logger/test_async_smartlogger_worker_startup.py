# tests/async/test_async_smartlogger_worker_startup.py
import asyncio
import pytest
from LogSmith.async_smartlogger import AsyncSmartLogger


def test_logger_created_outside_loop():
    lg = AsyncSmartLogger("lazy")
    # No loop yet
    assert lg._AsyncSmartLogger__loop is None
    assert lg._AsyncSmartLogger__worker_tasks is None  # placeholder list


@pytest.mark.asyncio
async def test_worker_starts_on_first_log(tmp_path):
    lg = AsyncSmartLogger("lazy2")

    # Because we are inside an event loop, loop must NOT be None
    assert lg._AsyncSmartLogger__loop is asyncio.get_running_loop()
    assert lg._AsyncSmartLogger__worker_tasks is not None

    # Now verify worker actually processes logs
    lg.add_file(str(tmp_path), "x.log")
    await lg.a_info("hello")
    await lg.flush()

    assert (tmp_path / "x.log").read_text().strip().endswith("hello")


@pytest.mark.asyncio
async def test_ensure_worker_started(tmp_path):
    lg = AsyncSmartLogger("lazy3")

    # Force worker_tasks to None to hit the branch
    lg._AsyncSmartLogger__worker_tasks = None

    await lg._AsyncSmartLogger__ensure_worker_started()

    assert lg._AsyncSmartLogger__loop is asyncio.get_running_loop()
    assert lg._AsyncSmartLogger__worker_tasks is not None
