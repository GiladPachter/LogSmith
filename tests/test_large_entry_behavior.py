import json
import logging

import pytest

from LogSmith import SmartLogger, RotationLogic, When, RotationTimestamp, AsyncSmartLogger
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.file_registry import FileHandlerRegistry
from LogSmith.formatter import StructuredNDJSONFormatter, LogRecordDetails
from LogSmith.rotation import LargeLogEntryBehavior, ConcurrentTimedSizedRotatingFileHandler


def test_large_entry_default_empty_file(tmp_path):
    log_dir = tmp_path
    rotation = RotationLogic(maxBytes=10, backupCount=5)

    logger = SmartLogger("test_default_empty")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    # Oversized entry (len > 10)
    logger.info("X" * 20)

    # Expect: write first, then rotate
    rotated = sorted(p for p in log_dir.iterdir() if p.name.startswith("app.log.") and p.suffix != ".lock")
    assert len(rotated) == 1

    # Rotated file should contain the entry
    assert rotated[0].read_text(encoding="utf-8").strip().endswith("XXXXXXXXXXXXXXXXXXXX")


def test_large_entry_default_nonempty_file(tmp_path):
    log_dir = tmp_path
    rotation = RotationLogic(maxBytes=100, backupCount=5)

    logger = SmartLogger("test_default_nonempty")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    # First write a small entry that does NOT exceed maxBytes when formatted
    logger.info("ok")

    # Now write an oversized entry that DOES exceed maxBytes
    logger.info("X" * 200)

    rotated = sorted(
        p for p in log_dir.iterdir()
        if p.name.startswith("app.log.") and p.suffix != ".lock"
    )
    assert len(rotated) == 1

    # Rotated file should contain the small entry
    assert rotated[0].read_text().strip().endswith("ok")

    # Current file should contain the large entry
    assert (log_dir / "app.log").read_text().strip().endswith("X" * 200)


def test_large_entry_rotate_first(tmp_path):
    log_dir = tmp_path
    rotation = RotationLogic(
        maxBytes=10,
        backupCount=5,
        log_entry_larger_than_maxBytes_behavior=LargeLogEntryBehavior.RotateFirst,
    )

    logger = SmartLogger("test_rotatefirst")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    logger.info("X" * 20)

    rotated = sorted(p for p in log_dir.iterdir() if p.name.startswith("app.log.") and p.suffix != ".lock")
    assert len(rotated) == 1

    # Rotated file should be empty (because we rotated before writing)
    assert rotated[0].read_text() == ""

    # Current file contains the large entry
    assert (log_dir / "app.log").read_text().strip().endswith("XXXXXXXXXXXXXXXXXXXX")


def test_large_entry_dump_silently(tmp_path):
    log_dir = tmp_path
    rotation = RotationLogic(
        maxBytes=10,
        backupCount=5,
        log_entry_larger_than_maxBytes_behavior=LargeLogEntryBehavior.DumpSilently,
    )

    logger = SmartLogger("test_dumpsilently")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    logger.info("X" * 20)

    # No rotation, no write
    assert (log_dir / "app.log").read_text() == ""
    rotated = [p for p in log_dir.iterdir() if p.name.startswith("app.log.") and p.suffix != ".lock"]
    assert rotated == []


def test_large_entry_crash(tmp_path):
    log_dir = tmp_path
    rotation = RotationLogic(
        maxBytes=10,
        backupCount=5,
        log_entry_larger_than_maxBytes_behavior=LargeLogEntryBehavior.Crash,
    )

    logger = SmartLogger("test_crash")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    with pytest.raises(ValueError):
        logger.info("X" * 20)

    # No rotation, no write
    assert (log_dir / "app.log").read_text() == ""


def test_backup_count(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=50, backupCount=2)
    logger = SmartLogger("fs_backup")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    for i in range(50):
        logger.info("X" * 20)

    rotated = [
        p for p in log_dir.iterdir()
        if p.name.startswith("app.log.") and p.suffix != ".lock"
    ]

    assert len(rotated) <= 2

    logger.destroy()


def test_sync_large_entry_exceed_if_empty(tmp_path):
    path = tmp_path / "x.log"

    h = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty,
    )

    # First write: file empty → allowed
    h.emit(logging.makeLogRecord({"level": logging.INFO, "msg": "123456"}))

    path2 = tmp_path / "x.log.1"
    assert path.read_text(encoding="utf-8") == ""           # rotation immediately after writing oversized log entry
    assert path2.exists()
    assert path2.read_text(encoding="utf-8") == "123456\n"  # read from rotating file

    # Second write: file not empty → rotate first
    h.emit(logging.makeLogRecord({"msg": "abcdef"}))

    assert path2.read_text() == "abcdef\n"


@pytest.mark.asyncio
async def test_async_large_entry_exceed_if_empty(tmp_path):
    path = tmp_path / "x.log"

    h = Async_TimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty,
    )

    # Fake rotation callback
    rotations = []
    h.rotation_callback = lambda handler: rotations.append("rotate")

    # First write: allowed
    h.emit(logging.makeLogRecord({"msg": "123456"}))
    assert path.read_text() == "123456\n"

    # Second write: rotate_then_write
    h.emit(logging.makeLogRecord({"msg": "abcdef"}))

    # Rotation scheduled
    assert rotations == ["rotate"]


def test_async_large_entry_dump_silently(tmp_path):
    path = tmp_path / "x.log"

    h = Async_TimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.DumpSilently,
    )

    h.emit(logging.makeLogRecord({"msg": "123456"}))
    assert path.read_text() == ""  # dropped


def test_async_large_entry_crash(tmp_path):
    path = tmp_path / "x.log"

    h = Async_TimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.Crash,
    )

    with pytest.raises(ValueError):
        h.emit(logging.makeLogRecord({"msg": "123456"}))


def test_rotation_logic_second_interval():
    rl = RotationLogic(when=When.SECOND, interval=5)
    assert rl.interval == 5

def test_rotation_logic_daily_timestamp():
    rl = RotationLogic(when=When.EVERYDAY, timestamp=RotationTimestamp(3, 30, 0))
    assert rl.timestamp.hour == 3
    assert rl.timestamp.minute == 30


# from LogSmith.rotation_base import BaseTimedSizedRotatingFileHandler, LargeLogEntryBehavior

def test_base_handle_large_entry_dump(tmp_path):
    path = tmp_path / "x.log"
    h = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.DumpSilently,
    )

    # noinspection PyUnresolvedReferences
    assert h._ConcurrentTimedSizedRotatingFileHandler__handle_large_entry("123456") is True


def test_ndjson_no_blank_lines():
    fmt = StructuredNDJSONFormatter(LogRecordDetails())
    r = logging.makeLogRecord({"msg": "hello", "level": logging.INFO})
    out = fmt.format(r)
    assert out.endswith("}")  # no newline
    json.loads(out)  # must be valid JSON


def test_registry_prevents_duplicates(tmp_path):
    p = tmp_path / "x.log"
    FileHandlerRegistry.register(str(p))

    with pytest.raises(ValueError):
        FileHandlerRegistry.register(str(p))

    FileHandlerRegistry.unregister(str(p))


@pytest.mark.asyncio
async def test_async_worker_survives_handler_exception(tmp_path):
    logger = AsyncSmartLogger("x")

    # Add a handler that always throws
    class BadHandler(logging.Handler):
        def emit(self, record):
            raise RuntimeError("boom")

    logger._AsyncSmartLogger__py_logger.addHandler(BadHandler())

    # Capture baseline BEFORE logging
    before = logger.messages_processed()

    await logger.a_info("hello")
    # await logger.__queue.join()  # worker must not die
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    after = logger.messages_processed()

    # No successful writes → no increment
    assert after == before

    await logger.destroy()


def test_smartlogger_add_remove_console():
    log = SmartLogger("x")
    log.add_console()
    assert log.console_handler is not None
    log.remove_console()
    assert log.console_handler is None

    log.destroy()


@pytest.mark.asyncio
async def test_async_logger_raw(tmp_path):
    logger = AsyncSmartLogger("y")
    logger.add_file(str(tmp_path), "y.log")

    await logger.a_raw(logging.INFO, "hello")
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    assert (tmp_path / "y.log").read_text().strip() == "hello"
