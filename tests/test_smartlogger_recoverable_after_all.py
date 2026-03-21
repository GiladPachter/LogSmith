import os
import threading

import pytest

from LogSmith.levels import TRACE


def test_smartlogger_init_creates_parent_for_dotted_name():
    import logging
    from LogSmith.smartlogger import SmartLogger

    # Ensure parent logger is not pre-created
    logging.Logger.manager.loggerDict.pop("myapp", None)

    logger = SmartLogger("myapp.api")

    py_logger = logger._SmartLogger__py_logger
    parent = py_logger.parent

    # Parent must be a Logger named "myapp"
    assert isinstance(parent, logging.Logger)


def test_smartlogger_one_liner_methods_call___log(monkeypatch):
    from LogSmith.smartlogger import SmartLogger
    import logging

    logger = SmartLogger("one.liners")

    called = []

    def fake_log(self, level, msg, args, **kwargs):
        called.append((level, msg))

    monkeypatch.setattr(SmartLogger, "_SmartLogger__log", fake_log)

    logger.trace("t")
    logger.debug("d")
    logger.info("i")
    logger.warning("w")
    logger.error("e")
    logger.critical("c")

    levels = [c[0] for c in called]
    assert logging.DEBUG in levels
    assert logging.INFO in levels
    assert logging.WARNING in levels
    assert logging.ERROR in levels
    assert logging.CRITICAL in levels
    # and your TRACE constant if you want to assert that too


def test_one_liner_wrappers(monkeypatch):
    from LogSmith.smartlogger import SmartLogger
    import logging

    logger = SmartLogger("x.y")

    calls = []

    def fake_log(self, level, msg, args, **kwargs):
        calls.append(level)

    monkeypatch.setattr(SmartLogger, "_SmartLogger__log", fake_log)

    logger.trace("t")
    logger.debug("d")
    logger.info("i")
    logger.warning("w")
    logger.error("e")
    logger.critical("c")

    assert logging.DEBUG in calls
    assert logging.INFO in calls
    assert logging.WARNING in calls
    assert logging.ERROR in calls
    assert logging.CRITICAL in calls
    assert any(level == TRACE for level in calls)


def test_add_file_duplicate_detection(tmp_path):
    from LogSmith import SmartLogger
    logdir = tmp_path / "logs"
    logdir.mkdir()

    logger1 = SmartLogger("dup.test")
    logger1.add_file(str(logdir), "x.log")

    logger2 = SmartLogger("dup.test2")
    with pytest.raises(ValueError):
        logger2.add_file(str(logdir), "x.log")


def test_get_record_skip_logic():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("skip.test")

    rec = logger.get_record()
    # If skip=3 was applied, func_name should be the test function, not get_record
    assert rec.func_name.startswith("test_")


def test_get_record_parts_requires_fields():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    with pytest.raises(ValueError):
        logger.get_record_parts()


def test_get_record_parts_task_name_sync():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")
    rec = logger.get_record_parts(task_name=True)
    assert rec.task_name is None


import asyncio

async def test_get_record_parts_task_name_async():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")
    rec = logger.get_record_parts(task_name=True)
    assert rec.task_name == asyncio.current_task().get_name()


def test_get_record_parts_exc_info():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        rec = logger.get_record_parts(exc_info=True)

    assert rec.exc_info["exc_parts"]["err_type_name"] == "RuntimeError"
    assert "boom" in rec.exc_info["full_trace_text"]


def test_get_record_parts_stack_info():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record_parts(stack_info=True)
    assert "test_get_record_parts_stack_info" in rec.stack_info


def test_get_record_parts_process_name():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record_parts(process_name=True)
    assert rec.process_name is not None


def test_get_record_parts_timestamp():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record_parts(timestamp=True)
    assert " " in rec.timestamp  # space instead of T
    assert len(rec.timestamp) >= 23  # yyyy-mm-dd hh:mm:ss.mmm


def test_get_record_parts_relative_created():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record_parts(relative_created=True)
    assert rec.relative_created >= 0


def test_get_record_parts_file_info():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record_parts(file_path=True, file_name=True, lineno=True, func_name=True)

    assert rec.file_path.endswith(".py")
    assert rec.file_name.endswith(".py")
    assert isinstance(rec.lineno, int)
    assert rec.func_name.startswith("test_")


def test_get_record_parts_thread_process():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record_parts(thread_id=True, thread_name=True, process_id=True)

    assert rec.thread_id == threading.current_thread().ident
    assert rec.thread_name == threading.current_thread().name
    assert rec.process_id == os.getpid()


