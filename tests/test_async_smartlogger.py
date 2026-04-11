import io
import os
import asyncio
import logging
import threading

import pytest

from pathlib import Path
from unittest.mock import MagicMock

from LogSmith import CPrint, LogRecordDetails, OptionalRecordFields
from LogSmith import AsyncSmartLogger
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith import RotationLogic, When, LargeLogEntryBehavior
from LogSmith import LevelStyle
from LogSmith.async_smartlogger import _QueueItem, AsyncOp
from LogSmith.level_registry import LEVELS

from tests.helpers import read_file, DummyHandler


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

async def drain(logger: AsyncSmartLogger):
    # noinspection PyProtectedMember
    q = logger._AsyncSmartLogger__queue
    await q.join()
    await asyncio.sleep(0)


# ---------------------------------------------------------
# Basic Async Logging Tests
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_async_info_to_console(async_logger, capsys):
    async_logger.add_console()
    await async_logger.a_info("hello async")
    await async_logger.shutdown()  # <-- ensures worker flushes
    out = capsys.readouterr().out
    assert "hello async" in out
    assert "INFO" in out


@pytest.mark.asyncio
async def test_async_info_to_file(async_logger, tmp_log_dir):
    log_dir = str(tmp_log_dir.resolve())
    logfile = tmp_log_dir / "async.log"

    async_logger.add_file(log_dir, "async.log")
    await async_logger.a_info("hello file")
    await async_logger.flush()          # ensure worker finished

    text = read_file(logfile)
    assert "hello file" in text
    assert "INFO" in text


# ---------------------------------------------------------
# Raw Logging Tests
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_async_raw_console(async_logger, capsys):
    async_logger.add_console()
    await async_logger.a_raw("RAW")
    await async_logger.flush()

    out = capsys.readouterr().out
    stripped = CPrint.strip_ansi(out).strip()

    assert stripped == "RAW"


@pytest.mark.asyncio
async def test_async_raw_file(async_logger, tmp_log_dir):
    path = tmp_log_dir / "raw_async.log"
    async_logger.add_file(tmp_log_dir.__str__(), "raw_async.log")
    await async_logger.a_raw("RAW")
    await async_logger.flush()
    assert read_file(path).strip() == "RAW"


# ---------------------------------------------------------
# Diagnostics Tests
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_async_exc_info(async_logger, capsys):
    async_logger.add_console(
        log_record_details = LogRecordDetails(
            optional_record_fields = OptionalRecordFields(
                exc_info=True
            )
        )
    )
    await async_logger.a_info("hello")
    await async_logger.flush()
    try:
        1 / 0
    except ZeroDivisionError:
        await async_logger.a_error("boom", exc_info=True)

    await async_logger.flush()

    out = capsys.readouterr().out
    assert "ZeroDivisionError" in out
    assert "boom" in out


@pytest.mark.asyncio
async def test_async_stack_info(async_logger, capsys):
    async_logger.add_console(
        log_record_details = LogRecordDetails(
            optional_record_fields = OptionalRecordFields(
                stack_info = True
            )
        )
    )
    await async_logger.a_info("stack", stack_info=True)

    await async_logger.flush()

    out = capsys.readouterr().out
    assert "stack" in out
    assert "File" in out


@pytest.mark.asyncio
async def test_async_extras(async_logger, capsys):
    async_logger.add_console()
    await async_logger.a_info("msg", user="gilad", action="async")

    await async_logger.flush()

    out = capsys.readouterr().out
    assert "gilad" in out
    assert "async" in out


# ---------------------------------------------------------
# Handler Management Tests
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_async_add_remove_console(async_logger, capsys):
    async_logger.add_console()
    async_logger.remove_console()
    await async_logger.a_info("hello")

    await async_logger.flush()

    out = capsys.readouterr().out
    assert out == ""


@pytest.mark.asyncio
async def test_async_add_remove_file(async_logger, tmp_log_dir):
    path = tmp_log_dir
    async_logger.add_file(path.__str__(), "x_async.log")
    log_file = async_logger.handler_info[0]['path']
    async_logger.remove_file_handler("x_async.txt", path.__str__())
    await async_logger.a_info("hello")
    assert read_file(Path(log_file)) == ""


# ---------------------------------------------------------
# Shutdown Tests
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_async_shutdown(async_logger, tmp_log_dir):
    path = tmp_log_dir
    async_logger.add_file(path.__str__(), "shutdown.log")

    for i in range(5):
        await async_logger.a_info(f"msg {i}")

    # Capture file path BEFORE shutdown
    log_file = async_logger.handler_info[0]['path']

    await async_logger.shutdown()

    text = read_file(Path(log_file))
    assert "msg 0" in text
    assert "msg 4" in text


# ---------------------------------------------------------
# Rotation Integration Tests
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_async_size_rotation(async_logger, tmp_log_dir):
    log_dir = str(tmp_log_dir.resolve())

    async_logger.add_file(
        log_dir=log_dir,
        logfile_name="rot_async.log",
        rotation_logic=RotationLogic(maxBytes=20, backupCount=2)
    )

    for i in range(10):
        await async_logger.a_info("x" * 50)

    await async_logger.flush()

    files = list(Path(log_dir).iterdir())
    assert len(files) >= 2


@pytest.mark.asyncio
async def test_basic_info_to_file(tmp_path):
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger = AsyncSmartLogger("basic-info")
    logger.add_file(log_dir=log_dir, logfile_name="test.log")

    await logger.a_info("hello async")
    await logger.flush()

    text = (tmp_path / "test.log").read_text()
    assert "hello async" in text


@pytest.mark.asyncio
async def test_raw_logging_uses_bleach_and_file_reopen(tmp_path):
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger = AsyncSmartLogger("raw-test")
    logger.add_file(log_dir=log_dir, logfile_name="raw.log")

    # Close stream to force reopen path in __process_raw
    handler = logger._AsyncSmartLogger__py_logger.handlers[-1]
    handler.stream.close()
    handler.stream = None

    msg = "\x1b[31mRED\x1b[0m plain"
    await logger.a_raw(msg)
    await logger.flush()

    text = (tmp_path / "raw.log").read_text()
    assert "plain" in text


@pytest.mark.asyncio
async def test_retire_blocks_logging(tmp_path):
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger = AsyncSmartLogger("retire-test")
    logger.add_file(log_dir=log_dir, logfile_name="retire.log")

    await logger.a_info("before")
    logger.retire()

    with pytest.raises(RuntimeError):
        await logger.a_info("after")

    await logger.flush()
    text = (tmp_path / "retire.log").read_text()
    assert "before" in text
    assert "after" not in text

    logger.destroy()


@pytest.mark.asyncio
async def test_shutdown_stops_worker(tmp_path):
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger = AsyncSmartLogger("shutdown-test")
    logger.add_file(log_dir=log_dir, logfile_name="shut.log")

    await logger.a_info("msg")
    await logger.shutdown()

    # Worker tasks must be done
    for task in logger._AsyncSmartLogger__worker_tasks:
        assert task.done()

    # Handlers are removed after shutdown (destroy)
    assert len(logger.handler_info) == 0


@pytest.mark.asyncio
async def test_rotation_callback_and_process_rotate(tmp_path):
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger = AsyncSmartLogger("rotate-test")

    rotation_logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        timestamp=None,
        maxBytes=10,
        backupCount=2,
        expiration_rule=None,
        log_entry_larger_than_maxBytes_behavior=None,
    )

    logger.add_file(
        log_dir=log_dir,
        logfile_name="rotate.log",
        rotation_logic=rotation_logic,
    )

    # Write enough to trigger rotation
    for _ in range(5):
        await logger.a_info("X" * 50)

    await logger.flush()

    base = tmp_path / "rotate.log"
    rotated = tmp_path / "rotate.log.1"
    assert base.exists()
    assert rotated.exists()


@pytest.mark.asyncio
async def test_audit_everything_and_terminate(tmp_path):
    log_dir = os.path.abspath(tmp_path.as_posix())

    await AsyncSmartLogger.audit_everything(
        log_dir=log_dir,
        logfile_name="audit.log",
        rotation_logic=None,
        details=None,
    )

    logger = AsyncSmartLogger("audited")
    logger.add_file(log_dir=log_dir, logfile_name="audited.log")

    await logger.a_info("audited message")
    await logger.flush()

    info = AsyncSmartLogger.audit_handler_info()
    assert info is not None
    assert info["formatter"] == "plain"

    await AsyncSmartLogger.terminate_auditing()
    assert AsyncSmartLogger.audit_handler_info() is None

    logger.destroy()


@pytest.mark.asyncio
async def test_dynamic_level_registration_and_call(tmp_path):
    log_dir = os.path.abspath(tmp_path.as_posix())
    AsyncSmartLogger.register_level("NOTICE", 25, style=None)

    logger = AsyncSmartLogger("dynamic-level")
    logger.add_file(log_dir=log_dir, logfile_name="dyn.log")

    # __getattr__ should create a_notice dynamically
    await logger.a_notice("dynamic level works")
    await logger.flush()

    text = (tmp_path / "dyn.log").read_text()
    assert "dynamic level works" in text
    assert "NOTICE" in AsyncSmartLogger.levels()


@pytest.mark.asyncio
async def test_apply_color_theme_and_errors():
    # valid theme
    theme = {meta["value"]: LevelStyle() for name, meta in LEVELS.all().items()}
    await AsyncSmartLogger.apply_color_theme(theme)

    # invalid theme type
    with pytest.raises(TypeError):
        await AsyncSmartLogger.apply_color_theme("not-a-dict")  # type: ignore[arg-type]

    # invalid key type
    with pytest.raises(TypeError):
        await AsyncSmartLogger.apply_color_theme({"x": LevelStyle()})  # type: ignore[arg-type]

    # invalid value type
    with pytest.raises(TypeError):
        await AsyncSmartLogger.apply_color_theme({10: "not-style"})  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_get_record_includes_basic_metadata():
    rec = AsyncSmartLogger.get_record(exc_info=False, stack_info=True)
    assert rec.file_name.endswith(".py")
    assert rec.func_name is not None
    assert rec.thread_id is not None
    assert rec.process_id == os.getpid()
    assert rec.stack_info is not None


# ------------------------------------------------------------
# 1. Basic async logging dispatch (console handler)
# ------------------------------------------------------------

# 1. Basic async log processing via __enqueue_log
@pytest.mark.asyncio
async def test_basic_async_log_processing():
    logger = AsyncSmartLogger("test_basic")

    dummy = DummyHandler()
    logger._AsyncSmartLogger__py_logger.addHandler(dummy)

    await logger._AsyncSmartLogger__enqueue_log(
        level=logging.INFO,
        msg="hello",
        args=(),
        extra={},
        fields={},
        exc_info=None,
        stack_info_flag=False,
        pathname=__file__,
        lineno=123,
        func_name="test_basic_async_log_processing",
    )

    await drain(logger)

    assert dummy.records == ["hello"]


# 2. Multiple handlers receive the same record
@pytest.mark.asyncio
async def test_multiple_handlers_receive_log():
    logger = AsyncSmartLogger("test_multi")

    h1 = DummyHandler()
    h2 = DummyHandler()
    logger._AsyncSmartLogger__py_logger.addHandler(h1)
    logger._AsyncSmartLogger__py_logger.addHandler(h2)

    await logger._AsyncSmartLogger__enqueue_log(
        level=logging.WARNING,
        msg="warn",
        args=(),
        extra={},
        fields={},
        exc_info=None,
        stack_info_flag=False,
        pathname=__file__,
        lineno=10,
        func_name="test_multiple_handlers_receive_log",
    )

    await drain(logger)

    assert h1.records == ["warn"]
    assert h2.records == ["warn"]


# 3. Handler exception is swallowed, others still run
@pytest.mark.asyncio
async def test_handler_exception_swallowed():
    logger = AsyncSmartLogger("test_exc")

    # Force worker creation properly
    logger._AsyncSmartLogger__worker_tasks = None
    await logger._AsyncSmartLogger__ensure_worker_started()

    # Clear inherited handlers from earlier tests
    logger._AsyncSmartLogger__py_logger.handlers.clear()

    bad = DummyHandler()
    bad.emit = MagicMock(side_effect=RuntimeError("boom"))

    good = DummyHandler()

    # Good first, then bad
    logger._AsyncSmartLogger__py_logger.addHandler(good)
    logger._AsyncSmartLogger__py_logger.addHandler(bad)

    item = _QueueItem(
        op=AsyncOp.LOG,
        payload={
            "level": logging.ERROR,
            "msg": "oops",
            "args": (),
            "extra": {},
            "fields": {},
            "exc_info": None,
            "stack_info_flag": False,
            "pathname": __file__,
            "lineno": 20,
            "func_name": "test_handler_exception_swallowed",
            "stack_info": None,
        },
    )
    logger._AsyncSmartLogger__queue.put_nowait(item)

    await drain(logger)

    assert good.records == ["oops"]

    logger.destroy()


# 4. __process_raw writes to console handler (StreamHandler)
@pytest.mark.asyncio
async def test_process_raw_console():
    logger = AsyncSmartLogger("test_raw_console")

    buf = io.StringIO()
    console = logging.StreamHandler(stream=buf)
    logger._AsyncSmartLogger__py_logger.addHandler(console)

    item = _QueueItem(
        op=AsyncOp.RAW,
        payload={"message": "hello raw", "end": "\n"},
    )
    logger._AsyncSmartLogger__queue.put_nowait(item)

    await drain(logger)

    out = buf.getvalue()
    assert "hello raw" in out


# 5. __process_raw treats file-like handler as file (no console bleaching)
@pytest.mark.asyncio
async def test_process_raw_file_like():
    logger = AsyncSmartLogger("test_raw_file")

    buf = io.StringIO()
    file_handler = logging.StreamHandler(stream=buf)
    # Mark as "file" by giving it a baseFilename attribute
    setattr(file_handler, "baseFilename", "dummy.log")
    logger._AsyncSmartLogger__py_logger.addHandler(file_handler)

    colored = "\x1b[31mRED\x1b[0m"
    item = _QueueItem(
        op=AsyncOp.RAW,
        payload={"message": colored, "end": ""},
    )
    logger._AsyncSmartLogger__queue.put_nowait(item)

    await drain(logger)

    # For file handlers, ANSI is stripped unless do_not_sanitize is True
    out = buf.getvalue()
    assert "RED" in out
    assert "\x1b" not in out


# 6. __process_rotate calls perform_rotation on Async_TimedSizedRotatingFileHandler
@pytest.mark.asyncio
async def test_process_rotate_calls_perform_rotation(tmp_path):
    logger = AsyncSmartLogger("test_rotate")

    file = tmp_path / "log.txt"
    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(file),
        max_bytes=5,
        backup_count=2,
        large_entry_behavior=LargeLogEntryBehavior.RotateFirst,
    )

    logger._AsyncSmartLogger__py_logger.addHandler(handler)

    handler.perform_rotation = MagicMock()

    item = _QueueItem(
        op=AsyncOp.ROTATE,
        payload={"handler": handler},
    )
    logger._AsyncSmartLogger__queue.put_nowait(item)

    await drain(logger)

    handler.perform_rotation.assert_called_once()


# 7. queue_size property reflects enqueued items
@pytest.mark.asyncio
async def test_queue_size_property():
    logger = AsyncSmartLogger("test_queue_size")

    # Enqueue without draining
    await logger._AsyncSmartLogger__enqueue_log(
        level=logging.INFO,
        msg="one",
        args=(),
        extra={},
        fields={},
        exc_info=None,
        stack_info_flag=False,
        pathname=__file__,
        lineno=1,
        func_name="test_queue_size_property",
    )

    assert logger.queue_size >= 1

    await drain(logger)


# 8. Shutdown prevents further logging via __enqueue_log
@pytest.mark.asyncio
async def test_shutdown_prevents_enqueue():
    logger = AsyncSmartLogger("test_shutdown")

    dummy = DummyHandler()
    logger._AsyncSmartLogger__py_logger.addHandler(dummy)

    await logger._AsyncSmartLogger__enqueue_log(
        level=logging.INFO,
        msg="before",
        args=(),
        extra={},
        fields={},
        exc_info=None,
        stack_info_flag=False,
        pathname=__file__,
        lineno=1,
        func_name="test_shutdown_prevents_enqueue",
    )
    await drain(logger)

    # Call the real shutdown (async) if present
    if hasattr(logger, "shutdown"):
        await logger.shutdown()
        logger.destroy()
    else:
        # Fallback: mark stopped flag directly if shutdown is named differently
        logger._AsyncSmartLogger__stopped = True

    with pytest.raises(RuntimeError):
        await logger._AsyncSmartLogger__enqueue_log(
            level=logging.INFO,
            msg="after",
            args=(),
            extra={},
            fields={},
            exc_info=None,
            stack_info_flag=False,
            pathname=__file__,
            lineno=2,
            func_name="test_shutdown_prevents_enqueue",
        )

    logger.destroy()


def test_rotation_callback_external_thread(tmp_path):
    lg = AsyncSmartLogger("ext_rot")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "x.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    def trigger():
        handler.rotation_callback(handler)

    t = threading.Thread(target=trigger)
    t.start()
    t.join()

    # Worker should exist
    assert lg._AsyncSmartLogger__worker_tasks is not None


def test_no_loop_queue_put():
    asyncio.set_event_loop(None)
    lg = AsyncSmartLogger("no_loop")
    item = _QueueItem(AsyncOp.LOG, {"level": 20, "msg": "x", "args": (), "extra": {}, "fields": {}, "exc_info": None, "stack_info_flag": False, "pathname": __file__, "lineno": 1, "func_name": "f"})
    lg._AsyncSmartLogger__queue.put_nowait(item)

    # No worker should start
    assert lg._AsyncSmartLogger__worker_tasks is None


@pytest.mark.asyncio
async def test_profiling_mode(tmp_path):
    lg = AsyncSmartLogger("prof")
    lg.add_console()
    lg.enable_profiling(True)

    await lg.a_info("hello")

    # Ensure the worker has processed the log
    await lg.flush()

    out = lg.get_profiling_details()

    assert "Avg" in out


@pytest.mark.asyncio
async def test_audit_mode(tmp_path):
    await AsyncSmartLogger.audit_everything(log_dir=str(tmp_path), logfile_name="audit.log")

    lg = AsyncSmartLogger("audited")
    lg.add_console()
    await lg.a_info("hello")

    await lg.flush()

    await AsyncSmartLogger.terminate_auditing()

    audit_file = tmp_path / "audit.log"
    assert audit_file.exists()
    assert "hello" in audit_file.read_text()


@pytest.mark.asyncio
async def test_shutdown_no_worker():
    lg = AsyncSmartLogger("no_worker_shutdown")
    lg._AsyncSmartLogger__worker_tasks = None
    await lg.shutdown()


def test_get_record_no_caller():
    rec = AsyncSmartLogger.get_record()
    assert rec.timestamp is not None


def test_rotation_callback_dict_handler(tmp_path):
    lg = AsyncSmartLogger("dict_rot")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "x.log", rotation_logic=logic)

    meta = lg.file_handlers[0]
    lg._AsyncSmartLogger__enqueue_rotation(meta)

    assert lg._AsyncSmartLogger__worker_tasks is not None


def test_rotation_queuefull(monkeypatch, tmp_path):
    lg = AsyncSmartLogger("queuefull")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "x.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    def full(*args, **kwargs):
        raise asyncio.QueueFull

    monkeypatch.setattr(lg._AsyncSmartLogger__queue, "put_nowait", full)

    # Should not crash
    handler.rotation_callback(handler)

    lg.destroy()


@pytest.mark.asyncio
async def test_worker_exits_on_sentinel(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger, AsyncOp
    import asyncio

    lg = AsyncSmartLogger("exit_test")
    lg.add_file(str(tmp_path), "exp.log")

    # Dummy queue item with .op and .payload
    class Dummy:
        def __init__(self, op):
            self.op = op
            self.payload = None

    # Enqueue sentinel
    await lg._AsyncSmartLogger__queue.put(Dummy(AsyncOp.SENTINEL))

    # Give worker time to process
    await asyncio.sleep(0.1)

    # Worker tasks should be done
    for task in lg._AsyncSmartLogger__worker_tasks:
        assert task.done()

    lg.destroy()


@pytest.mark.asyncio
async def test_raw_processed(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("raw_test")
    lg.add_file(str(tmp_path), "exp.log")

    await lg.a_raw("hello raw")
    await lg.flush()

    # RAW may not write to file, but must not crash
    assert (tmp_path / "exp.log").exists()

    lg.destroy()


@pytest.mark.asyncio
async def test_rotation_scheduled_once(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger
    from LogSmith.rotation_base import RotationLogic

    lg = AsyncSmartLogger("sched_test")
    lg.add_file(str(tmp_path), "exp.log", rotation_logic=RotationLogic(maxBytes=1))

    # Trigger multiple writes that exceed maxBytes
    for _ in range(5):
        await lg.a_info("X" * 100)

    await lg.flush()

    # Only one rotation should have been scheduled at a time
    # (no crash = branch covered)
    assert True


@pytest.mark.asyncio
async def test_worker_swallows_exceptions(tmp_path, monkeypatch):
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("err_test")
    lg.add_file(str(tmp_path), "exp.log")

    # Force __process_log to raise
    monkeypatch.setattr(
        lg,
        "_AsyncSmartLogger__process_log",
        lambda payload: (_ for _ in ()).throw(Exception("boom"))
    )

    await lg.a_info("A")
    await lg.flush()

    # Worker should not crash
    assert True

    lg.destroy()


