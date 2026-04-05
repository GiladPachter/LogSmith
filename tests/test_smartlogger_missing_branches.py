import logging
import pytest

from LogSmith.smartlogger import SmartLogger
from LogSmith.colors import CPrint
from LogSmith.level_registry import reset_levels_for_tests
from LogSmith.rotation_base import RotationLogic
from tests.helpers import isolated_logger


# ============================================================
# SAFETY GUARD: ensure audit is off before/after each test
# ============================================================
@pytest.fixture(autouse=True)
def cleanup_audit():
    SmartLogger.terminate_auditing()
    yield
    SmartLogger.terminate_auditing()


# ============================================================
# SAFETY GUARD: ensure level registry is reset
# ============================================================
@pytest.fixture(autouse=True)
def cleanup_levels():
    reset_levels_for_tests()
    yield
    reset_levels_for_tests()


# ============================================================
# 1. Caller resolution edge cases (230, 257, 261, 265, 269)
# ============================================================
def test_caller_resolution_edge(tmp_path):
    logger = isolated_logger("caller-edge")

    logger.add_file(str(tmp_path), "caller_edge.log")

    def helper():
        # Force logging module to appear in stack
        logging.getLogger("dummy").info("trigger")
        logger.info("hello")

    helper()

    text = (tmp_path / "caller_edge.log").read_text()
    assert "hello" in text


# ============================================================
# 2. Bleach edge cases (291, 322–325)
# ============================================================
def test_bleach_edge_cases():
    logger = isolated_logger("bleach-edge")

    class Buf:
        def __init__(self):
            self.data = []
        def write(self, s):
            self.data.append(s)
        def flush(self):
            pass
        def get(self):
            return "".join(self.data)

    buf = Buf()

    class Console(logging.StreamHandler):
        def __init__(self, stream):
            super().__init__()
            self.stream = stream

    handler = Console(buf)
    logger._SmartLogger__py_logger.addHandler(handler)

    # Ends with plain text while color_active=True
    msg = CPrint.colorize("RED", fg=CPrint.FG.RED) + "plain"
    logger.raw(msg)

    out = buf.get()
    assert "plain" in out


# ============================================================
# 3. Raw reopen failure path (388)
# ============================================================
def test_raw_reopen_failure(tmp_path):
    logger = isolated_logger("raw-fail2")

    class FakeFileHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.stream = None  # triggers the skip path
            # IMPORTANT: no baseFilename attribute

        def emit(self, record):
            pass  # never called

    handler = FakeFileHandler()
    logger._SmartLogger__py_logger.addHandler(handler)

    # Should skip handler silently (no exception)
    logger.raw("hello")

    # Nothing to assert — success is "no crash"


# ============================================================
# 4. Audit inactive path (450–456)
# ============================================================
def test_audit_inactive_path(tmp_path):
    SmartLogger.audit_everything(str(tmp_path), "audit_inactive.log")
    SmartLogger.terminate_auditing()  # disable but handler still exists

    logger = isolated_logger("audit-inactive")
    logger.info("x")  # should NOT write to audit file

    text = (tmp_path / "audit_inactive.log").read_text()
    assert "audit-inactive" not in text


# ============================================================
# 5. Duplicate handler unregister path (495, 499)
# ============================================================
def test_duplicate_handler_unregister(tmp_path):
    from LogSmith.file_registry import FileHandlerRegistry

    l1 = isolated_logger("dupA")
    l2 = isolated_logger("dupB")

    path = str(tmp_path / "dup.log")

    l1.add_file(str(tmp_path), "dup.log")

    # This raises BEFORE SmartLogger can unregister
    with pytest.raises(ValueError):
        l2.add_file(str(tmp_path), "dup.log")

    # Clean registry manually
    FileHandlerRegistry.unregister(path)

    # Now it should succeed
    l3 = isolated_logger("dupC")
    l3.add_file(str(tmp_path), "dup.log")


# ============================================================
# 6. Handler metadata: rotation None path (577)
# ============================================================
def test_handler_metadata_no_rotation(tmp_path):
    logger = isolated_logger("meta-norot")
    logger.add_file(str(tmp_path), "m.log", rotation_logic=None)

    info = logger.file_handlers[0]

    # Rotation metadata should exist but contain default values
    assert info["rotation"] == {
        "maxBytes": None,
        "when": None,
        "interval": None,
        "backupCount": 5,
    }


# ============================================================
# 7. OutputMode enum path (672→671, 700→699)
# ============================================================
def test_output_mode_enum(tmp_path):
    logger = isolated_logger("mode-enum")

    from LogSmith.formatter import OutputMode
    logger.add_console(output_mode=OutputMode.JSON)

    assert logger.console_handler["formatter"] == "json"


# ============================================================
# 8. PassthroughFormatter path (731, 733, 735, 742)
# ============================================================
def test_passthrough_formatter(tmp_path):
    logger = isolated_logger("passfmt")

    logger.add_file(
        str(tmp_path),
        "p.log",
        output_mode="plain",
        preserve_colors_in_log_files=True,
    )

    colored = CPrint.colorize("X", fg=CPrint.FG.RED)
    logger.info(colored)

    text = (tmp_path / "p.log").read_text()
    assert "\x1b[" in text  # ANSI preserved


# ============================================================
# 9. Retire deep guards (772, 796–821)
# ============================================================
def test_retire_deep_guards(tmp_path):
    logger = isolated_logger("retire-deep")
    logger.add_console()
    logger.add_file(str(tmp_path), "r.log")

    logger.retire()

    with pytest.raises(RuntimeError):
        logger.raw("x")

    with pytest.raises(RuntimeError):
        logger.add_file(str(tmp_path), "x.log")

    with pytest.raises(RuntimeError):
        logger.remove_console()


# ============================================================
# 10. Destroy deep cleanup (922–939)
# ============================================================
def test_destroy_deep_cleanup(tmp_path):
    logger = isolated_logger("destroy-deep")
    logger.add_console()
    logger.add_file(str(tmp_path), "d1.log")
    logger.add_file(str(tmp_path), "d2.log")

    SmartLogger.audit_everything(str(tmp_path), "audit_d.log")

    logger.destroy()
    logger.destroy()  # reentrant

    assert logger.handler_info == []


# ============================================================
# 11. Dynamic level safeguard paths (972–989)
# ============================================================
def test_dynamic_level_safeguards():
    # Duplicate name
    with pytest.raises(ValueError):
        SmartLogger.register_level("INFO", 60)

    # Duplicate numeric value
    with pytest.raises(ValueError):
        SmartLogger.register_level("NEWLVL", 20)

    # Negative numeric value
    with pytest.raises(ValueError):
        SmartLogger.register_level("NEG", -1)


# ============================================================
# 12. get_record minimal path (1008, 1021–1031)
# ============================================================
def test_get_record_minimal():
    rec = SmartLogger.get_record()

    # Timestamp is ALWAYS present
    assert isinstance(rec.timestamp, str)

    # No level because no log record was passed
    assert rec.level is None

    assert rec.exc_info is None # not inside "except:" block

    # stack_info is ALWAYS present (SmartLogger forces it)
    assert isinstance(rec.stack_info, str)
    assert "File" in rec.stack_info  # basic sanity check

    # Basic caller info should exist
    assert rec.file_name.endswith(".py")
    assert isinstance(rec.lineno, int)
    assert isinstance(rec.thread_id, int)
    assert isinstance(rec.process_id, int)


# ============================================================
# 13. Audit handler info rotation paths (1115–1145)
# ============================================================
def test_audit_handler_info_rotation(tmp_path):
    logic = RotationLogic(maxBytes=1, backupCount=1)

    # rotation_logic is accepted but not applied to audit handlers
    SmartLogger.audit_everything(str(tmp_path), "audit_rot.log", rotation_logic=logic)

    info = SmartLogger.audit_handler_info()

    # Audit handlers never expose rotation metadata
    assert info["rotation"] is None


# ============================================================
# 14. Output targets: file-only path (1180)
# ============================================================
def test_output_targets_file_only(tmp_path):
    logger = isolated_logger("targets-file")
    logger.add_file(str(tmp_path), "t.log")

    targets = logger.output_targets
    assert targets == [str((tmp_path / "t.log").resolve())]


# ============================================================
# 15. File handler metadata: rotation None (1195–1252)
# ============================================================
def test_file_handler_metadata_no_rotation(tmp_path):
    logger = isolated_logger("meta-norot2")
    logger.add_file(str(tmp_path), "m2.log", rotation_logic=None)

    info = logger.file_handlers[0]

    # SmartLogger always attaches default rotation metadata
    assert info["rotation"] == {
        "maxBytes": None,
        "when": None,
        "interval": None,
        "backupCount": 5,
    }


# ============================================================
# 16. Rotation logic pid/timestamp (1262–1284)
# ============================================================
def test_rotation_pid_timestamp(tmp_path):
    logic = RotationLogic(
        maxBytes=1,
        backupCount=1,
        append_filename_pid=True,
        append_filename_timestamp=True,
    )

    logger = isolated_logger("rot-pid-ts")
    logger.add_file(str(tmp_path), "rt.log", rotation_logic=logic)

    logger.info("hello")
    logger.info("world")

    handlers = logger.file_handlers
    assert handlers[0]["rotation"]["maxBytes"] == 1


# ============================================================
# 17. Destroy reentrancy (1316–1321)
# ============================================================
def test_destroy_reentrant(tmp_path):
    logger = isolated_logger("destroy-reent")
    logger.add_file(str(tmp_path), "dr.log")

    # Force reentrant destroy
    logger.destroy()
    logger.destroy()

    assert logger.handler_info == []


# ============================================================
# 18. Audit double-terminate (1339–1349)
# ============================================================
def test_audit_double_terminate(tmp_path):
    SmartLogger.audit_everything(str(tmp_path), "ad.log")
    SmartLogger.terminate_auditing()
    SmartLogger.terminate_auditing()  # second call should be safe

    assert SmartLogger.audit_handler_info() is None


def test_add_console_duplicate():
    from LogSmith.smartlogger import SmartLogger

    lg = SmartLogger("dup_console")
    lg.add_console()

    with pytest.raises(RuntimeError):
        lg.add_console()

    lg.destroy()


def test_invalid_separator():
    from LogSmith.formatter import LogRecordDetails

    with pytest.raises(ValueError):
        LogRecordDetails(separator="A")  # alphanumeric


def test_invalid_message_parts_order_timestamp():
    from LogSmith.formatter import LogRecordDetails, OptionalRecordFields

    orf = OptionalRecordFields(logger_name=True)
    with pytest.raises(ValueError):
        LogRecordDetails(optional_record_fields=orf, message_parts_order=["timestamp", "level", "logger_name"])


def test_invalid_logger_hierarchy():
    from LogSmith.smartlogger import SmartLogger

    with pytest.raises(RuntimeError):
        SmartLogger("parent.child")  # parent does not exist


def test_raw_writes_to_file_handler(tmp_path):
    from LogSmith.smartlogger import SmartLogger

    lg = SmartLogger("raw_file")
    lg.add_file(str(tmp_path), "x.log")

    lg.raw("\x1b[31mRED\x1b[0m", end="!")

    with open(tmp_path / "x.log", "r") as f:
        assert f.read() == "RED!"

    lg.destroy()


