import time
from pathlib import Path

from LogSmith import CPrint, LogRecordDetails, OptionalRecordFields, RotationLogic
from LogSmith.smartlogger import SmartLogger
from tests.helpers import read_file


# ---------------------------------------------------------
# Basic Logging Tests
# ---------------------------------------------------------

def test_info_to_console(logger, capsys):
    logger.add_console()
    logger.info("hello world")

    out = capsys.readouterr().out
    assert "hello world" in out
    assert "INFO" in out


def test_info_to_file(logger, tmp_log_dir):
    path = tmp_log_dir / "log.txt"
    logger.add_file(tmp_log_dir.__str__(), "log.txt")
    logger.info("hello file")
    text = read_file(path)
    assert "hello file" in text
    assert "INFO" in text


# ---------------------------------------------------------
# Raw Logging Tests
# ---------------------------------------------------------

def test_raw_console(logger, capsys):
    logger.add_console()
    logger.raw("RAW")
    out = capsys.readouterr().out
    stripped = CPrint.strip_ansi(out).strip()
    assert "RAW" in stripped
    assert stripped == "RAW"


def test_raw_file(logger, tmp_log_dir):
    path = tmp_log_dir / "raw.txt"
    logger.add_file(tmp_log_dir.__str__(), "raw.txt")
    logger.raw("RAW")
    assert read_file(path).strip() == "RAW"


# ---------------------------------------------------------
# Handler Management Tests
# ---------------------------------------------------------

def test_add_remove_console(logger, capsys):
    logger.add_console()
    logger.remove_console()
    logger.info("hello")
    out = capsys.readouterr().out
    assert out == ""


def test_add_remove_file(logger, tmp_log_dir):
    path = tmp_log_dir / "x.log"
    logger.add_file(tmp_log_dir.__str__(), "x.log")
    logger.remove_file_handler("x.log", tmp_log_dir.__str__())
    logger.info("hello")
    assert read_file(path) == ""


# ---------------------------------------------------------
# Diagnostics Tests
# ---------------------------------------------------------

def test_exc_info(logger, capsys):
    logger.add_console(
        log_record_details = LogRecordDetails(
            optional_record_fields = OptionalRecordFields(
                exc_info=True
            )
        )
    )
    try:
        1 / 0
    except ZeroDivisionError:
        logger.error("boom", exc_info=True)

    out = capsys.readouterr().out
    assert "ZeroDivisionError" in out
    assert "boom" in out


def test_stack_info(logger, capsys):
    logger.add_console(
        log_record_details = LogRecordDetails(
            optional_record_fields = OptionalRecordFields(
                stack_info = True
            )
        )
    )
    logger.info("stack", stack_info=True)
    out = capsys.readouterr().out
    assert "File" in out
    assert "stack" in out


def test_extras(logger, capsys):
    logger.add_console()
    logger.info("msg", user="gilad", action="test")
    out = capsys.readouterr().out
    assert "gilad" in out
    assert "test" in out


def test_message_parts_order(logger, capsys):
    logger.add_console(log_record_details=LogRecordDetails(
        datefmt="%Y-%m-%d %H:%M:%S.%2f",   # milliseconds
        separator="•",
        optional_record_fields=OptionalRecordFields(
            file_name=True,
            func_name=True,
        ),
        message_parts_order=[
            "func_name",
            "file_name",
            "level",        # colored by level style
            # "message",    # colored by level style
        ],
        color_all_log_record_fields=False,  # only level + message are colored
    ))

    logger.info("hello")
    out = capsys.readouterr().out
    assert out.index("test_message_parts_order") < out.index("test_smartlogger.py")


# ---------------------------------------------------------
# Audit Mode Tests
# ---------------------------------------------------------

def test_audit_mode(tmp_path, logger):
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()

    # enable audit mode using the real API
    logger.audit_everything(
        log_dir=str(audit_dir),
        logfile_name="audit.log"
    )

    logger.info("hello")
    logger.terminate_auditing()

    # read the audit file
    audit_file = audit_dir / "audit.log"
    lines = audit_file.read_text().splitlines()

    assert len(lines) == 1
    assert "hello" in lines[0]


# ---------------------------------------------------------
# Rotation Integration Tests
# ---------------------------------------------------------

def test_size_rotation(logger, tmp_log_dir):
    path = tmp_log_dir / "rot.log"
    logger.add_file(
        tmp_log_dir.__str__(),
        "rot.log",
        rotation_logic = RotationLogic(
            maxBytes=2000,     # rotate when file exceeds ~2 KB
            backupCount=5,
        )
    )

    for i in range(10):
        logger.info("x" * 50)

    files = list(tmp_log_dir.iterdir())
    assert len(files) >= 2
