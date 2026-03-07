from pathlib import Path

ROOT = Path("..").resolve()

UNIT_TEST_FILES = {
    "tests/unit/test_levels_and_dynamic.py": """\
import pytest

from LogSmith import SmartLogger, AsyncSmartLogger, LevelStyle, CPrint


def test_levels_contains_core_levels():
    levels = SmartLogger.levels()
    for name in ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        assert name in levels
        assert isinstance(levels[name], int)


def test_register_dynamic_level_creates_method_and_value_unique():
    levels_before = SmartLogger.levels()
    assert "NOTICE" not in levels_before

    SmartLogger.register_level(name="NOTICE", value=25)
    levels_after = SmartLogger.levels()

    assert "NOTICE" in levels_after
    assert levels_after["NOTICE"] == 25

    logger = SmartLogger("dynamic.level.test", level=levels_after["TRACE"])
    logger.add_console()

    # dynamic method should exist
    assert hasattr(logger, "notice")

    # calling it should not raise
    logger.notice("dynamic level works")


def test_register_dynamic_level_with_style_and_theme_integration():
    SmartLogger.register_level(
        name="SECURITY",
        value=45,
        style=LevelStyle(fg=CPrint.FG.BRIGHT_RED, intensity=CPrint.Intensity.BOLD),
    )

    levels = SmartLogger.levels()
    assert "SECURITY" in levels

    logger = SmartLogger("security.logger", level=levels["TRACE"])
    logger.add_console()

    # method exists
    assert hasattr(logger, "security")
    logger.security("security event", user="gilad")


@pytest.mark.asyncio
async def test_async_dynamic_level_registration_and_method():
    AsyncSmartLogger.register_level("SUCCESS", 35)
    levels = AsyncSmartLogger.levels()
    assert "SUCCESS" in levels

    logger = AsyncSmartLogger("async.dynamic", level=levels["TRACE"])
    logger.add_console()

    assert hasattr(logger, "a_success")
    await logger.a_success("async success")
    await logger.flush()
""",

    "tests/unit/test_logrecorddetails_and_optional_fields.py": """\
from LogSmith import LogRecordDetails, OptionalRecordFields, SmartLogger


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

    out = capsys.readouterr().out.strip()
    # basic structural expectations
    assert "INFO" in out
    assert "details.console" in out
    assert "User login" in out
    assert "username = 'Gilad'" in out
    assert "|" in out
""",

    "tests/unit/test_output_modes_json_ndjson.py": """\
import json
from pathlib import Path

from LogSmith import SmartLogger, OutputMode, LogRecordDetails, OptionalRecordFields


def test_console_json_output_structure(capsys):
    levels = SmartLogger.levels()
    logger = SmartLogger("json.console", level=levels["TRACE"])

    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(
            logger_name=True,
            file_name=True,
            lineno=True,
        )
    )

    logger.add_console(
        output_mode=OutputMode.JSON,
        log_record_details=details,
    )

    logger.info("User login", username="Gilad", action="login")
    out = capsys.readouterr().out.strip()
    data = json.loads(out)

    assert data["level"] == "INFO"
    assert data["logger"] == "json.console"
    assert data["message"] == "User login"
    assert data["fields"]["username"] == "Gilad"
    assert data["fields"]["action"] == "login"
    assert "file" in data
    assert "line" in data


def test_file_ndjson_output(tmp_path: Path):
    levels = SmartLogger.levels()
    logger = SmartLogger("ndjson.file", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="events.ndjson",
        output_mode=OutputMode.NDJSON,
    )

    logger.info("User login", username="Gilad", action="login")
    logger.warning("Something odd", code=123)

    logfile = log_dir / "events.ndjson"
    assert logfile.exists()

    lines = logfile.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["level"] == "INFO"
    assert first["message"] == "User login"
    assert first["fields"]["username"] == "Gilad"

    assert second["level"] == "WARNING"
    assert second["fields"]["code"] == 123
""",

    "tests/unit/test_cprint_and_themes.py": """\
import re

from LogSmith import CPrint, SmartLogger, DARK_THEME, LevelStyle


ANSI_PATTERN = re.compile(r"\\x1b\\[[0-9;]*m")


def test_cprint_colorize_adds_ansi_and_strip_removes():
    text = "Hello"
    colored = CPrint.colorize(text, fg=CPrint.FG.BRIGHT_GREEN, bold=True)
    assert text in colored
    assert ANSI_PATTERN.search(colored)

    stripped = CPrint.strip_ansi(colored)
    assert stripped == text


def test_cprint_gradient_length_preserved():
    text = "Rainbow!"
    grad = CPrint.gradient(text, fg_codes=CPrint.GradientPalette.RAINBOW)
    stripped = CPrint.strip_ansi(grad)
    assert stripped == text


def test_apply_color_theme_changes_level_style(capsys):
    levels = SmartLogger.levels()
    logger = SmartLogger("theme.test", level=levels["TRACE"])

    SmartLogger.apply_color_theme(DARK_THEME)
    logger.add_console()
    logger.info("Dark theme activated!")

    out = capsys.readouterr().out
    # we don't assert specific codes, just that ANSI is present
    assert ANSI_PATTERN.search(out)


def test_custom_theme_for_dynamic_level(capsys):
    SmartLogger.register_level("NOTICE", 25)
    from LogSmith import CPrint as CP  # alias to avoid confusion

    MY_THEME = {
        "NOTICE": LevelStyle(fg=CP.FG.BRIGHT_MAGENTA),
    }
    SmartLogger.apply_color_theme(MY_THEME)

    levels = SmartLogger.levels()
    logger = SmartLogger("theme.dynamic", level=levels["TRACE"])
    logger.add_console()

    logger.notice("Notice message")
    out = capsys.readouterr().out
    assert "Notice message" in out
    assert ANSI_PATTERN.search(out)
""",

    "tests/unit/test_rotationlogic_core.py": """\
import time
from pathlib import Path

from LogSmith import (
    SmartLogger,
    RotationLogic,
    When,
    RotationTimestamp,
    ExpirationRule,
    ExpirationScale,
)


def test_rotationlogic_basic_attributes():
    rotation = RotationLogic(
        maxBytes=50_000,
        when=When.SECOND,
        interval=1,
        backupCount=5,
        append_filename_pid=True,
        append_filename_timestamp=True,
    )

    assert rotation.maxBytes == 50_000
    assert rotation.when == When.SECOND
    assert rotation.interval == 1
    assert rotation.backupCount == 5
    assert rotation.append_filename_pid is True
    assert rotation.append_filename_timestamp is True


def test_rotationtimestamp_to_seconds():
    ts = RotationTimestamp(hour=1, minute=2, second=3)
    assert ts.to_seconds() == 1 * 3600 + 2 * 60 + 3


def test_expiration_rule_configuration():
    rule = ExpirationRule(scale=ExpirationScale.Days, interval=7)
    assert rule.scale == ExpirationScale.Days
    assert rule.interval == 7


def test_size_based_rotation_triggers(tmp_path: Path):
    levels = SmartLogger.levels()
    logger = SmartLogger("rotation.size", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    rotation = RotationLogic(maxBytes=200, backupCount=3)
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="app.log",
        rotation_logic=rotation,
    )

    # generate enough logs to trigger rotation
    for i in range(100):
        logger.info("X" * 50, index=i)

    base = log_dir / "app.log"
    assert base.exists()

    rotated = [p for p in log_dir.iterdir() if p.name.startswith("app.log.")]
    assert len(rotated) <= 3


def test_time_based_rotation_triggers(tmp_path: Path):
    levels = SmartLogger.levels()
    logger = SmartLogger("rotation.time", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    rotation = RotationLogic(
        when=When.SECOND,
        interval=1,
        backupCount=5,
    )

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="time.log",
        rotation_logic=rotation,
    )

    logger.info("before rotation")
    time.sleep(1.2)
    logger.info("after rotation")

    base = log_dir / "time.log"
    assert base.exists()
    rotated = [p for p in log_dir.iterdir() if p.name.startswith("time.log.")]
    assert len(rotated) >= 1
""",

    "tests/unit/test_hierarchy_and_lifecycle.py": """\
from LogSmith import SmartLogger


def test_logger_hierarchy_inheritance_and_override(capsys):
    levels = SmartLogger.levels()

    root = SmartLogger("myapp", level=levels["INFO"])
    root.add_console()

    api = SmartLogger("myapp.api", level=levels["NOTSET"])
    users = SmartLogger("myapp.api.users", level=levels["DEBUG"])

    # api inherits INFO, users overrides to DEBUG
    api.info("api info")
    api.debug("api debug (should be filtered)")

    users.debug("users debug")
    users.info("users info")

    out = capsys.readouterr().out
    assert "api info" in out
    assert "api debug" not in out
    assert "users debug" in out
    assert "users info" in out


def test_handlers_do_not_propagate_without_auditing(tmp_path):
    levels = SmartLogger.levels()

    root = SmartLogger("root.noaudit", level=levels["TRACE"])
    api = SmartLogger("root.noaudit.api", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    root.add_file(log_dir=str(log_dir), logfile_name="root.log")
    api.add_file(log_dir=str(log_dir), logfile_name="api.log")

    api.info("from api")

    root_log = (log_dir / "root.log").read_text(encoding="utf-8")
    api_log = (log_dir / "api.log").read_text(encoding="utf-8")

    assert "from api" not in root_log
    assert "from api" in api_log


def test_retire_and_destroy_logger(tmp_path):
    levels = SmartLogger.levels()
    logger = SmartLogger("lifecycle.test", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add_file(log_dir=str(log_dir), logfile_name="life.log")
    logger.info("before retire")

    logger.retire()
    # after retire, logging should be effectively disabled
    logger.info("after retire")

    content = (log_dir / "life.log").read_text(encoding="utf-8")
    assert "before retire" in content
    assert "after retire" not in content

    logger.destroy()
    # recreating with same name should be clean
    logger2 = SmartLogger("lifecycle.test", level=levels["INFO"])
    logger2.add_file(log_dir=str(log_dir), logfile_name="life2.log")
    logger2.info("new logger")

    content2 = (log_dir / "life2.log").read_text(encoding="utf-8")
    assert "new logger" in content2
""",

    "tests/unit/test_smartlogger_core.py": """\
from pathlib import Path

from LogSmith import SmartLogger, OutputMode, LogRecordDetails, OptionalRecordFields


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
    assert "user = 'gilad'" in content


def test_raw_output_bypasses_formatting(capsys):
    levels = SmartLogger.levels()
    logger = SmartLogger("core.raw", level=levels["TRACE"])
    logger.add_console()

    logger.raw("RAW LINE")
    out = capsys.readouterr().out.strip()

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

    out = capsys.readouterr().out
    assert "User login" in out
    assert "username = 'Gilad'" in out

    content = (log_dir / "struct.log").read_text(encoding="utf-8")
    assert "User login" in content
    assert "username = 'Gilad'" in content


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
    assert "x = 1" in content
""",

    "tests/unit/test_asyncsmartlogger_core.py": """\
import json
from pathlib import Path

import pytest

from LogSmith import AsyncSmartLogger, OutputMode


@pytest.mark.asyncio
async def test_async_console_logging(capsys):
    levels = AsyncSmartLogger.levels()
    logger = AsyncSmartLogger("async.console", level=levels["TRACE"])
    logger.add_console()

    await logger.a_trace("trace message")
    await logger.a_debug("debug message")
    await logger.a_info("info message")
    await logger.flush()

    out = capsys.readouterr().out
    assert "trace message" in out
    assert "debug message" in out
    assert "info message" in out


@pytest.mark.asyncio
async def test_async_file_logging_ndjson(tmp_path: Path):
    levels = AsyncSmartLogger.levels()
    logger = AsyncSmartLogger("async.file", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="async.ndjson",
        output_mode=OutputMode.NDJSON,
    )

    await logger.a_info("User login", username="Gilad")
    await logger.a_warning("Something odd", code=123)
    await logger.flush()

    logfile = log_dir / "async.ndjson"
    assert logfile.exists()

    lines = logfile.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["level"] == "INFO"
    assert first["message"] == "User login"
    assert first["fields"]["username"] == "Gilad"

    assert second["level"] == "WARNING"
    assert second["fields"]["code"] == 123


@pytest.mark.asyncio
async def test_async_ordering_guarantee(tmp_path: Path):
    levels = AsyncSmartLogger.levels()
    logger = AsyncSmartLogger("async.order", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="order.ndjson",
        output_mode=OutputMode.NDJSON,
    )

    for i in range(50):
        await logger.a_info("msg", index=i)

    await logger.flush()

    logfile = log_dir / "order.ndjson"
    lines = logfile.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 50

    indices = [json.loads(line)["fields"]["index"] for line in lines]
    assert indices == list(range(50))
""",
}


def ensure_dirs():
    (ROOT / "tests").mkdir(exist_ok=True)
    (ROOT / "tests/unit").mkdir(parents=True, exist_ok=True)


def write_file_safe(path: Path, content: str):
    if path.exists():
        print(f"[SKIP] {path} (already exists)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[NEW]  {path}")


def main():
    print(f"\nCreating LogSmith unit tests in: {ROOT}\n")
    ensure_dirs()
    for rel, content in UNIT_TEST_FILES.items():
        write_file_safe(ROOT / rel, content)
    print("\nDone. Run: pytest tests/unit\n")


if __name__ == "__main__":
    main()
