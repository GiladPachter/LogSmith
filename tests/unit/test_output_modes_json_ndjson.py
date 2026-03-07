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
        ),
        message_parts_order=[
            "level",
            "logger_name",
            "file_name",
            "lineno",
        ],
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
    assert "file_name" in data
    assert "lineno" in data


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
