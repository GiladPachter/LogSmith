import logging
import os
from pathlib import Path
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler


def test_backup_rotation_basic(tmp_path):
    base = Path(tmp_path) / "app.log"

    # Create fake existing rotated files: app.log.1, app.log.2
    (tmp_path / "app.log").write_text("oldbase")
    (tmp_path / "app.log.1").write_text("one")
    (tmp_path / "app.log.2").write_text("two")

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=10,
        backup_count=3,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    # Force rotation
    handler.perform_rotation()

    # After rotation:
    # app.log.3 ← old app.log.2
    # app.log.2 ← old app.log.1
    # app.log.1 ← old base file
    assert (tmp_path / "app.log.3").read_text() == "two"
    assert (tmp_path / "app.log.2").read_text() == "one"
    assert (tmp_path / "app.log.1").read_text() == "oldbase"

    # New base file exists and is empty
    assert (tmp_path / "app.log").exists()
    assert (tmp_path / "app.log").read_text() == ""


import logging
from pathlib import Path
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler


def test_backup_rotation_with_suffix(tmp_path, monkeypatch):
    base = Path(tmp_path) / "suffixed.log"
    base.write_text("base")

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=10,
        backup_count=3,
        append_filename_pid=True,
        append_filename_timestamp=True,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    # Force a fixed suffix so it doesn't change between calls
    fixed_suffix = "PID.TIMESTAMP"
    monkeypatch.setattr(handler, "_rotation_suffix", lambda: fixed_suffix)

    # Create rotated files using the SAME suffix pattern
    (tmp_path / f"suffixed.log.{fixed_suffix}.1").write_text("one")
    (tmp_path / f"suffixed.log.{fixed_suffix}.2").write_text("two")

    handler.perform_rotation()

    rotated = [f.name for f in tmp_path.iterdir() if f.name.startswith("suffixed.log.")]

    assert f"suffixed.log.{fixed_suffix}.1" in rotated
    assert f"suffixed.log.{fixed_suffix}.2" in rotated
    assert f"suffixed.log.{fixed_suffix}.3" in rotated

    assert base.exists()


def test_rotation_rename_failure(tmp_path, monkeypatch):
    base = tmp_path / "fail.log"
    base.write_text("x")

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=10,
        backup_count=2,
        append_filename_pid=False,
        append_filename_timestamp=False,
    )

    # Create .1 so rename is attempted
    (tmp_path / "fail.log.1").write_text("one")

    # Force rename to fail
    monkeypatch.setattr(os, "rename", lambda *args, **kwargs: (_ for _ in ()).throw(OSError()))

    handler.perform_rotation()

    # Should not crash
    assert base.exists()


def test_rotation_missing_intermediate_file(tmp_path):
    base = tmp_path / "skip.log"
    base.write_text("x")

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=10,
        backup_count=3,
    )

    # Only create .1, not .2
    (tmp_path / "skip.log.1").write_text("one")

    handler.perform_rotation()

    # .2 should now contain .1
    assert (tmp_path / "skip.log.2").read_text() == "one"


def test_rotation_no_backups(tmp_path):
    base = tmp_path / "nobackup.log"
    base.write_text("x")

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=10,
        backup_count=0,
    )

    handler.perform_rotation()

    # No rotated files should exist
    assert len(list(tmp_path.iterdir())) == 1


def test_rollover_weekday_today_future(tmp_path):
    from datetime import datetime
    from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
    from LogSmith.rotation_base import When, RotationTimestamp

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(tmp_path / "x.log"),
        when=When.WEDNESDAY,
        timestamp=RotationTimestamp(hour=3, minute=0, second=0),
    )

    # Fake "now" Wednesday 01:00
    now_dt = datetime(2024, 1, 3, 1, 0, 0)  # Wednesday
    now = now_dt.timestamp()

    # noinspection PyUnresolvedReferences
    nxt = handler._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)
    nxt_dt = datetime.fromtimestamp(nxt)

    assert nxt_dt.date() == now_dt.date()   # same day
    assert nxt_dt.hour == 3


def test_expiration_delete_failure(tmp_path, monkeypatch):
    import os, time
    from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
    from LogSmith.rotation_base import ExpirationRule, ExpirationScale

    base = tmp_path / "exp.log"
    base.write_text("x")

    old = tmp_path / "exp.log.1"
    old.write_text("old")

    # Make it old enough to expire
    old_mtime = time.time() - 10
    os.utime(old, (old_mtime, old_mtime))

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        expiration_rule=ExpirationRule(ExpirationScale.Seconds, interval=5),
    )

    # Force deletion to fail
    monkeypatch.setattr(os, "remove", lambda *args, **kwargs: (_ for _ in ()).throw(OSError()))

    # noinspection PyUnresolvedReferences
    handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    # File should still exist because deletion failed
    assert old.exists()


