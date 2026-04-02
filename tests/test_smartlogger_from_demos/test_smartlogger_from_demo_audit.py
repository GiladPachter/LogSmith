# tests/test_smartlogger_from_demo_audit.py

import logging
import pytest

from LogSmith import SmartLogger
from LogSmith import RotationLogic, When
from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith.level_registry import reset_levels_for_tests


@pytest.fixture(autouse=True)
def cleanup_global_state():
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()
    yield
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()


def test_audit_enable_disable_reenable(tmp_path):
    # Prepare audit directory
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()

    # Create a logger with a console handler
    lg = SmartLogger("audit_demo", level=logging.INFO)
    lg.add_console(level=logging.INFO)

    # Enable auditing
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(
            logger_name=True,
            lineno=True,
        ),
        message_parts_order=["level", "logger_name", "lineno"],
    )

    rotation = RotationLogic(
        maxBytes=3000,
        when=When.SECOND,
        interval=1,
        backupCount=5,
    )

    SmartLogger.audit_everything(
        log_dir=str(audit_dir),
        logfile_name="audit.log",
        rotation_logic=rotation,
        details=details,
    )

    # Audit should now be active
    info = SmartLogger.audit_handler_info()
    assert info is not None
    assert info["kind"] == "file"
    assert info["formatter"] == "plain"  # default for audit
    assert info["rotation"] is None

    # Log something
    lg.info("hello audit")

    # Disable auditing
    SmartLogger.terminate_auditing()
    info2 = SmartLogger.audit_handler_info()
    assert info2 is None

    # Re-enable auditing (tests branch where handler existed before)
    SmartLogger.audit_everything(
        log_dir=str(audit_dir),
        logfile_name="audit2.log",
        rotation_logic=None,  # no rotation this time
        details=details,
    )

    info3 = SmartLogger.audit_handler_info()
    assert info3 is not None
    assert info3["rotation"] is None  # rotation_logic=None → no rotation metadata

    # Log again
    lg.warning("audit re-enabled")

    # Disable again (tests reentrant terminate)
    SmartLogger.terminate_auditing()
    assert SmartLogger.audit_handler_info() is None
