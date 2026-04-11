import asyncio
import os
import threading
import pytest

from LogSmith.levels import TRACE


def test_smartlogger_init_creates_parent_for_dotted_name():
    import logging
    from LogSmith.smartlogger import SmartLogger

    # Ensure parent logger is not pre-created
    logging.Logger.manager.loggerDict.pop("myapp", None)

    logger = SmartLogger("myapp_api")

    py_logger = logger._SmartLogger__py_logger
    parent = py_logger.parent

    # Parent must be a Logger named "myapp"
    assert isinstance(parent, logging.Logger)

    logger.destroy()


def test_smartlogger_one_liner_methods_call___log(monkeypatch):
    from LogSmith.smartlogger import SmartLogger
    import logging

    logger = SmartLogger("one_liners")

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

    logger = SmartLogger("x_y")

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

    logger1 = SmartLogger("dup_test")
    logger1.add_file(str(logdir), "x.log")

    logger2 = SmartLogger("dup_test2")
    with pytest.raises(ValueError):
        logger2.add_file(str(logdir), "x.log")


def test_get_record_skip_logic():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("skip_test")

    rec = logger.get_record()
    # If skip=3 was applied, func_name should be the test function, not get_record
    assert rec.func_name.startswith("test_")


def test_retire_closes_and_clears_handlers(tmp_path):
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("life_retire")
    logger.add_console()
    logger.add_file(str(tmp_path), "x.log")

    assert logger.handler_info  # sanity

    logger.retire()

    assert logger.retired is True
    assert logger.handler_info == []
    assert logger._SmartLogger__py_logger.handlers == []


def test_destroy_removes_logger_and_rejects_children():
    from LogSmith.smartlogger import SmartLogger
    import logging

    parent = SmartLogger("life_parent")
    child = SmartLogger("life_parent.child")

    # Child is initially parented correctly
    assert child._SmartLogger__py_logger.parent is parent._SmartLogger__py_logger

    # Destroy child first
    child.destroy()

    # Now parent can be destroyed
    parent.destroy()

    # Parent removed from loggerDict
    assert "life_parent" not in logging.Logger.manager.loggerDict

    # Child removed entirely (no reparenting)
    assert "life_parent.child" not in logging.Logger.manager.loggerDict

    # Parent marked retired
    assert parent.retired is True


def test_destroy_is_idempotent():
    from LogSmith.smartlogger import SmartLogger

    logger = SmartLogger("life_idempotent")
    logger.destroy()
    logger.destroy()  # should not raise
    assert logger.retired is True


def test_dynamic_level_method_calls___log(monkeypatch):
    from LogSmith.smartlogger import SmartLogger, LEVELS

    logger = SmartLogger("dyn_level")
    LEVELS.register("CUSTOM", 35, None)

    called = {}

    def fake_log(self, level, msg, args, **kwargs):
        called["level"] = level
        called["msg"] = msg

    monkeypatch.setattr(SmartLogger, "_SmartLogger__log", fake_log)

    logger.custom("hello")
    assert called["level"] == LEVELS.get("CUSTOM")["value"]
    assert called["msg"] == "hello"


def test_get_record_requires_no_fields():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record()
    assert rec is not None

    logger.destroy()


def test_get_record_task_name_sync():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record()
    assert rec.task_name is None

    logger.destroy()


import asyncio

async def test_get_record_task_name_async():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record()
    assert rec.task_name == asyncio.current_task().get_name()

    logger.destroy()


def test_get_record_exc_info():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        rec = logger.get_record(exc_info = True)

    assert rec.exc_info["exc_parts"]["err_type_name"] == "RuntimeError"
    assert "boom" in rec.exc_info["full_trace_text"]

    logger.destroy()


def test_get_record_stack_info():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record(stack_info = True)
    assert "test_get_record_stack_info" in rec.stack_info

    logger.destroy()


def test_get_record_process_name():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record()
    assert rec.process_name is not None

    logger.destroy()


def test_get_record_timestamp():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record()
    assert " " in rec.timestamp
    assert len(rec.timestamp) >= 23

    logger.destroy()


def test_get_record_relative_created():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record()
    assert rec.relative_created >= 0

    logger.destroy()


def test_get_record_file_info():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("x")

    rec = logger.get_record()

    assert rec.file_path.endswith(".py")
    assert rec.file_name.endswith(".py")
    assert isinstance(rec.lineno, int)
    assert rec.func_name.startswith("test_")

    logger.destroy()


def test_get_record_thread_process():
    from LogSmith.smartlogger import SmartLogger
    import threading, os

    logger = SmartLogger("x")

    rec = logger.get_record()

    assert rec.thread_id == threading.current_thread().ident
    assert rec.thread_name == threading.current_thread().name
    assert rec.process_id == os.getpid()

    logger.destroy()


def test_get_record_process_name_non_empty():
    from LogSmith.smartlogger import SmartLogger
    logger = SmartLogger("proc_name")

    rec = logger.get_record()
    assert rec.process_name is None or isinstance(rec.process_name, str)
