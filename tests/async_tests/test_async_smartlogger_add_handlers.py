import pytest
import logging
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic, When, RotationTimestamp


# ------------------------------------------------------------
# add_console validation
# ------------------------------------------------------------

def test_add_console_duplicate_is_ignored(caplog):
    logger = AsyncSmartLogger("test_console_dup")
    logger.add_console(level=logging.INFO)
    # Second call should be ignored (no duplicate console handler)
    logger.add_console(level=logging.INFO)

    handlers = logger._AsyncSmartLogger__py_logger.handlers
    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.StreamHandler)


def test_add_console_invalid_output_mode():
    logger = AsyncSmartLogger("test_console_invalid")
    with pytest.raises(ValueError):
        logger.add_console(output_mode="not-a-mode")


def test_add_console_after_retire():
    logger = AsyncSmartLogger("test_console_retired")
    logger.retire()
    with pytest.raises(RuntimeError):
        logger.add_console()


# ------------------------------------------------------------
# add_file validation
# ------------------------------------------------------------

def test_add_file_requires_normalized_log_dir(tmp_path):
    logger = AsyncSmartLogger("test_file_norm")

    # Create a non-normalized path: "tmp_path/../tmp_path"
    bad_path = tmp_path / ".." / tmp_path.name

    with pytest.raises(ValueError):
        logger.add_file(log_dir=str(bad_path))


def test_add_file_duplicate_detection(tmp_path):
    logger1 = AsyncSmartLogger("logger1")
    logger2 = AsyncSmartLogger("logger2")

    log_dir = str(tmp_path)
    logfile = "dup.log"

    # First logger registers the file
    logger1.add_file(log_dir=log_dir, logfile_name=logfile)

    # Second logger should raise ValueError due to FileHandlerRegistry
    with pytest.raises(ValueError):
        logger2.add_file(log_dir=log_dir, logfile_name=logfile)


def test_add_file_after_retire(tmp_path):
    logger = AsyncSmartLogger("test_file_retired")
    logger.retire()

    with pytest.raises(RuntimeError):
        logger.add_file(log_dir=str(tmp_path))


def test_add_file_with_rotation_logic(tmp_path):
    logger = AsyncSmartLogger("test_file_rotation")

    logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        timestamp=RotationTimestamp(0, 0, 0),
        maxBytes=100,
        backupCount=3,
    )

    logger.add_file(log_dir=str(tmp_path), rotation_logic=logic)

    handlers = logger._AsyncSmartLogger__py_logger.handlers
    assert len(handlers) == 1

    h = handlers[0]
    assert hasattr(h, "rotation_callback")
    assert h.rotation_callback == logger._AsyncSmartLogger__enqueue_rotation
