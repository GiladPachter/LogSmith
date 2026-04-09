import pytest

from LogSmith import SmartLogger, AsyncSmartLogger, OutputMode, LogRecordDetails, OptionalRecordFields, CPrint
from LogSmith.levels import TRACE


def test_smartlogger_file_logging_with_full_details(tmp_path):
    log_file = tmp_path / "smart_full_details.log"
    if log_file.exists():
        log_file.unlink()

    logger = SmartLogger("smart_full_details")
    logger.add_file(str(tmp_path), "smart_full_details.log",
                    TRACE,
                    LogRecordDetails(optional_record_fields = OptionalRecordFields(relative_created=True,
                                                                                   logger_name=True,
                                                                                   file_path=True,
                                                                                   file_name=True,
                                                                                   lineno=True,
                                                                                   func_name=True,
                                                                                   thread_id=True,
                                                                                   thread_name=True,
                                                                                   task_name=True,
                                                                                   process_id=True,
                                                                                   process_name=True,
                                                                                   stack_info=True,
                                                                                   exc_info=True,),
                                     message_parts_order =["relative_created",
                                                           "logger_name",
                                                           "file_path",
                                                           "file_name",
                                                           "lineno",
                                                           "func_name",
                                                           "thread_id",
                                                           "thread_name",
                                                           "task_name",
                                                           "process_id",
                                                           "process_name",
                                                           "level",
                                                           ],
                                     color_all_log_record_fields = True
                                     ),
                    preserve_colors_in_log_files = True,
                    output_mode = OutputMode.COLOR,
                    ),

    colored = [
        CPrint.colorize("RAW",      fg=CPrint.FG.BRIGHT_RED),
        CPrint.colorize("text",     fg=CPrint.FG.ORANGE),
        CPrint.colorize("rocks",    fg=CPrint.FG.BRIGHT_YELLOW),
        CPrint.colorize("in",       fg=CPrint.FG.BRIGHT_GREEN),
        CPrint.colorize("multiple", fg=CPrint.FG.BRIGHT_BLUE),
        CPrint.colorize("colors",   fg=CPrint.FG.SOFT_PURPLE)
    ]

    logger.info(" ".join(colored), stack_info=True, exc_info=True)

    logger.destroy()

    # Verify file exists
    assert log_file.exists()

    content = log_file.read_text(encoding="utf-8")

    # Message must appear
    assert "RAW"      in content
    assert "text"     in content
    assert "rocks"    in content
    assert "in"       in content
    assert "multiple" in content
    assert "colors"   in content

    # ANSI color codes must appear (preserved colors)
    assert "\x1b[" in content

    # Optional fields must appear
    assert "INFO" in content
    assert "smart_full_details" in content
    assert ".py" in content or "line" in content or "function" in content


@pytest.mark.asyncio
async def test_asyncsmartlogger_file_logging_with_full_details(tmp_path):
    log_file = tmp_path / "smart_full_details.log"
    if log_file.exists():
        log_file.unlink()

    logger = AsyncSmartLogger("smart_full_details_async")
    logger.add_file(str(tmp_path), "smart_full_details.log",
                    TRACE,
                    LogRecordDetails(optional_record_fields = OptionalRecordFields(relative_created=True,
                                                                                   logger_name=True,
                                                                                   file_path=True,
                                                                                   file_name=True,
                                                                                   lineno=True,
                                                                                   func_name=True,
                                                                                   thread_id=True,
                                                                                   thread_name=True,
                                                                                   task_name=True,
                                                                                   process_id=True,
                                                                                   process_name=True,
                                                                                   stack_info=True,
                                                                                   exc_info=True,),
                                     message_parts_order =["relative_created",
                                                           "logger_name",
                                                           "file_path",
                                                           "file_name",
                                                           "lineno",
                                                           "func_name",
                                                           "thread_id",
                                                           "thread_name",
                                                           "task_name",
                                                           "process_id",
                                                           "process_name",
                                                           "level",
                                                           ],
                                     color_all_log_record_fields = True
                                     ),
                    preserve_colors_in_log_files = True,
                    output_mode = OutputMode.COLOR,
                    ),

    colored = [
        CPrint.colorize("RAW",      fg=CPrint.FG.BRIGHT_RED),
        CPrint.colorize("text",     fg=CPrint.FG.ORANGE),
        CPrint.colorize("rocks",    fg=CPrint.FG.BRIGHT_YELLOW),
        CPrint.colorize("in",       fg=CPrint.FG.BRIGHT_GREEN),
        CPrint.colorize("multiple", fg=CPrint.FG.BRIGHT_BLUE),
        CPrint.colorize("colors",   fg=CPrint.FG.SOFT_PURPLE)
    ]

    await logger.a_info(" ".join(colored), stack_info=True, exc_info=True)

    await logger.flush()

    logger.destroy()

    # Verify file exists
    assert log_file.exists()

    content = log_file.read_text(encoding="utf-8")

    # Message must appear
    assert "RAW"      in content
    assert "text"     in content
    assert "rocks"    in content
    assert "in"       in content
    assert "multiple" in content
    assert "colors"   in content

    # ANSI color codes must appear (preserved colors)
    assert "\x1b[" in content

    # Optional fields must appear
    assert "INFO" in content
    assert "smart_full_details_async" in content
    assert ".py" in content or "line" in content or "function" in content
