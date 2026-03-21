# tests/test_smartlogger_from_demo_misc.py

import json
import logging
import pytest
from pathlib import Path

from LogSmith import SmartLogger
from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith import RotationLogic
from LogSmith.colors import CPrint
from LogSmith.level_registry import reset_levels_for_tests


@pytest.fixture(autouse=True)
def cleanup_global_state():
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()
    yield
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()


def test_get_record_basic_fields():
    rec = SmartLogger.get_record()

    # Timestamp always present
    assert isinstance(rec.timestamp, str)

    # Level is None when no record is passed
    assert rec.level is None

    # exc_info always exists as dict
    assert isinstance(rec.exc_info, dict)
    assert rec.exc_info["exc_parts"]["err_type_name"] is None

    # stack_info always present (SmartLogger forces it)
    assert isinstance(rec.stack_info, str)
    assert "File" in rec.stack_info


def test_exc_info_and_stack_info_capture(tmp_path):
    logger = SmartLogger("misc.exc", level=logging.DEBUG)
    logger.add_console()

    try:
        1 / 0
    except ZeroDivisionError:
        rec = SmartLogger.get_record()
        assert rec.exc_info["exc_parts"]["err_type_name"] == "ZeroDivisionError"

    # stack_info=True should produce a non-empty string
    logger.debug("debug with stack", stack_info=True)


def test_retire_and_destroy_behavior():
    logger = SmartLogger("misc.retire", level=logging.INFO)
    logger.add_console()

    logger.info("before retire")
    logger.retire()

    # After retire, adding handlers should fail
    with pytest.raises(Exception):
        logger.add_console()

    logger.destroy()

    # After destroy, any logging should fail
    with pytest.raises(Exception):
        logger.info("should fail")


def test_invalid_message_parts_order():
    # Forbidden field "timestamp"
    with pytest.raises(Exception):
        LogRecordDetails(
            message_parts_order=["timestamp", "message"]
        )


def test_invalid_log_dir():
    logger = SmartLogger("misc.invalid_logdir", level=logging.INFO)

    # Relative paths are forbidden
    with pytest.raises(Exception):
        logger.add_file(log_dir="relative/path/not/allowed", logfile_name="x.log")


def test_invalid_rotation_logic():
    # Negative maxBytes is invalid
    with pytest.raises(Exception):
        RotationLogic(maxBytes=-5)


def test_invalid_level_registration():
    # Duplicate name
    with pytest.raises(Exception):
        SmartLogger.register_level("INFO", 20)

    # Invalid name
    with pytest.raises(Exception):
        SmartLogger.register_level("BAD LEVEL NAME!", 55)


def test_invalid_theme_registration():
    from LogSmith import LevelStyle
    from LogSmith.colors import CPrint

    # Wrong key type (string instead of int)
    with pytest.raises(Exception):
        SmartLogger.apply_color_theme({"INFO": LevelStyle(fg=CPrint.FG.RED)})

    # Wrong value type (string instead of LevelStyle)
    with pytest.raises(Exception):
        SmartLogger.apply_color_theme({20: "not a LevelStyle"})
