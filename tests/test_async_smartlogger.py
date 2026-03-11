from pathlib import Path

import pytest

from LogSmith import CPrint, LogRecordDetails, OptionalRecordFields, RotationLogic, a_stdout
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
