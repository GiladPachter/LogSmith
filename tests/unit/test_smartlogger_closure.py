import logging
import pytest

from LogSmith.smartlogger import SmartLogger
from LogSmith.level_registry import reset_levels_for_tests
from LogSmith.rotation_base import RotationLogic
from LogSmith.colors import CPrint


# ---------------------------------------------------------------------------
# 1. CALLER RESOLUTION
# ---------------------------------------------------------------------------
def test_caller_resolution(tmp_path):
    logger = SmartLogger("caller-test")
    logger.add_file(str(tmp_path), "caller.log")

    def helper():
        logger.info("hello")

    helper()
    text = (tmp_path / "caller.log").read_text(encoding="utf-8")
    assert "hell" in text


# ---------------------------------------------------------------------------
# 2. BLEACH NON-COLORED TEXT (console raw)
# ---------------------------------------------------------------------------
def test_console_bleach(tmp_path, capsys):
    logger = SmartLogger("bleach-test")
    logger.add_console()

    red = CPrint.colorize("RED", fg=CPrint.FG.RED)
    logger.raw("plain " + red)

    out = capsys.readouterr().out
    assert "RED" in out
    assert "plain" in out
    assert "\x1b" in out  # colored


# ---------------------------------------------------------------------------
# 3. RAW FILE REOPEN (stream=None)
# ---------------------------------------------------------------------------
def test_raw_file_reopen(tmp_path):
    logger = SmartLogger("raw-reopen")
    path = tmp_path / "x.log"

    handler = logging.FileHandler(path)
    handler.stream = None
    logger._SmartLogger__py_logger.addHandler(handler)

    logger.raw("hello")
    assert path.read_text().strip() == "hello"


# ---------------------------------------------------------------------------
# 4. AUDIT LOGGING
# ---------------------------------------------------------------------------
def test_audit_logging(tmp_path):
    SmartLogger.audit_everything(str(tmp_path), "audit.log")
    logger = SmartLogger("audit-test")
    logger.info("x")
    SmartLogger.terminate_auditing()

    info = SmartLogger.audit_handler_info()
    assert info is None  # audit disabled now

    text = (tmp_path / "audit.log").read_text()
    assert "audit-test" in text


# ---------------------------------------------------------------------------
# 5. DUPLICATE FILE HANDLER DETECTION
# ---------------------------------------------------------------------------
def test_duplicate_file_handler(tmp_path):
    l1 = SmartLogger("dup1")
    l2 = SmartLogger("dup2")

    l1.add_file(str(tmp_path), "x.log")
    with pytest.raises(ValueError):
        l2.add_file(str(tmp_path), "x.log")


# ---------------------------------------------------------------------------
# 6. HANDLER METADATA
# ---------------------------------------------------------------------------
def test_handler_metadata(tmp_path):
    logger = SmartLogger("meta-test")
    logger.add_console()
    logger.add_file(str(tmp_path), "m.log")

    info = logger.handler_info
    assert len(info) == 2
    assert logger.console_handler is not None
    assert len(logger.file_handlers) == 1


# ---------------------------------------------------------------------------
# 7. OUTPUT MODE NORMALIZATION
# ---------------------------------------------------------------------------
def test_output_mode_normalization(tmp_path):
    logger = SmartLogger("mode-test")

    with pytest.raises(ValueError):
        logger.add_console(output_mode="invalid")

    logger.add_console(output_mode="json")
    assert logger.console_handler["formatter"] == "json"


# ---------------------------------------------------------------------------
# 8. FORMATTER SELECTION (JSON, NDJSON, plain, passthrough)
# ---------------------------------------------------------------------------
def test_formatter_selection(tmp_path):
    logger = SmartLogger("fmt-test")

    logger.add_console(output_mode="json")
    logger.add_file(str(tmp_path), "a.json", output_mode="json")
    logger.add_file(str(tmp_path), "b.ndjson", output_mode="ndjson")
    logger.add_file(str(tmp_path), "c.txt", output_mode="plain")
    logger.add_file(str(tmp_path), "d.pass", output_mode="plain",
                    do_not_sanitize_colors_from_string=True)

    logger.info("hello")

    assert (tmp_path / "a.json").read_text().strip().startswith("{")
    assert (tmp_path / "b.ndjson").read_text().strip().startswith("{")
    assert "hello" in (tmp_path / "c.txt").read_text()
    assert "hello" in (tmp_path / "d.pass").read_text()


# ---------------------------------------------------------------------------
# 9. RETIRE LOGIC
# ---------------------------------------------------------------------------
def test_retire_logic(tmp_path):
    logger = SmartLogger("retire-test")
    logger.add_console()
    logger.retire()

    with pytest.raises(RuntimeError):
        logger.info("x")

    with pytest.raises(RuntimeError):
        logger.add_console()


# ---------------------------------------------------------------------------
# 10. DESTROY LOGIC
# ---------------------------------------------------------------------------
def test_destroy_logic(tmp_path):
    logger = SmartLogger("destroy-test")
    logger.add_file(str(tmp_path), "d.log")

    logger.destroy()
    logger.destroy()  # idempotent

    assert logger.handler_info == []


# ---------------------------------------------------------------------------
# 11. DYNAMIC LEVEL REGISTRATION
# ---------------------------------------------------------------------------
def test_dynamic_level_registration(tmp_path):
    reset_levels_for_tests()
    SmartLogger.register_level("NOTICE", 25)

    logger = SmartLogger("dyn-test")
    logger.add_file(str(tmp_path), "dyn.log")

    logger.notice("hello")
    assert "hello" in (tmp_path / "dyn.log").read_text()


# ---------------------------------------------------------------------------
# 12. GET_RECORD
# ---------------------------------------------------------------------------
def test_get_record():
    rec = SmartLogger.get_record()
    assert rec.file_name
    assert rec.func_name
    assert rec.process_id
    assert rec.stack_info


# ---------------------------------------------------------------------------
# 13. OUTPUT TARGETS
# ---------------------------------------------------------------------------
def test_output_targets(tmp_path):
    logger = SmartLogger("targets-test")
    logger.add_console()
    logger.add_file(str(tmp_path), "t.log")

    targets = logger.output_targets
    assert "console" in targets
    assert any("t.log" in t for t in targets)


# ---------------------------------------------------------------------------
# 14. ROTATING FILE HANDLER METADATA
# ---------------------------------------------------------------------------
def test_rotating_file_metadata(tmp_path):
    logger = SmartLogger("rotate-meta")

    logic = RotationLogic(maxBytes=1, backupCount=1)
    logger.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    logger.info("hello")
    logger.info("world")  # force rotation

    handlers = logger.file_handlers
    assert handlers[0]["rotation"]["maxBytes"] == 1
    assert handlers[0]["rotation"]["backupCount"] == 1
