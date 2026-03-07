import time
from pathlib import Path

from LogSmith import (
    SmartLogger,
    RotationLogic,
    When,
    RotationTimestamp,
    ExpirationRule,
    ExpirationScale,
)


def test_rotationlogic_basic_attributes():
    rotation = RotationLogic(
        maxBytes=50_000,
        when=When.SECOND,
        interval=1,
        backupCount=5,
        append_filename_pid=True,
        append_filename_timestamp=True,
    )

    assert rotation.maxBytes == 50_000
    assert rotation.when == When.SECOND
    assert rotation.interval == 1
    assert rotation.backupCount == 5
    assert rotation.append_filename_pid is True
    assert rotation.append_filename_timestamp is True


def test_rotationtimestamp_to_seconds():
    ts = RotationTimestamp(hour=1, minute=2, second=3)
    assert ts.to_seconds() == 1 * 3600 + 2 * 60 + 3


def test_expiration_rule_configuration():
    rule = ExpirationRule(scale=ExpirationScale.Days, interval=7)
    assert rule.scale == ExpirationScale.Days
    assert rule.interval == 7


def test_size_based_rotation_triggers(tmp_path: Path):
    levels = SmartLogger.levels()
    logger = SmartLogger("rotation.size", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    rotation = RotationLogic(maxBytes=200, backupCount=3)
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="app.log",
        rotation_logic=rotation,
    )

    # generate enough logs to trigger rotation
    for i in range(100):
        logger.info("X" * 50, index=i)

    base = log_dir / "app.log"
    assert base.exists()

    rotated = [p for p in log_dir.iterdir() if p.name.startswith("app.log.")]
    assert len(rotated) <= 3


def test_time_based_rotation_triggers(tmp_path: Path):
    levels = SmartLogger.levels()
    logger = SmartLogger("rotation.time", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    rotation = RotationLogic(
        when=When.SECOND,
        interval=1,
        backupCount=5,
    )

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="time.log",
        rotation_logic=rotation,
    )

    logger.info("before rotation")
    time.sleep(1.2)
    logger.info("after rotation")

    base = log_dir / "time.log"
    assert base.exists()
    rotated = [p for p in log_dir.iterdir() if p.name.startswith("time.log.")]
    assert len(rotated) >= 1
