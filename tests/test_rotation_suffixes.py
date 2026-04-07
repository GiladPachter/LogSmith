import os
import re
import asyncio
from pathlib import Path

import pytest

from LogSmith import SmartLogger, AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic


def _pattern_for_rotated(base: Path, pid: bool, ts: bool):
    stem = base.stem

    # No suffixes
    if not pid and not ts:
        return re.compile(rf"^{re.escape(stem)}\.log\.1$")

    # Timestamp only
    if ts and not pid:
        return re.compile(
            rf"^{re.escape(stem)}\.log\.\d{{8}}_\d{{6}}\.1$"
        )

    # PID only
    if pid and not ts:
        return re.compile(
            rf"^{re.escape(stem)}\.log\.{os.getpid()}\.1$"
        )

    # BOTH: PID first, then timestamp  ← THIS IS THE FIX
    return re.compile(
        rf"^{re.escape(stem)}\.log\.{os.getpid()}\.\d{{8}}_\d{{6}}\.1$"
    )


def _list_rotated_files(base: Path):
    return [
        f.name for f in base.parent.iterdir()
        if f.name != base.name and f.name.startswith(base.stem)
    ]


@pytest.mark.parametrize("pid, ts",
                         [(False, False),
                          (True,  False),
                          (False, True),
                          (True,  True)]
                         )
def test_smartlogger_rotation_suffixes(tmp_path, pid, ts):
    log_dir = tmp_path
    logfile = "app.log"
    base = log_dir / logfile

    logic = RotationLogic(
        maxBytes=1,
        append_filename_pid=pid,
        append_filename_timestamp=ts,
    )

    logger = SmartLogger("smart_test")
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name=logfile,
        rotation_logic=logic,
    )

    # Trigger rotation
    logger.info("X")

    rotated = _list_rotated_files(base)
    assert rotated, "No rotated files found"

    pattern = _pattern_for_rotated(base, pid, ts)
    assert pattern.match(rotated[0]), rotated[0]

    logger.destroy()


@pytest.mark.parametrize("pid, ts",
                         [(False, False),
                          (True,  False),
                          (False, True),
                          (True,  True)]
                         )
@pytest.mark.asyncio
async def test_asyncsmartlogger_rotation_suffixes(tmp_path, pid, ts):
    log_dir = tmp_path
    logfile = "app.log"
    base = log_dir / logfile

    logic = RotationLogic(
        maxBytes=1,
        append_filename_pid=pid,
        append_filename_timestamp=ts,
    )

    logger = AsyncSmartLogger("async_test")
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name=logfile,
        rotation_logic=logic,
    )

    # Trigger rotation
    await logger.a_info("X")

    # Allow async worker to perform rotation
    await asyncio.sleep(0.1)

    rotated = _list_rotated_files(base)
    assert rotated, "No rotated files found"

    pattern = _pattern_for_rotated(base, pid, ts)
    assert pattern.match(rotated[0]), rotated[0]

    logger.destroy()


def test_rotation_with_suffix(tmp_path, monkeypatch):
    from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler

    base = tmp_path / "exp.log"
    base.write_text("x")

    monkeypatch.setattr(
        Async_TimedSizedRotatingFileHandler,
        "_Async_TimedSizedRotatingFileHandler__rotation_suffix",
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
