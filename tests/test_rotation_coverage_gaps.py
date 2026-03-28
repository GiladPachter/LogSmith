import os
import time
import pytest
from pathlib import Path
from LogSmith.rotation import ConcurrentTimedSizedRotatingFileHandler
from LogSmith.rotation_base import (
    RotationLogic,
    LargeLogEntryBehavior,
    ExpirationRule,
    ExpirationScale,
)


# ------------------------------------------------------------
# Helper: write a record
# ------------------------------------------------------------
class DummyRecord:
    def __init__(self, msg="x"):
        self.msg = msg
        self.args = ()
        self.levelname = "INFO"
        self.levelno = 20
        self.pathname = "x"
        self.filename = "x"
        self.module = "x"
        self.exc_info = None
        self.exc_text = None
        self.stack_info = None
        self.lineno = 1
        self.funcName = "f"
        self.created = time.time()
        self.msecs = 0
        self.relativeCreated = 0
        self.thread = 0
        self.threadName = "t"
        self.processName = "p"
        self.process = 0

    def getMessage(self):
        return self.msg


# ------------------------------------------------------------
# 1. Large entry behaviors
# ------------------------------------------------------------
@pytest.mark.parametrize("behavior", [
    LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty,
    LargeLogEntryBehavior.RotateFirst,
    LargeLogEntryBehavior.DumpSilently,
])
def test_large_entry_behaviors(tmp_path, behavior):
    path = tmp_path / "big.log"
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=5,
        backup_count=2,
        large_entry_behavior=behavior,
    )

    rec = DummyRecord(msg="X" * 50)

    if behavior is LargeLogEntryBehavior.DumpSilently:
        handler.emit(rec)
        assert path.read_text() == ""
    else:
        handler.emit(rec)
        assert path.exists()


def test_large_entry_crash(tmp_path):
    path = tmp_path / "crash.log"
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=5,
        backup_count=2,
        large_entry_behavior=LargeLogEntryBehavior.Crash,
    )

    rec = DummyRecord(msg="X" * 50)

    with pytest.raises(ValueError):
        handler.emit(rec)


# ------------------------------------------------------------
# 2. Time-based rollover
# ------------------------------------------------------------
def test_time_based_rollover(tmp_path):
    path = tmp_path / "time.log"
    logic = RotationLogic(when=None, maxBytes=10, backupCount=2)
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=10,
        backup_count=2,
    )

    rec = DummyRecord(msg="1234567890")
    handler.emit(rec)
    handler.emit(rec)  # triggers rotation

    rotated = list(tmp_path.glob("time.log.*"))
    assert len(rotated) >= 1


# ------------------------------------------------------------
# 3. Forced rollover on old file
# ------------------------------------------------------------
def test_force_rollover_on_old_file(tmp_path):
    path = tmp_path / "old.log"
    path.write_text("hello")

    old = time.time() - 999999
    os.utime(path, (old, old))

    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        when=None,
        max_bytes=1,
        backup_count=1,
    )

    rec = DummyRecord(msg="x")
    handler.emit(rec)

    rotated = list(tmp_path.glob("old.log.*"))
    assert len(rotated) >= 1


# ------------------------------------------------------------
# 4. PermissionError during rename
# ------------------------------------------------------------
def test_permission_error_during_rename(tmp_path, monkeypatch):
    path = tmp_path / "perm.log"
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=1,
        backup_count=1,
    )

    def bad_replace(src, dst):
        if src == str(path):
            raise PermissionError
        return os.replace(src, dst)

    monkeypatch.setattr(os, "replace", bad_replace)

    rec = DummyRecord(msg="xx")
    handler.emit(rec)  # should not raise

    assert path.exists()


# ------------------------------------------------------------
# 5. Expiration policy
# ------------------------------------------------------------
def test_expiration_policy(tmp_path):
    path = tmp_path / "exp.log"
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=1,
        backup_count=5,
        expiration_rule=ExpirationRule(ExpirationScale.Seconds, 0),
    )

    # Create fake rotated files
    for i in range(1, 4):
        f = tmp_path / f"exp.log.{i}"
        f.write_text("x")
        old = time.time() - 999999
        os.utime(f, (old, old))

    rec = DummyRecord(msg="xx")
    handler.emit(rec)

    remaining = list(tmp_path.glob("exp.log.*"))
    assert len(remaining) == 1  # only the newest survives
