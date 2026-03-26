import pytest
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic, When, LargeLogEntryBehavior


# ------------------------------------------------------------
# 1. SIZE-BASED ROTATION
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_size_based_rotation(tmp_path, monkeypatch):
    log_dir = str(tmp_path)

    # Force deterministic suffix
    monkeypatch.setattr(
        "LogSmith.async_rotation.Async_TimedSizedRotatingFileHandler._rotation_suffix",
        lambda self: "FIXED"
    )

    logic = RotationLogic(
        when=None,
        maxBytes=20,
        backupCount=2,
    )

    logger = AsyncSmartLogger("size_rotate")
    logger.add_file(log_dir=log_dir, rotation_logic=logic)

    # Write enough to exceed 20 bytes multiple times
    for _ in range(5):
        await logger.a_info("1234567890")  # 10 bytes

    await logger.flush()
    await logger.shutdown()

    files = sorted(f.name for f in tmp_path.iterdir() if f.name.startswith("size_rotate"))
    assert len(files) >= 2
    assert any("FIXED.1" in f for f in files)


# ------------------------------------------------------------
# 2. TIME-BASED ROTATION (mock time)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_time_based_rotation(tmp_path, monkeypatch):
    log_dir = str(tmp_path)

    # Deterministic suffix
    monkeypatch.setattr(
        "LogSmith.async_rotation.Async_TimedSizedRotatingFileHandler._rotation_suffix",
        lambda self: "TROT"
    )

    # Fake time
    fake_time = [1000.0]

    monkeypatch.setattr("time.time", lambda: fake_time[0])

    logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        timestamp=None,
        maxBytes=None,
        backupCount=2,
    )

    logger = AsyncSmartLogger("time_rotate")
    logger.add_file(log_dir=log_dir, rotation_logic=logic)

    # First write — no rotation
    await logger.a_info("hello")
    await logger.flush()

    # Advance time to trigger rotation
    fake_time[0] += 2

    await logger.a_info("world")
    await logger.flush()
    await logger.shutdown()

    files = sorted(f.name for f in tmp_path.iterdir() if f.name.startswith("time_rotate"))
    assert len(files) >= 2
    assert any("TROT.1" in f for f in files)


# ------------------------------------------------------------
# 3. LARGE ENTRY BEHAVIOR: RotateFirst
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_large_entry_rotate_first(tmp_path, monkeypatch):
    log_dir = str(tmp_path)

    monkeypatch.setattr(
        "LogSmith.async_rotation.Async_TimedSizedRotatingFileHandler._rotation_suffix",
        lambda self: "LARGE"
    )

    logic = RotationLogic(
        when=None,
        maxBytes=10,
        backupCount=2,
        log_entry_larger_than_maxBytes_behavior=LargeLogEntryBehavior.RotateFirst,
    )

    logger = AsyncSmartLogger("large_rotate")
    logger.add_file(log_dir=log_dir, rotation_logic=logic)

    # This message is > maxBytes → triggers RotateFirst
    await logger.a_info("X" * 50)

    await logger.flush()
    await logger.shutdown()

    files = sorted(f.name for f in tmp_path.iterdir() if f.name.startswith("large_rotate"))
    assert len(files) >= 2
    assert any("LARGE.1" in f for f in files)


# ------------------------------------------------------------
# 4. ROTATION CALLBACK SCHEDULING
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_callback_scheduling(tmp_path, monkeypatch):
    log_dir = str(tmp_path)

    monkeypatch.setattr(
        "LogSmith.async_rotation.Async_TimedSizedRotatingFileHandler._rotation_suffix",
        lambda self: "CALLBACK"
    )

    logic = RotationLogic(
        when=None,
        maxBytes=10,
        backupCount=1,
    )

    logger = AsyncSmartLogger("callback_rotate")
    logger.add_file(log_dir=log_dir, rotation_logic=logic)

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    # Spy on rotation callback
    called = {"count": 0}

    def spy(handler_obj):
        called["count"] += 1
        logger._AsyncSmartLogger__enqueue_rotation(handler_obj)

    handler.rotation_callback = spy

    await logger.a_info("1234567890")  # triggers rotation
    await logger.flush()
    await logger.shutdown()

    assert called["count"] >= 1


# ------------------------------------------------------------
# 5. ROTATION ERROR SWALLOWING
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_error_swallowed(tmp_path, monkeypatch):
    log_dir = str(tmp_path)

    logic = RotationLogic(
        when=None,
        maxBytes=10,
        backupCount=1,
    )

    logger = AsyncSmartLogger("rot_err")
    logger.add_file(log_dir=log_dir, rotation_logic=logic)

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    # Force perform_rotation to fail
    def bad_rotate():
        raise RuntimeError("boom")

    monkeypatch.setattr(handler, "perform_rotation", bad_rotate)

    # Should not crash
    await logger.a_info("1234567890")
    await logger.flush()
    await logger.shutdown()


# ------------------------------------------------------------
# 6. ROTATION + EXPIRATION
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_expiration(tmp_path, monkeypatch):
    log_dir = str(tmp_path)

    monkeypatch.setattr(
        "LogSmith.async_rotation.Async_TimedSizedRotatingFileHandler._rotation_suffix",
        lambda self: "EXP"
    )

    from LogSmith.rotation_base import ExpirationRule, ExpirationScale

    logic = RotationLogic(
        when=None,
        maxBytes=10,
        backupCount=5,
        expiration_rule=ExpirationRule(ExpirationScale.Seconds, interval=0),
    )

    logger = AsyncSmartLogger("expire_rotate")
    logger.add_file(log_dir=log_dir, rotation_logic=logic)

    # Trigger multiple rotations
    for _ in range(5):
        await logger.a_info("1234567890")

    await logger.flush()
    await logger.shutdown()

    # ExpirationRule(interval=0) deletes all rotated files
    files = sorted(f.name for f in tmp_path.iterdir() if f.name.startswith("expire_rotate"))
    assert files == ["expire_rotate.log"]
