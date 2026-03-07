import re
from pathlib import Path

from LogSmith import SmartLogger, OutputMode, LogRecordDetails, OptionalRecordFields, CPrint


def test_basic_console_logging(capsys):
    levels = SmartLogger.levels()
    logger = SmartLogger("core.console", level=levels["TRACE"])
    logger.add_console()

    logger.trace("trace message")
    logger.debug("debug message")
    logger.info("info message")

    out = capsys.readouterr().out
    assert "trace message" in out
    assert "debug message" in out
    assert "info message" in out


def test_file_logging_plain(tmp_path: Path):
    levels = SmartLogger.levels()
    logger = SmartLogger("core.file", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="app.log",
        output_mode=OutputMode.PLAIN,
    )

    logger.info("hello file", user="gilad")

    logfile = log_dir / "app.log"
    assert logfile.exists()

    content = logfile.read_text(encoding="utf-8")
    assert "hello file" in content
    assert "user='gilad'" in content


def test_raw_output_bypasses_formatting(capsys):
    levels = SmartLogger.levels()
    logger = SmartLogger("core.raw", level=levels["TRACE"])
    logger.add_console()

    logger.raw("RAW LINE")

    # out = capsys.readouterr().out.strip()

    ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

    captured = capsys.readouterr().out.strip()
    clean_via_regex = ANSI_RE.sub("", captured)
    clean_via_cprint = CPrint.strip_ansi(captured)
    assert clean_via_regex == clean_via_cprint

    out = clean_via_cprint

    # raw output should not include level or timestamp
    assert out == "RAW LINE"


def test_structured_fields_in_console_and_file(tmp_path, capsys):
    levels = SmartLogger.levels()
    logger = SmartLogger("core.struct", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add_console()
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="struct.log",
        output_mode=OutputMode.PLAIN,
    )

    logger.info("User login", username="Gilad", action="login")

    ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

    captured = capsys.readouterr().out
    clean_via_regex = ANSI_RE.sub("", captured)
    clean_via_cprint = CPrint.strip_ansi(captured)
    assert clean_via_regex == clean_via_cprint

    out = clean_via_cprint

    assert "User login" in out
    assert "username = 'Gilad'" in out      # content spaced out for readability

    content = (log_dir / "struct.log").read_text(encoding="utf-8")
    assert "User login" in content
    assert "username='Gilad'" in content    # content condensed for preserving disk space


def test_custom_logrecorddetails_for_file(tmp_path: Path):
    levels = SmartLogger.levels()
    logger = SmartLogger("core.details.file", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    details = LogRecordDetails(
        datefmt="%H:%M:%S",
        separator="|",
        optional_record_fields=OptionalRecordFields(
            logger_name=True,
            process_id=True,
        ),
        message_parts_order=[
            "level",
            "logger_name",
            "process_id",
        ],
    )

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="details.log",
        output_mode=OutputMode.PLAIN,
        log_record_details=details,
    )

    logger.info("hello", x=1)

    content = (log_dir / "details.log").read_text(encoding="utf-8")
    assert "core.details.file" in content
    assert "hello" in content
    assert "x=1" in content
