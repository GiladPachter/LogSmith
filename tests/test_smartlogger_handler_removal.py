import logging
from LogSmith import SmartLogger

def test_remove_console(tmp_path):
    logger = SmartLogger("rmconsole", logging.INFO)
    logger.add_console()

    assert logger.console_handler is not None
    logger.remove_console()
    assert logger.console_handler is None

def test_remove_file_handler(tmp_path):
    logger = SmartLogger("rmfile", logging.INFO)
    logger.add_file(str(tmp_path), "x.log")

    assert len(logger.file_handlers) == 1
    logger.remove_file_handler("x.log", str(tmp_path))
    assert len(logger.file_handlers) == 0
