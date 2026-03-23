import io
import os
import json
import logging
import pytest
from pathlib import Path

from LogSmith.smartlogger import SmartLogger
from LogSmith.level_registry import reset_levels_for_tests
from LogSmith.colors import CPrint


# ----------------------------------------------------------------------
# 1. Caller resolution (230, 257, 261, 265, 269)
# ----------------------------------------------------------------------
def helper_caller(logger):
    logger.info("hello from helper")
    return True


def test_caller_resolution(tmp_path):
    logger = SmartLogger("caller-test")
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    logger._SmartLogger__py_logger.addHandler(handler)

    helper_caller(logger)
    out = buf.getvalue()

    assert "hello from helper" in out


# ----------------------------------------------------------------------
# 2. ANSI bleaching (322–325, 341–347)
# ----------------------------------------------------------------------
def test_bleach_non_colored_text(tmp_path):
    # Use a unique logger name to avoid handler pollution
    logger = SmartLogger("bleach-test-unique")

    # Remove any handlers that SmartLogger or earlier tests may have attached
    for h in list(logger._SmartLogger__py_logger.handlers):
        logger._SmartLogger__py_logger.removeHandler(h)

    class UnclosableBuffer:
        def __init__(self):
            self.data = []
        def write(self, s):
            self.data.append(s)
        def flush(self):
            pass
        def getvalue(self):
            return "".join(self.data)
        def close(self):
            pass  # pytest cannot close this

    buf = UnclosableBuffer()

    class CustomConsoleHandler(logging.StreamHandler):
        def __init__(self, stream):
            super().__init__()
            self.stream = stream  # force SmartLogger to use this
        def close(self):
            pass

    handler = CustomConsoleHandler(buf)
    logger._SmartLogger__py_logger.addHandler(handler)

    colored_red = CPrint.colorize("RED", fg=CPrint.FG.RED) + " plain"
    msg = f"plain {colored_red} text"
    logger.raw(msg)

    out = buf.getvalue()
    assert "RED" in out
    assert CPrint.FG.CONSOLE_DEFAULT.split(";")[0] in out


# ----------------------------------------------------------------------
# 3. Raw logging edge case: stream=None (388)
# ----------------------------------------------------------------------
def test_raw_stream_none(tmp_path):
    logger = SmartLogger("raw-none")

    # Use a real FileHandler, not StreamHandler
    file_path = tmp_path / "x.log"
    handler = logging.FileHandler(file_path, mode="a")
    handler.stream = None  # force reopen path

    logger._SmartLogger__py_logger.addHandler(handler)

    logger.raw("hello")

    assert file_path.read_text().strip() == "hello"


# ----------------------------------------------------------------------
# 4. Audit logging (450–456, 464–465)
# ----------------------------------------------------------------------
def test_audit_logging(tmp_path):
    SmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
        rotation_logic=None,
        details=None,
    )

    logger = SmartLogger("audit-test")
    logger.info("audit me")

    SmartLogger.terminate_auditing()

    text = (tmp_path / "audit.log").read_text()
    assert "audit me" in text


# ----------------------------------------------------------------------
# 5. Duplicate file handler detection (495, 499)
# ----------------------------------------------------------------------
def test_duplicate_file_handler(tmp_path):
    logger1 = SmartLogger("dup1")
    logger2 = SmartLogger("dup2")

    logger1.add_file(str(tmp_path), "dup.log")

    with pytest.raises(ValueError):
        logger2.add_file(str(tmp_path), "dup.log")


# ----------------------------------------------------------------------
# 6. Handler metadata (577, 619–626)
# ----------------------------------------------------------------------
def test_handler_metadata(tmp_path):
    logger = SmartLogger("meta-test")
    logger.add_console()
    logger.add_file(str(tmp_path), "meta.log")

    info = logger.handler_info
    assert len(info) == 2
    assert info[0]["kind"] == "console"
    assert info[1]["kind"] == "file"


# ----------------------------------------------------------------------
# 7. Output mode normalization (672→671, 700→699)
# ----------------------------------------------------------------------
def test_output_mode_normalization(tmp_path):
    # 1. Invalid mode should raise ValueError BEFORE any console handler exists
    logger = SmartLogger("mode-test-invalid")
    with pytest.raises(ValueError):
        logger.add_console(output_mode="invalid-mode")

    # 2. Valid mode works
    logger = SmartLogger("mode-test-valid")
    logger.add_console(output_mode="json")
    info = logger.console_handler
    assert info["formatter"] == "json"

    # 3. Duplicate console handler should raise RuntimeError
    with pytest.raises(RuntimeError):
        logger.add_console(output_mode="ndjson")


# ----------------------------------------------------------------------
# 8. JSON / NDJSON / Passthrough formatters (710–717, 724–749)
# ----------------------------------------------------------------------
def test_json_formatter(tmp_path):
    logger = SmartLogger("json-test")
    logger.add_file(str(tmp_path), "json.log", output_mode="json")
    logger.info("hello json")

    text = (tmp_path / "json.log").read_text()
    data = json.loads(text)
    assert data["message"] == "hello json"


def test_ndjson_formatter(tmp_path):
    logger = SmartLogger("ndjson-test")
    logger.add_file(str(tmp_path), "ndjson.log", output_mode="ndjson")
    logger.info("hello ndjson")

    text = (tmp_path / "ndjson.log").read_text().strip()
    data = json.loads(text)
    assert data["message"] == "hello ndjson"


def test_passthrough_formatter(tmp_path):
    logger = SmartLogger("pass-test")
    logger.add_file(
        str(tmp_path),
        "pass.log",
        preserve_colors_in_log_files=True,
        output_mode="plain",
    )

    colored = CPrint.colorize("RED", fg=CPrint.FG.RED)
    logger.info(colored)

    text = (tmp_path / "pass.log").read_text()
    assert colored in text


# ----------------------------------------------------------------------
# 9. Retire logic (772, 781, 796–798, 802, 807, 809, 821)
# ----------------------------------------------------------------------
def test_retire_logic(tmp_path):
    logger = SmartLogger("retire-test")
    logger.add_console()

    logger.retire()

    with pytest.raises(RuntimeError):
        logger.info("nope")

    with pytest.raises(RuntimeError):
        logger.add_console()


# ----------------------------------------------------------------------
# 10. Audit handler info (879, 899)
# ----------------------------------------------------------------------
def test_audit_handler_info(tmp_path):
    SmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit2.log",
        rotation_logic=None,
        details=None,
    )

    info = SmartLogger.audit_handler_info()
    assert info is not None
    assert info["kind"] == "file"

    SmartLogger.terminate_auditing()


# ----------------------------------------------------------------------
# 11. Shutdown logic (922, 927, 932→exit, 939)
# ----------------------------------------------------------------------
def test_shutdown_logic(tmp_path):
    logger = SmartLogger("shutdown-test")
    logger.add_file(str(tmp_path), "shut.log")

    logger.destroy()
    logger.destroy()  # idempotent

    assert (tmp_path / "shut.log").exists()


# ----------------------------------------------------------------------
# 12. Dynamic level registration (972, 978–981, 986–989)
# ----------------------------------------------------------------------
def test_dynamic_level_registration(tmp_path):
    reset_levels_for_tests()
    SmartLogger.register_level("NOTICE", 25)

    logger = SmartLogger("dyn-test")
    logger.add_file(str(tmp_path), "dyn.log")

    logger.notice("dynamic works")
    text = (tmp_path / "dyn.log").read_text()

    assert "dynamic works" in text


# ----------------------------------------------------------------------
# 13. Record building (1008, 1021–1024, 1031, 1035)
# ----------------------------------------------------------------------
def test_get_record():
    rec = SmartLogger.get_record()
    assert rec.file_name.endswith(".py")
    assert rec.func_name is not None
    assert rec.process_id == os.getpid()
    assert rec.stack_info is not None


# ----------------------------------------------------------------------
# 14. Formatter metadata (1112–1252, 1258–1284)
# ----------------------------------------------------------------------
def test_formatter_metadata(tmp_path):
    logger = SmartLogger("meta2-test")
    logger.add_file(str(tmp_path), "meta2.log", output_mode="json")
    logger.add_file(str(tmp_path), "meta3.log", output_mode="ndjson")
    logger.add_file(str(tmp_path), "meta4.log", output_mode="plain")

    info = logger.file_handlers
    assert len(info) == 3
    assert info[0]["formatter"] == "json"
    assert info[1]["formatter"] == "ndjson"
    assert info[2]["formatter"] == "plain"


# ----------------------------------------------------------------------
# 15. Output targets (1316–1321)
# ----------------------------------------------------------------------
def test_output_targets(tmp_path):
    logger = SmartLogger("targets-test")
    logger.add_console()
    logger.add_file(str(tmp_path), "t.log")

    targets = logger.output_targets
    assert "console" in targets
    assert any(t.endswith("t.log") for t in targets)


# ----------------------------------------------------------------------
# 16. Error branches (1339–1349, 1362–1373)
# ----------------------------------------------------------------------
def test_invalid_output_mode():
    logger = SmartLogger("err-test")
    with pytest.raises(ValueError):
        logger.add_console(output_mode="invalid-mode")


def test_invalid_level_registration():
    reset_levels_for_tests()
    with pytest.raises(ValueError):
        SmartLogger.register_level("bad name", 50)


# ----------------------------------------------------------------------
# 17. Fallback branches
# ----------------------------------------------------------------------
