# tests/test_smartlogger_from_demos/test_smartlogger_from_demo_misc_full.py

import pytest

from LogSmith import SmartLogger
from LogSmith import LogRecordDetails
from LogSmith import RotationLogic
from LogSmith.level_registry import reset_levels_for_tests

from tests.helpers import isolated_logger


@pytest.fixture(autouse=True)
def cleanup_global_state():
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()
    yield
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()


def test_get_record_exc_and_stack():
    logger = isolated_logger("misc_get")

    # exc_info
    try:
        1 / 0
    except ZeroDivisionError:
        rec = SmartLogger.get_record(exc_info = True)
        assert rec.exc_info["exc_parts"]["err_type_name"] == "ZeroDivisionError"

    # stack_info
    logger.debug("stack", stack_info=True)
    rec2 = SmartLogger.get_record(stack_info = True)
    assert isinstance(rec2.stack_info, str)


def test_retire_and_destroy_full(tmp_path):
    logger = isolated_logger("misc_lifecycle")
    logger.add_console()

    # retire
    logger.info("before retire")
    logger.retire()

    with pytest.raises(Exception):
        logger.add_console()

    with pytest.raises(Exception):
        logger.add_file(log_dir=str(tmp_path), logfile_name="x.log")

    with pytest.raises(Exception):
        logger.info("after retire")

    # destroy
    logger.destroy()

    # destroy again (reentrant)
    logger.destroy()

    # all operations must fail
    with pytest.raises(Exception):
        logger.info("fail")

    with pytest.raises(Exception):
        logger.raw("fail")

    with pytest.raises(Exception):
        logger.add_console()

    with pytest.raises(Exception):
        logger.add_file(log_dir=str(tmp_path), logfile_name="y.log")

    with pytest.raises(Exception):
        logger.remove_file_handler(str(tmp_path), "x.log")


def test_invalid_message_parts_order():
    with pytest.raises(Exception):
        LogRecordDetails(message_parts_order=["timestamp", "message"])


def test_invalid_log_dir():
    logger = isolated_logger("misc_logdir")

    with pytest.raises(Exception):
        logger.add_file(log_dir="relative/path", logfile_name="x.log")

    logger.destroy()


def test_invalid_rotation_logic():
    with pytest.raises(Exception):
        RotationLogic(maxBytes=-1)


def test_invalid_level_registration():
    # duplicate
    with pytest.raises(Exception):
        SmartLogger.register_level("INFO", 20)

    # invalid name
    with pytest.raises(Exception):
        SmartLogger.register_level("BAD LEVEL NAME!", 55)


def test_invalid_theme_registration():
    with pytest.raises(Exception):
        SmartLogger.apply_color_theme({20: "not a LevelStyle"})
