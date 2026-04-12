import logging

import pytest

from LogSmith import RotationLogic
from LogSmith import SmartLogger
from LogSmith import AsyncSmartLogger


@pytest.mark.asyncio
async def test_async_basic_logging(tmp_path):
    logger = AsyncSmartLogger("async_basic")
    logger.add_file(str(tmp_path), "out.log")

    await logger.a_info("hello async")
    await logger.flush()

    text = (tmp_path / "out.log").read_text()
    assert "hello async" in text

    logger.destroy()


@pytest.mark.asyncio
async def test_async_caller_resolution():
    logger = AsyncSmartLogger("async_caller")

    async def inner():
        rec = AsyncSmartLogger.get_record()
        return rec.func_name

    func = await inner()
    assert func == "inner"


@pytest.mark.asyncio
async def test_async_raw_logging(tmp_path):
    logger = AsyncSmartLogger("async_raw")
    logger.add_file(str(tmp_path), "raw.log")

    await logger.a_raw(logging.INFO, "RAW-LINE", end="")
    await logger.flush()

    assert "RAW-LINE" in (tmp_path / "raw.log").read_text()

    logger.destroy()


@pytest.mark.asyncio
async def test_async_rotation(tmp_path):
    logger = AsyncSmartLogger("async_rotate")
    logic = RotationLogic(maxBytes=20)
    logger.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    for _ in range(10):
        await logger.a_info("1234567890")

    await logger.flush()

    files = {p.name for p in tmp_path.iterdir()}
    assert any(name.startswith("rot.log.") for name in files)

    logger.destroy()


@pytest.mark.asyncio
async def test_async_audit(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    logger = AsyncSmartLogger("async_audit")
    await logger.a_info("audit me")
    await logger.flush()

    text = (tmp_path / "audit.log").read_text()
    assert "audit me" in text
    assert "async_audit" in text

    await AsyncSmartLogger.terminate_auditing()


@pytest.mark.asyncio
async def test_async_dynamic_levels(tmp_path):
    logger = AsyncSmartLogger("async_dynamic")
    logger.add_file(str(tmp_path), "dyn.log")

    await logger.a_info("info msg")
    await logger.a_debug("debug msg")

    await logger.flush()

    text = (tmp_path / "dyn.log").read_text()
    assert "info msg" in text
    assert "debug msg" in text

    logger.destroy()


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
    logger = AsyncSmartLogger("async_flush")
    logger.add_file(str(tmp_path), "flush.log")

    await logger.a_info("x")
    await logger.flush()

    assert (tmp_path / "flush.log").read_text()


@pytest.mark.asyncio
async def test_async_shutdown(tmp_path):
    logger = AsyncSmartLogger("async_shutdown")
    logger.add_file(str(tmp_path), "shut.log")

    await logger.a_info("bye")
    await logger.shutdown()

    assert logger._AsyncSmartLogger__py_logger.handlers == []

    logger.destroy()


@pytest.mark.asyncio
async def test_async_retire():
    logger = AsyncSmartLogger("async_retire")
    logger.retire()

    with pytest.raises(RuntimeError):
        await logger.a_info("nope")

    logger.destroy()


@pytest.mark.asyncio
async def test_async_enqueue_raw_no_errors(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger

    logger = AsyncSmartLogger("async_raw_enqueue")
    logger.add_file(str(tmp_path), "raw2.log")

    # This hits the enqueue path where put_nowait succeeds immediately
    await logger.a_raw(logging.INFO, "X")
    await logger.flush()

    assert "X" in (tmp_path / "raw2.log").read_text()


@pytest.mark.asyncio
async def test_async_rotation_enqueue_inside_loop(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger
    from LogSmith.rotation_base import RotationLogic

    logger = AsyncSmartLogger("async_rotate_enqueue")
    logic = RotationLogic(maxBytes=1)
    logger.add_file(str(tmp_path), "rot2.log", rotation_logic=logic)

    # Force rotation from inside the worker loop
    await logger.a_info("A")
    await logger.flush()

    # If enqueue succeeded inside the loop, rotation will have occurred
    files = {p.name for p in tmp_path.iterdir()}
    assert any(name.startswith("rot2.log.") for name in files)


@pytest.mark.asyncio
async def test_async_rotation_profiling(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger
    from LogSmith.rotation_base import RotationLogic

    logger = AsyncSmartLogger("async_rotate_profile")
    logger.enable_profiling(True)

    logic = RotationLogic(maxBytes=1)
    logger.add_file(str(tmp_path), "rot3.log", rotation_logic=logic)

    await logger.a_info("A")
    await logger.flush()

    stats = logger.get_profiling_details()
    assert "rotation time" in stats.lower()


@pytest.mark.asyncio
async def test_async_dynamic_level_caching(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger

    logger = AsyncSmartLogger("async_dynamic_cache")
    logger.add_file(str(tmp_path), "dyn2.log")

    # First call creates the dynamic method
    await logger.a_warning("W1")

    # Second call uses cached method (covers setattr path)
    await logger.a_warning("W2")

    await logger.flush()

    text = (tmp_path / "dyn2.log").read_text()
    assert "W1" in text and "W2" in text


@pytest.mark.asyncio
async def test_async_apply_color_theme_errors():
    from LogSmith.async_smartlogger import AsyncSmartLogger
    from LogSmith.levels import LevelStyle

    with pytest.raises(TypeError):
        await AsyncSmartLogger.apply_color_theme("not a dict")

    with pytest.raises(TypeError):
        await AsyncSmartLogger.apply_color_theme({ "x": LevelStyle() })

    with pytest.raises(TypeError):
        await AsyncSmartLogger.apply_color_theme({ 10: "not a style" })


@pytest.mark.asyncio
async def test_async_flush_calls_handler_flush(tmp_path, monkeypatch):
    from LogSmith.async_smartlogger import AsyncSmartLogger

    logger = AsyncSmartLogger("async_flush_handler")
    logger.add_file(str(tmp_path), "flush2.log")

    called = {}

    def fake_flush():
        called["yes"] = True

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]
    monkeypatch.setattr(handler, "flush", fake_flush)

    await logger.a_info("X")
    await logger.flush()

    assert called.get("yes") is True


def test_smartlogger_get_record_exc_info():
    lg = SmartLogger("exc_test_smart")

    # noinspection PyBroadException
    try:
        raise ValueError("boom")
    except Exception as e:
        record = lg.get_record(exc_info = True)

    assert record.exc_info is not None
    assert isinstance(record.exc_info, dict)
    assert record.exc_info["exc_parts"]["err_type_name"] == "ValueError"
    assert str(record.exc_info["exc_parts"]["error_text"]) == "boom"
    assert "ValueError: boom" in record.exc_info["full_trace_text"]

    lg.destroy()


import pytest

@pytest.mark.asyncio
async def test_asyncsmartlogger_get_record_exc_info():
    lg = AsyncSmartLogger("exc_test_async")

    # noinspection PyBroadException
    try:
        raise RuntimeError("async boom")
    except Exception as e:
        record = lg.get_record(exc_info = True)

    assert record.exc_info is not None
    assert isinstance(record.exc_info, dict)
    assert record.exc_info["exc_parts"]["err_type_name"] == "RuntimeError"
    assert str(record.exc_info["exc_parts"]["error_text"]) == "async boom"
    assert "RuntimeError: async boom" in record.exc_info["full_trace_text"]

    await lg.shutdown()
    lg.destroy()
