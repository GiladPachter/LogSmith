import pytest
import os
import time
from datetime import datetime

from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import (
    RotationLogic,
    When,
    RotationTimestamp,
    LargeLogEntryBehavior,
    ExpirationRule,
    ExpirationScale,
)


# ------------------------------------------------------------
# 2. Large-entry behavior: RotateFirst
# ------------------------------------------------------------
def test_large_entry_rotate_first(tmp_path):
    file = tmp_path / "x.log"
    file.write_text("")

    logic = RotationLogic(
        maxBytes=10,
        log_entry_larger_than_maxBytes_behavior=LargeLogEntryBehavior.RotateFirst,
    )
    handler = Async_TimedSizedRotatingFileHandler(str(file), max_bytes=10,
                                                  large_entry_behavior=LargeLogEntryBehavior.RotateFirst)

    assert handler._Async_TimedSizedRotatingFileHandler__async_large_entry_decision("X" * 50).name == "ROTATE_THEN_WRITE"


# ------------------------------------------------------------
# 3. Large-entry behavior: DumpSilently
# ------------------------------------------------------------
def test_large_entry_dump_silently(tmp_path):
    file = tmp_path / "x.log"
    file.write_text("")

    handler = Async_TimedSizedRotatingFileHandler(
        str(file),
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.DumpSilently,
    )

    assert handler._Async_TimedSizedRotatingFileHandler__async_large_entry_decision("X" * 50).name == "DROP"


# ------------------------------------------------------------
# 4. Large-entry behavior: Crash
# ------------------------------------------------------------
def test_large_entry_crash(tmp_path):
    file = tmp_path / "x.log"
    file.write_text("")

    handler = Async_TimedSizedRotatingFileHandler(
        str(file),
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.Crash,
    )

    with pytest.raises(ValueError):
        handler._Async_TimedSizedRotatingFileHandler__async_large_entry_decision("X" * 50)


# ------------------------------------------------------------
# 5. Time-based rollover (SECOND)
# ------------------------------------------------------------
def test_compute_next_rollover_second(tmp_path):
    file = tmp_path / "x.log"
    file.write_text("")

    handler = Async_TimedSizedRotatingFileHandler(
        str(file),
        when=When.SECOND,
        interval=5,
    )

    now = time.time()
    nxt = handler._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)

    assert abs(nxt - (now + 5)) < 0.001


# ------------------------------------------------------------
# 6. Time-based rollover (MINUTE)
# ------------------------------------------------------------
def test_compute_next_rollover_minute(tmp_path):
    file = tmp_path / "x.log"
    file.write_text("")

    handler = Async_TimedSizedRotatingFileHandler(
        str(file),
        when=When.MINUTE,
        interval=2,
    )

    now = time.time()
    nxt = handler._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)

    assert abs(nxt - (now + 120)) < 0.001


# ------------------------------------------------------------
# 7. Timestamp-based rollover (EVERYDAY)
# ------------------------------------------------------------
def test_timestamp_rollover_everyday(tmp_path):
    file = tmp_path / "x.log"
    file.write_text("")

    ts = RotationTimestamp(hour=12, minute=30, second=0)

    handler = Async_TimedSizedRotatingFileHandler(
        str(file),
        when=When.EVERYDAY,
        timestamp=ts,
    )

    now = datetime(2024, 1, 1, 12, 0, 0).timestamp()
    nxt = handler._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)

    dt = datetime.fromtimestamp(nxt)
    assert dt.hour == 12
    assert dt.minute == 30
    assert dt > datetime.fromtimestamp(now)


# ------------------------------------------------------------
# 8. Expiration rule: delete expired rotated files
# ------------------------------------------------------------
def test_expiration_rule_seconds(tmp_path):
    base = tmp_path / "x.log"
    base.write_text("")

    # Create rotated files
    old = tmp_path / "x.log.1"
    new = tmp_path / "x.log.2"

    old.write_text("old")
    new.write_text("new")

    # Set mtimes
    old_time = time.time() - 100
    new_time = time.time() - 5
    os.utime(old, (old_time, old_time))
    os.utime(new, (new_time, new_time))

    handler = Async_TimedSizedRotatingFileHandler(
        str(base),
        expiration_rule=ExpirationRule(ExpirationScale.Seconds, interval=10),
    )

    handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    assert not old.exists()
    assert new.exists()


# ------------------------------------------------------------
# 9. Backup rotation naming
# ------------------------------------------------------------
def test_backup_rotation_naming(tmp_path):
    base = tmp_path / "x.log"
    base.write_text("hello")

    handler = Async_TimedSizedRotatingFileHandler(
        str(base),
        max_bytes=1,
        backup_count=3,
    )

    # Force deterministic suffix
    handler.append_filename_timestamp = False
    handler.append_filename_pid = False

    handler.perform_rotation()

    assert (tmp_path / "x.log.1").exists()
    assert base.exists()
