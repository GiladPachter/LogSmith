import asyncio
import logging
import threading

import pytest
from LogSmith.async_smartlogger import AsyncSmartLogger, AsyncOp, _QueueItem
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import RotationLogic


# ------------------------------------------------------------
# 1. Worker stops on SENTINEL
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_worker_stops_on_sentinel():
    lg = AsyncSmartLogger("sentinel_test")

    # Push sentinel directly
    lg._AsyncSmartLogger__queue.put_nowait(
        _QueueItem(op=AsyncOp.SENTINEL, payload={})
    )

    await asyncio.sleep(0)  # allow worker to process

    # At least one worker task should be done
    assert any(t.done() for t in lg._AsyncSmartLogger__worker_tasks)

    lg.destroy()


# ------------------------------------------------------------
# 2. Worker swallows handler exceptions
# ------------------------------------------------------------
class ExplodingHandler(logging.Handler):
    def emit(self, record):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_worker_swallows_handler_exceptions():
    lg = AsyncSmartLogger("explode_test")
    lg._AsyncSmartLogger__py_logger.addHandler(ExplodingHandler())

    # Should not raise
    await lg.a_info("hello")
    await asyncio.sleep(0)

    # Worker must still be alive
    assert all(not t.done() for t in lg._AsyncSmartLogger__worker_tasks)

    lg.destroy()


# ------------------------------------------------------------
# 3. Deferred worker creation
# ------------------------------------------------------------
def test_deferred_worker_creation():
    lg = AsyncSmartLogger("deferred_test")  # created outside event loop
    assert lg._AsyncSmartLogger__worker_tasks is None

    async def use_logger():
        await lg.a_info("hello")
        assert lg._AsyncSmartLogger__worker_tasks is not None

    asyncio.run(use_logger())

    lg.destroy()


# ------------------------------------------------------------
# 4. RAW stream reopening
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_raw_reopens_file(tmp_path):
    lg = AsyncSmartLogger("raw_test")
    lg.add_file(str(tmp_path), "raw.log")

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]
    handler.stream = None  # simulate missing stream

    await lg.a_raw("hello")
    await lg.flush()

    text = (tmp_path / "raw.log").read_text()
    assert "hello" in text

    lg.destroy()


# ------------------------------------------------------------
# 5. Rotation callback path
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_callback(tmp_path):
    logic = RotationLogic(maxBytes=20, backupCount=2)
    lg = AsyncSmartLogger("rotate_test")
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]
    assert isinstance(handler, Async_TimedSizedRotatingFileHandler)

    # Force rotation
    handler.rotation_callback(handler)
    await asyncio.sleep(0)
    await lg.flush()

    rotated = list(tmp_path.glob("rot.log.*"))
    assert len(rotated) >= 1

    lg.destroy()


# ------------------------------------------------------------
# 6. Profiling branches
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_profiling_paths(tmp_path):
    lg = AsyncSmartLogger("profile_test")
    lg.enable_profiling(True)
    lg.add_file(str(tmp_path), "prof.log")

    await lg.a_info("hello")
    await lg.flush()

    text = lg.get_profiling_details()
    assert "Avg total per log" in text

    lg.destroy()


@pytest.mark.asyncio
async def test_profiling_no_data():
    lg = AsyncSmartLogger("profile_empty")
    lg.enable_profiling(True)

    text = lg.get_profiling_details()
    assert text == "No profiling data collected."

    lg.destroy()


# ------------------------------------------------------------
# 7. QueueFull backpressure path
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_full_backpressure(monkeypatch):
    lg = AsyncSmartLogger("queuefull")

    # Force put_nowait to raise QueueFull
    def boom(*args, **kwargs):
        raise asyncio.QueueFull

    monkeypatch.setattr(lg._AsyncSmartLogger__queue, "put_nowait", boom)

    # Should not raise
    await lg.a_info("hello")

    lg.destroy()


def test_ancestor_missing():
    with pytest.raises(RuntimeError):
        AsyncSmartLogger("a.b.c")  # "a" does not exist


def test_name_collision():
    lg = AsyncSmartLogger("dup")
    with pytest.raises(RuntimeError):
        AsyncSmartLogger("dup")


@pytest.mark.asyncio
async def test_queuefull_retry(monkeypatch):
    lg = AsyncSmartLogger("qfull")
    lg.add_console()

    calls = {"n": 0}

    def full(item):
        calls["n"] += 1
        raise asyncio.QueueFull

    monkeypatch.setattr(lg._AsyncSmartLogger__queue, "put_nowait", full)

    await lg.a_info("hello")

    assert calls["n"] >= 3

    lg.destroy()


@pytest.mark.asyncio
async def test_raw_write_fallback(tmp_path):
    lg = AsyncSmartLogger("raw")
    lg.add_file(str(tmp_path), "x.log")

    # Force stream to None to trigger reopen
    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]
    handler.stream = None

    await lg.a_raw("hello")
    await lg.flush()

    assert "hello" in (tmp_path / "x.log").read_text()

    lg.destroy()


@pytest.mark.asyncio
async def test_dynamic_level():
    AsyncSmartLogger.register_level("ALERT", 45)
    lg = AsyncSmartLogger("dyn")
    lg.add_console()

    await lg.a_alert("boom")  # dynamic method

    await lg.destroy()


def test_get_record_fallback():
    rec = AsyncSmartLogger.get_record()
    assert rec.timestamp is not None


def test_retire():
    lg = AsyncSmartLogger("ret")
    lg.retire()
    with pytest.raises(RuntimeError):
        lg.add_console()

    lg.destroy()


@pytest.mark.asyncio
async def test_destroy():
    lg = AsyncSmartLogger("dest")
    lg.add_console()
    await lg.destroy()
    assert lg.name not in logging.Logger.manager.loggerDict

    lg.destroy()


def test_theme_application():
    from LogSmith.levels import LevelStyle
    style = LevelStyle()
    AsyncSmartLogger.apply_color_theme({logging.INFO: style})


@pytest.mark.asyncio
async def test_audit_ndjson(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.ndjson",
        NDJSON_output=True,
    )

    lg = AsyncSmartLogger("aud")
    lg.add_console()
    await lg.a_info("hello")

    await lg.flush()

    await AsyncSmartLogger.terminate_auditing()

    text = (tmp_path / "audit.ndjson").read_text(encoding="utf-8")
    assert text.strip().startswith("[")
    assert text.strip().split(':')[1].lstrip().startswith("{")

    lg.destroy()


# ------------------------------------------------------------
# 8. Audit forwarding edge case
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_logger_does_not_audit_itself(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    audit_logger = AsyncSmartLogger._AsyncSmartLogger__audit_logger

    # Log from audit logger itself
    await audit_logger.a_info("self-test")
    await audit_logger.flush()

    text = (tmp_path / "audit.log").read_text()
    # Should contain only one prefix, not recursive
    assert text.count("[_async_audit]:") == 1

    audit_logger.destroy()


def test_check_ancestors_no_dot():
    # Should simply return without error
    AsyncSmartLogger._AsyncSmartLogger__check_ancestors("root")


def test_on_queue_put_no_loop(monkeypatch):
    lg = AsyncSmartLogger("no_loop_test")

    # Force no loop
    lg._AsyncSmartLogger__loop = None

    item = _QueueItem(AsyncOp.LOG, {"level": 20})
    lg._on_queue_put(item)

    # Worker should not start
    assert lg._AsyncSmartLogger__worker_tasks is None

    lg.destroy()


def test_rotation_callback_same_thread_placeholder(tmp_path):
    lg = AsyncSmartLogger("rot_same")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "x.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    # Force worker_tasks = None to trigger placeholder []
    lg._AsyncSmartLogger__worker_tasks = None

    handler.rotation_callback(handler)

    assert lg._AsyncSmartLogger__worker_tasks == []

    lg.destroy()


def test_rotation_queuefull_retry(monkeypatch, tmp_path):
    lg = AsyncSmartLogger("rot_qfull")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "x.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    def full(*args, **kwargs):
        raise asyncio.QueueFull

    monkeypatch.setattr(lg._AsyncSmartLogger__queue, "put_nowait", full)

    handler.rotation_callback(handler)  # Should not crash

    lg.destroy()


@pytest.mark.asyncio
async def test_raw_write_error(tmp_path, monkeypatch):
    lg = AsyncSmartLogger("raw_err")
    lg.add_file(str(tmp_path), "x.log")

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    def bad_write(*args, **kwargs):
        raise Exception("fail")

    monkeypatch.setattr(handler.stream, "write", bad_write)

    await lg.a_raw("hello")  # Should not crash

    lg.destroy()


def test_audit_prefix():
    out = AsyncSmartLogger._AsyncSmartLogger__audit_prefix("msg", "logger")
    assert out.startswith("logger :")


def test_dynamic_level_method_creation():
    AsyncSmartLogger.register_level("NOTICE", 25)
    lg = AsyncSmartLogger("dyn2")
    assert callable(lg.a_notice)

    lg.destroy()


@pytest.mark.asyncio
async def test_stack_info(tmp_path):
    lg = AsyncSmartLogger("stack")
    lg.add_console()

    await lg.a_info("hello", stack_info=True)
    await lg.flush()

    await lg.destroy()


@pytest.mark.asyncio
async def test_audit_metadata(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    meta = AsyncSmartLogger.audit_handler_info()
    assert meta["kind"] in ("file", "console")

    await AsyncSmartLogger.terminate_auditing()


@pytest.mark.asyncio
async def test_shutdown_no_worker():
    lg = AsyncSmartLogger("shutdown_noworker")
    lg._AsyncSmartLogger__worker_tasks = None
    await lg.shutdown()

    lg.destroy()


def test_retire_destroy():
    lg = AsyncSmartLogger("ret_dest")
    lg.retire()
    lg.destroy()


@pytest.mark.asyncio
async def test_theme_validation_errors():
    with pytest.raises(TypeError):
        await AsyncSmartLogger.apply_color_theme("bad")

    with pytest.raises(TypeError):
        await AsyncSmartLogger.apply_color_theme({ "x": 123 })


@pytest.mark.asyncio
async def test_async_logger_basic_usage():
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("test")

    # Attach a dummy handler so logging has somewhere to go
    import io, logging
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    lg._AsyncSmartLogger__py_logger.addHandler(handler)

    # Basic async logging should not raise
    await lg.a_info("hello")

    # Ensure the worker processes the queue
    await lg.flush()

    assert "hello" in stream.getvalue()

    lg.destroy()


# ============================================================
# async_smartlogger.py delta tests
# ============================================================

@pytest.mark.asyncio
async def test_async_logger_queue_full_retry():
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("delta_queue")

    await lg.a_info("one")
    await lg.a_info("two")  # triggers retry
    await lg.flush()

    lg.destroy()


@pytest.mark.asyncio
async def test_async_logger_external_thread_enqueue():
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("delta_thread")

    async def warmup():
        await lg.a_info("warm")

    await warmup()

    def worker():
        asyncio.run(lg.a_info("from-thread"))

    t = threading.Thread(target=worker)
    t.start()
    t.join()

    await lg.flush()

    lg.destroy()


@pytest.mark.asyncio
async def test_async_logger_retire_edge():
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("delta_retire")
    await lg.a_info("before")
    await lg.flush()

    lg.retire()

    with pytest.raises(RuntimeError):
        await lg.a_info("after")

    lg.destroy()


@pytest.mark.asyncio
async def test_async_logger_destroy_edge():
    from LogSmith.async_smartlogger import AsyncSmartLogger
    import logging

    lg = AsyncSmartLogger("delta_destroy")
    await lg.a_info("x")
    await lg.flush()

    lg.destroy()

    assert "delta.destroy" not in logging.Logger.manager.loggerDict


@pytest.mark.asyncio
async def test_async_logger_stdout_fallback(capsys):
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("delta_stdout")
    await lg.a_stdout("hello", "world", sep="-", end="!")

    captured = capsys.readouterr().out
    assert captured == "hello-world!"

    lg.destroy()


@pytest.mark.asyncio
async def test_async_logger_rotation_debounce(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger, RotationLogic

    lg = AsyncSmartLogger("delta_rotate")
    lg.add_file(str(tmp_path), "r.log", rotation_logic=RotationLogic(maxBytes=1))

    await lg.a_info("x")
    await lg.a_info("y")  # second rotation request should debounce
    await lg.flush()


import asyncio
import pytest
from LogSmith.async_smartlogger import AsyncSmartLogger


@pytest.mark.asyncio
async def test_asyncsmartlogger_profiling_short_stress():
    # Ensure clean state
    await AsyncSmartLogger.terminate_auditing()

    lg = AsyncSmartLogger("async_profile_test")
    lg.enable_profiling(enable = True)

    async def spammer():
        end = asyncio.get_event_loop().time() + 1.0  # run ~1 second
        while asyncio.get_event_loop().time() < end:
            await lg.a_info("profiling test message")
            # tiny sleep to avoid overwhelming event loop
            await asyncio.sleep(0)

    # Run a few concurrent spammers
    await asyncio.gather(
        spammer(),
        spammer(),
        spammer(),
    )

    # Flush all pending logs
    await lg.flush()

    # Grab profiling stats
    profiling_details = lg.get_profiling_details()

    await lg.a_stdout(profiling_details)

    lg.enable_profiling(False)

    # Clean shutdown
    await lg.shutdown()
    lg.destroy()
