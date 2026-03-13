import pytest

from LogSmith import SmartLogger, RotationLogic
from LogSmith.rotation import LargeLogEntryBehavior


def test_large_entry_default_empty_file(tmp_path):
    log_dir = tmp_path
    rotation = RotationLogic(maxBytes=10, backupCount=5)

    logger = SmartLogger("test.default.empty")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    # Oversized entry (len > 10)
    logger.info("X" * 20)

    # Expect: write first, then rotate
    rotated = sorted(p for p in log_dir.iterdir() if p.name.startswith("app.log.") and p.suffix != ".lock")
    assert len(rotated) == 1

    # Rotated file should contain the entry
    assert rotated[0].read_text(encoding="utf-8").strip().endswith("XXXXXXXXXXXXXXXXXXXX")


def test_large_entry_default_nonempty_file(tmp_path):
    log_dir = tmp_path
    rotation = RotationLogic(maxBytes=100, backupCount=5)

    logger = SmartLogger("test.default.nonempty")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    # First write a small entry that does NOT exceed maxBytes when formatted
    logger.info("ok")

    # Now write an oversized entry that DOES exceed maxBytes
    logger.info("X" * 200)

    rotated = sorted(
        p for p in log_dir.iterdir()
        if p.name.startswith("app.log.") and p.suffix != ".lock"
    )
    assert len(rotated) == 1

    # Rotated file should contain the small entry
    assert rotated[0].read_text().strip().endswith("ok")

    # Current file should contain the large entry
    assert (log_dir / "app.log").read_text().strip().endswith("X" * 200)


def test_large_entry_rotate_first(tmp_path):
    log_dir = tmp_path
    rotation = RotationLogic(
        maxBytes=10,
        backupCount=5,
        log_entry_larger_than_maxBytes_behavior=LargeLogEntryBehavior.RotateFirst,
    )

    logger = SmartLogger("test.rotatefirst")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    logger.info("X" * 20)

    rotated = sorted(p for p in log_dir.iterdir() if p.name.startswith("app.log.") and p.suffix != ".lock")
    assert len(rotated) == 1

    # Rotated file should be empty (because we rotated before writing)
    assert rotated[0].read_text() == ""

    # Current file contains the large entry
    assert (log_dir / "app.log").read_text().strip().endswith("XXXXXXXXXXXXXXXXXXXX")


def test_large_entry_dump_silently(tmp_path):
    log_dir = tmp_path
    rotation = RotationLogic(
        maxBytes=10,
        backupCount=5,
        log_entry_larger_than_maxBytes_behavior=LargeLogEntryBehavior.DumpSilently,
    )

    logger = SmartLogger("test.dumpsilently")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    logger.info("X" * 20)

    # No rotation, no write
    assert (log_dir / "app.log").read_text() == ""
    rotated = [p for p in log_dir.iterdir() if p.name.startswith("app.log.") and p.suffix != ".lock"]
    assert rotated == []


def test_large_entry_crash(tmp_path):
    log_dir = tmp_path
    rotation = RotationLogic(
        maxBytes=10,
        backupCount=5,
        log_entry_larger_than_maxBytes_behavior=LargeLogEntryBehavior.Crash,
    )

    logger = SmartLogger("test.crash")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    with pytest.raises(ValueError):
        logger.info("X" * 20)

    # No rotation, no write
    assert (log_dir / "app.log").read_text() == ""


def test_backup_count(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=50, backupCount=2)
    logger = SmartLogger("fs.backup")
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    for i in range(50):
        logger.info("X" * 20)

    rotated = [
        p for p in log_dir.iterdir()
        if p.name.startswith("app.log.") and p.suffix != ".lock"
    ]

    assert len(rotated) <= 2


