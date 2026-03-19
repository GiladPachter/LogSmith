import os
import pytest

from pathlib import Path

from LogSmith import CPrint, LogRecordDetails, OptionalRecordFields, RotationLogic
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic, When
from LogSmith import LevelStyle
from LogSmith.level_registry import LEVELS

from tests.helpers import read_file


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

    await async_logger.shutdown()

    log_file = async_logger.handler_info[0]['path']
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

    # Handlers remain — shutdown does NOT remove them
    assert len(logger.handler_info) == 1


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


def test_apply_color_theme_and_errors():
    # valid theme
    theme = {meta["value"]: LevelStyle() for name, meta in LEVELS.all().items()}
    AsyncSmartLogger.apply_color_theme(theme)

    # invalid theme type
    with pytest.raises(TypeError):
        AsyncSmartLogger.apply_color_theme("not-a-dict")  # type: ignore[arg-type]

    # invalid key type
    with pytest.raises(TypeError):
        AsyncSmartLogger.apply_color_theme({"x": LevelStyle()})  # type: ignore[arg-type]

    # invalid value type
    with pytest.raises(TypeError):
        AsyncSmartLogger.apply_color_theme({10: "not-style"})  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_get_record_includes_basic_metadata():
    rec = AsyncSmartLogger.get_record(exc_info=False, stack_info=True)
    assert rec.file_name.endswith(".py")
    assert rec.func_name is not None
    assert rec.thread_id is not None
    assert rec.process_id == os.getpid()
    assert rec.stack_info is not None
