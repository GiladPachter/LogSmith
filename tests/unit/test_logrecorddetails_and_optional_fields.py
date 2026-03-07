import re

from LogSmith import LogRecordDetails, OptionalRecordFields, SmartLogger, CPrint


def test_logrecorddetails_basic_configuration():
    details = LogRecordDetails(
        datefmt="%Y-%m-%d %H:%M:%S.%3f",
        separator="•",
        optional_record_fields=OptionalRecordFields(
            logger_name=True,
            file_name=True,
            lineno=True,
            func_name=True,
        ),
        message_parts_order=[
            "level",
            "logger_name",
            "file_name",
            "lineno",
            "func_name",
        ],
        color_all_log_record_fields=True,
    )

    assert details.datefmt == "%Y-%m-%d %H:%M:%S.%3f"
    assert details.separator == "•"
    assert details.optional_record_fields.logger_name is True
    assert details.optional_record_fields.file_name is True
    assert details.optional_record_fields.lineno is True
    assert details.optional_record_fields.func_name is True
    assert "level" in details.message_parts_order
    assert details.color_all_log_record_fields is True


def test_optionalrecordfields_toggles():
    opt = OptionalRecordFields(
        logger_name=True,
        file_path=False,
        file_name=True,
        lineno=False,
        func_name=True,
        thread_id=True,
        process_id=True,
    )

    assert opt.logger_name is True
    assert opt.file_path is False
    assert opt.file_name is True
    assert opt.lineno is False
    assert opt.func_name is True
    assert opt.thread_id is True
    assert opt.process_id is True


def test_logrecorddetails_used_by_console_output(capsys):
    levels = SmartLogger.levels()
    logger = SmartLogger("details.console", level=levels["TRACE"])

    details = LogRecordDetails(
        datefmt="%H:%M:%S",
        separator="|",
        optional_record_fields=OptionalRecordFields(
            logger_name=True,
            lineno=True,
        ),
        message_parts_order=[
            "level",
            "logger_name",
            "lineno",
        ],
        color_all_log_record_fields=False,
    )

    logger.add_console(log_record_details=details)
    logger.info("User login", username="Gilad")

    ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

    captured = capsys.readouterr().out
    clean_via_regex = ANSI_RE.sub("", captured)
    clean_via_cprint = CPrint.strip_ansi(captured)
    assert clean_via_regex == clean_via_cprint

    out = clean_via_cprint

    # basic structural expectations
    assert "INFO" in out
    assert "details.console" in out
    assert "User login" in out
    assert "username = 'Gilad'" in out
    assert "|" in out
    return
