# tests/test_smartlogger_from_demos/test_smartlogger_caller_resolution.py

import logging
from LogSmith import SmartLogger
from LogSmith.level_registry import reset_levels_for_tests
import pytest
from tests.helpers import isolated_logger


@pytest.fixture(autouse=True)
def cleanup_global_state():
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()
    yield
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()


def test_caller_resolution_deep_stack():
    logger = isolated_logger("caller.test")

    captured = {}

    # We will capture the caller info by intercepting LogRecord creation
    def spy_handle(record):
        captured["pathname"] = record.pathname.replace("\\", "/")
        captured["func"] = record.funcName
        captured["lineno"] = record.lineno

    # Monkeypatch the logger's handler to intercept records
    logger._SmartLogger__py_logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.emit = lambda record: spy_handle(record)
    logger._SmartLogger__py_logger.addHandler(handler)

    # Build a deep call stack
    def level1():
        return level2()

    def level2():
        return level3()

    def level3():
        return (lambda: level4())()

    def decorator(fn):
        def wrapper():
            return fn()
        return wrapper

    @decorator
    def level4():
        # This is the true caller we expect SmartLogger to detect
        logger.info("deep call")
        return True

    # Execute the nested call
    assert level1() is True

    # Now verify SmartLogger found level4() as the caller
    assert "test_smartlogger_caller_resolution" in captured["pathname"]
    assert captured["func"] == "level4"
    assert isinstance(captured["lineno"], int)
