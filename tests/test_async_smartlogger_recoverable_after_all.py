import pytest

from LogSmith import RotationLogic
from LogSmith.async_smartlogger import AsyncSmartLogger, a_stdout


@pytest.mark.asyncio
async def test_async_basic_logging(tmp_path):
    logger = AsyncSmartLogger("async.basic")
    logger.add_file(str(tmp_path), "out.log")

    await logger.a_info("hello async")
    await logger.flush()

    text = (tmp_path / "out.log").read_text()
    assert "hello async" in text


@pytest.mark.asyncio
async def test_async_caller_resolution():
    logger = AsyncSmartLogger("async.caller")

    async def inner():
        rec = AsyncSmartLogger.get_record()
        return rec.func_name

    func = await inner()
    assert func == "inner"


@pytest.mark.asyncio
async def test_async_raw_logging(tmp_path):
    logger = AsyncSmartLogger("async.raw")
    logger.add_file(str(tmp_path), "raw.log")

    await logger.a_raw("RAW-LINE", end="")
    await logger.flush()

    assert "RAW-LINE" in (tmp_path / "raw.log").read_text()


@pytest.mark.asyncio
async def test_async_rotation(tmp_path):
    logger = AsyncSmartLogger("async.rotate")
    logic = RotationLogic(maxBytes=20)
    logger.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    for _ in range(10):
        await logger.a_info("1234567890")

    await logger.flush()

    files = {p.name for p in tmp_path.iterdir()}
    assert any(name.startswith("rot.log.") for name in files)


@pytest.mark.asyncio
async def test_async_audit(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    logger = AsyncSmartLogger("async.audit")
    await logger.a_info("audit me")
    await logger.flush()

    text = (tmp_path / "audit.log").read_text()
    assert "audit me" in text
    assert "async.audit" in text

    await AsyncSmartLogger.terminate_auditing()


@pytest.mark.asyncio
async def test_async_dynamic_levels(tmp_path):
    logger = AsyncSmartLogger("async.dynamic")
    logger.add_file(str(tmp_path), "dyn.log")

    await logger.a_info("info msg")
    await logger.a_debug("debug msg")

    await logger.flush()

    text = (tmp_path / "dyn.log").read_text()
    assert "info msg" in text
    assert "debug msg" in text


@pytest.mark.asyncio
async def test_async_get_record_metadata():
    rec = AsyncSmartLogger.get_record(exc_info=True, stack_info=True)

    assert rec.file_path.endswith(".py")
    assert rec.func_name.startswith("test_")
    assert rec.thread_id is not None
    assert rec.process_id > 0
    assert rec.stack_info is not None


@pytest.mark.asyncio
async def test_async_flush(tmp_path):
    logger = AsyncSmartLogger("async.flush")
    logger.add_file(str(tmp_path), "flush.log")

    await logger.a_info("x")
    await logger.flush()

    assert (tmp_path / "flush.log").read_text()


@pytest.mark.asyncio
async def test_async_shutdown(tmp_path):
    logger = AsyncSmartLogger("async.shutdown")
    logger.add_file(str(tmp_path), "shut.log")

    await logger.a_info("bye")
    await logger.shutdown()

    assert logger._AsyncSmartLogger__py_logger.handlers == []


@pytest.mark.asyncio
async def test_async_retire():
    logger = AsyncSmartLogger("async.retire")
    logger.retire()

    with pytest.raises(RuntimeError):
        await logger.a_info("nope")


@pytest.mark.asyncio
async def test_async_stdout(capsys):
    await a_stdout("hello", "world", sep="-")
    captured = capsys.readouterr().out

    assert "hello-world" in captured
