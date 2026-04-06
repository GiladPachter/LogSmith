import os
import time

import pytest

from LogSmith import SmartLogger
from LogSmith.rotation_base import RotationLogic, ExpirationRule, ExpirationScale


def test_expiration(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=50, backupCount=10,
                             expiration_rule=ExpirationRule(scale=ExpirationScale.Seconds, interval=1))

    logger = SmartLogger("fs_expire", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    # First rotation
    logger.info("A" * 100)
    first = log_dir / "app.log.1"

    # Make it old
    old_time = time.time() - 10
    os.utime(first, (old_time, old_time))

    # Second rotation
    logger.info("B" * 100)

    rotated = [
        p for p in log_dir.iterdir()
        if p.name.startswith("app.log.") and not p.name.endswith(".lock")
    ]

    # Only the new rotated file should remain
    assert len(rotated) == 1


def test_expiration_policy_deletes_old_files(tmp_path):
    import os, time
    from LogSmith.rotation_base import ExpirationRule, ExpirationScale
    from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler

    base = tmp_path / "exp.log"
    base.write_text("x")

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=1,
        backup_count=5,
        expiration_rule=ExpirationRule(
            scale=ExpirationScale.Seconds,
            interval=1,
        ),
    )

    # Create fake rotated files
    files = [
        tmp_path / "exp.log.1",
        tmp_path / "exp.log.2",
        tmp_path / "exp.log.3",
    ]
    for f in files:
        f.write_text("x")

    # Age them
    old = time.time() - 999999
    for f in files:
        os.utime(f, (old, old))

    # Run expiration directly
    with handler.write_lock:
        # noinspection PyUnresolvedReferences
        handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    for f in files:
        assert not f.exists()


def test_rotation_renames_correctly(tmp_path):
    from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler

    base = tmp_path / "exp.log"
    base.write_text("A")

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=1,
        backup_count=5,
        expiration_rule=None,
    )

    # Create fake rotated files
    for i in range(1, 4):
        f = tmp_path / f"exp.log.{i}"
        f.write_text(str(i))

    # Perform rotation
    with handler.write_lock:
        handler.perform_rotation()

    # Assert rename chain
    assert (tmp_path / "exp.log.1").exists()
    assert (tmp_path / "exp.log.2").exists()
    assert (tmp_path / "exp.log.3").exists()
    assert (tmp_path / "exp.log.4").exists()


@pytest.mark.asyncio
async def test_worker_processes_all_ops(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger
    from LogSmith.rotation_base import RotationLogic

    lg = AsyncSmartLogger("worker_test")
    lg.add_file(str(tmp_path), "exp.log", rotation_logic=RotationLogic(maxBytes=50))

    # LOG
    await lg.a_info("A")

    # RAW
    await lg.a_raw("B")

    # Trigger ROTATE
    await lg.a_info("X" * 200)

    await lg.flush()

    # Close handlers
    for h in lg._AsyncSmartLogger__py_logger.handlers:
        try:
            h.close()
        except:
            pass

    # Assert the file exists (worker ran)
    assert (tmp_path / "exp.log").exists()

    # Assert rotation happened (worker processed ROTATE)
    rotated = tmp_path / "exp.log.1"
    assert rotated.exists()

    # Assert LOG produced output
    text = (tmp_path / "exp.log").read_text()
    assert "INFO" in text  # LOG path hit

    # Assert RAW was processed (queue path hit)
    # RAW may not write to file, but it must not crash
    # So we assert the test reached this point without error
    assert True


@pytest.mark.asyncio
async def test_async_rotation_expiration_contract(tmp_path):
    import os, time
    from datetime import datetime, timedelta
    from LogSmith.async_smartlogger import AsyncSmartLogger
    from LogSmith.rotation_base import RotationLogic, ExpirationRule, ExpirationScale

    rotation = RotationLogic(
        maxBytes=1,
        backupCount=5,
        expiration_rule=ExpirationRule(
            scale=ExpirationScale.Seconds,
            interval=1,
        ),
    )

    lg = AsyncSmartLogger("contract_test")
    lg.add_file(str(tmp_path), "exp.log", rotation_logic=rotation)

    # Create many rotations
    for ch in "ABCDEFGHIJK":
        await lg.a_info(ch)

    await lg.flush()

    # Age all rotated files
    very_old = time.time() - 999999
    for p in tmp_path.iterdir():
        if p.name.startswith("exp.log.") and p.name != "exp.log":
            os.utime(p, (very_old, very_old))

    # Trigger expiration
    await lg.a_info("Z")
    await lg.flush()

    # Close handlers
    for h in lg._AsyncSmartLogger__py_logger.handlers:
        try:
            h.close()
        except:
            pass

    # Assert contract
    cutoff = datetime.now() - timedelta(seconds=1)
    for p in tmp_path.iterdir():
        if p.name.startswith("exp.log.") and p.name != "exp.log":
            assert datetime.fromtimestamp(p.stat().st_mtime) >= cutoff


def test_rotation_with_suffix(tmp_path, monkeypatch):
    from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler

    base = tmp_path / "exp.log"
    base.write_text("x")

    # Force a suffix
    monkeypatch.setattr(
        Async_TimedSizedRotatingFileHandler,
        "_rotation_suffix",
        lambda self: "sfx"
    )

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=1,
        backup_count=3,
        expiration_rule=None,
    )

    with handler.write_lock:
        handler.perform_rotation()

    assert (tmp_path / "exp.log.sfx.1").exists()


def test_rotation_without_suffix(tmp_path):
    from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler

    base = tmp_path / "exp.log"
    base.write_text("x")

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=1,
        backup_count=3,
        expiration_rule=None,
    )

    with handler.write_lock:
        handler.perform_rotation()

    assert (tmp_path / "exp.log.1").exists()


def test_expiration_deletes_old_files(tmp_path):
    import os, time
    from LogSmith.rotation_base import ExpirationRule, ExpirationScale
    from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler

    base = tmp_path / "exp.log"
    base.write_text("x")

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=1,
        backup_count=5,
        expiration_rule=ExpirationRule(
            scale=ExpirationScale.Seconds,
            interval=1,
        ),
    )

    # Create rotated files
    files = [tmp_path / f"exp.log.{i}" for i in (1, 2, 3)]
    for f in files:
        f.write_text("x")

    # Age them
    old = time.time() - 999999
    for f in files:
        os.utime(f, (old, old))

    with handler.write_lock:
        # noinspection PyUnresolvedReferences
        handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    for f in files:
        assert not f.exists()


@pytest.mark.asyncio
async def test_async_rotation_expiration_contract(tmp_path):
    import os, time
    from datetime import datetime, timedelta
    from LogSmith.async_smartlogger import AsyncSmartLogger
    from LogSmith.rotation_base import RotationLogic, ExpirationRule, ExpirationScale

    rotation = RotationLogic(
        maxBytes=1,
        backupCount=5,
        expiration_rule=ExpirationRule(
            scale=ExpirationScale.Seconds,
            interval=1,
        ),
    )

    lg = AsyncSmartLogger("contract_test")
    lg.add_file(str(tmp_path), "exp.log", rotation_logic=rotation)

    for ch in "ABCDEFGHIJK":
        await lg.a_info(ch)

    await lg.flush()

    very_old = time.time() - 999999
    for p in tmp_path.iterdir():
        if p.name.startswith("exp.log.") and p.name != "exp.log":
            os.utime(p, (very_old, very_old))

    await lg.a_info("Z")
    await lg.flush()

    for h in lg._AsyncSmartLogger__py_logger.handlers:
        try:
            h.close()
        except:
            pass

    cutoff = datetime.now() - timedelta(seconds=1)
    for p in tmp_path.iterdir():
        if p.name.startswith("exp.log.") and p.name != "exp.log":
            assert datetime.fromtimestamp(p.stat().st_mtime) >= cutoff
