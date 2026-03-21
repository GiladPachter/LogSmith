# tests/test_smartlogger_from_demos/test_smartlogger_from_demo_rotation.py

import pytest

from LogSmith import SmartLogger
from LogSmith import RotationLogic, When
from LogSmith.level_registry import reset_levels_for_tests
from tests.helpers import isolated_logger


@pytest.fixture(autouse=True)
def cleanup_global_state():
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()
    yield
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()


def test_rotation_metadata_size_only(tmp_path):
    logger = isolated_logger("rot.size")
    log_dir = tmp_path / "size_only"
    log_dir.mkdir()

    rot = RotationLogic(maxBytes=2000, backupCount=5)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="size.log",
        rotation_logic=rot,
    )

    info = logger.file_handlers[0]["rotation"]
    assert info == {
        "maxBytes": 2000,
        "when": None,
        "interval": None,
        "backupCount": 5,
    }


def test_rotation_metadata_time_only(tmp_path):
    logger = isolated_logger("rot.time")
    log_dir = tmp_path / "time_only"
    log_dir.mkdir()

    rot = RotationLogic(when=When.SECOND, interval=1, backupCount=3)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="time.log",
        rotation_logic=rot,
    )

    info = logger.file_handlers[0]["rotation"]
    assert info == {
        "maxBytes": None,
        "when": "SECOND",
        "interval": 1,
        "backupCount": 3,
    }


def test_rotation_metadata_combined(tmp_path):
    logger = isolated_logger("rot.combo")
    log_dir = tmp_path / "combo"
    log_dir.mkdir()

    rot = RotationLogic(
        maxBytes=1500,
        when=When.SECOND,
        interval=2,
        backupCount=7,
    )

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="combo.log",
        rotation_logic=rot,
    )

    info = logger.file_handlers[0]["rotation"]
    assert info == {
        "maxBytes": 1500,
        "when": "SECOND",
        "interval": 2,
        "backupCount": 7,
    }


def test_rotation_metadata_default_logic(tmp_path):
    logger = isolated_logger("rot.default")
    log_dir = tmp_path / "default"
    log_dir.mkdir()

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="default.log",
        rotation_logic=None,
    )

    info = logger.file_handlers[0]["rotation"]
    assert info == {
        "maxBytes": None,
        "when": None,
        "interval": None,
        "backupCount": 5,
    }


def test_duplicate_file_handler_detection(tmp_path):
    logger1 = isolated_logger("rot.dup1")
    logger2 = isolated_logger("rot.dup2")

    log_dir = tmp_path / "dup"
    log_dir.mkdir()

    logger1.add_file(
        log_dir=str(log_dir),
        logfile_name="dup.log",
    )

    with pytest.raises(Exception):
        logger2.add_file(
            log_dir=str(log_dir),
            logfile_name="dup.log",
        )
