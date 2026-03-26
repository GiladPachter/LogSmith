import pytest
import threading
from LogSmith.async_smartlogger import AsyncSmartLogger


# ------------------------------------------------------------
# 1. Basic get_record() call
# ------------------------------------------------------------
def test_get_record_basic():
    rec = AsyncSmartLogger.get_record()

    assert rec.timestamp is not None
    assert rec.file_path.endswith("test_async_smartlogger_get_record.py")
    assert rec.file_name == "test_async_smartlogger_get_record.py"
    assert rec.lineno is not None
    assert rec.func_name == "test_get_record_basic"
    assert rec.thread_id == threading.current_thread().ident
    assert rec.process_id > 0


# ------------------------------------------------------------
# 2. get_record() inside an exception block (exc_info=True)
# ------------------------------------------------------------
def test_get_record_exc_info():
    try:
        raise ValueError("boom")
    except Exception:
        rec = AsyncSmartLogger.get_record(exc_info=True)

    assert rec.exc_info is not None
    assert rec.exc_info["exc_parts"]["err_type_name"] == "ValueError"
    assert "boom" in rec.exc_info["exc_parts"]["error_text"]


# ------------------------------------------------------------
# 3. get_record() with stack_info=True
# ------------------------------------------------------------
def test_get_record_stack_info():
    rec = AsyncSmartLogger.get_record(stack_info=True)
    assert rec.stack_info is not None
    assert "test_get_record_stack_info" in rec.stack_info


# ------------------------------------------------------------
# 4. get_record() from nested functions (tests caller resolution)
# ------------------------------------------------------------
def test_get_record_nested():
    def inner():
        return AsyncSmartLogger.get_record()

    rec = inner()
    assert rec.func_name == "inner"
    assert rec.file_name == "test_async_smartlogger_get_record.py"


# ------------------------------------------------------------
# 5. get_record() inside an async task (tests task_name)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_record_async_task():
    async def worker():
        return AsyncSmartLogger.get_record()

    rec = await worker()
    assert rec.task_name is not None
    assert "worker" in rec.task_name or rec.task_name.startswith("Task-")


# ------------------------------------------------------------
# 6. get_record() inside a thread (tests thread_name/id)
# ------------------------------------------------------------
def test_get_record_thread():
    result = {}

    def run():
        result["rec"] = AsyncSmartLogger.get_record()

    t = threading.Thread(target=run, name="TestThread")
    t.start()
    t.join()

    rec = result["rec"]
    assert rec.thread_name == "TestThread"
    assert rec.thread_id is not None
