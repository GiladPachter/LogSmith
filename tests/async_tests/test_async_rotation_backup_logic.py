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


