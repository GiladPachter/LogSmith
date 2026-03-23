# tests/test_smartlogger_sync.py

import logging
import uuid
import json
import pytest
from pathlib import Path

from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith.smartlogger import SmartLogger
from LogSmith.level_registry import LEVELS


@pytest.fixture
def clean_sync_logger():
    # Unique logger name per test
    name = f"test_sync_logger_{uuid.uuid4().hex}"
    py_logger = logging.getLogger(name)

    # Remove any existing handlers
    for h in list(py_logger.handlers):
        py_logger.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass

    logger = SmartLogger(name)
    yield logger

    # Cleanup
    for h in list(py_logger.handlers):
        py_logger.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass


# 1. Basic file logging

def test_sync_logger_writes_to_file(clean_sync_logger, tmp_path):
    logger = clean_sync_logger
    logger.add_file(str(tmp_path), "x.log")

    logger.info("hello")
    logger.info("world")

    content = (tmp_path / "x.log").read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]

    # Only check message bodies (after last separator)
    bodies = [line.split("•")[-1].strip() for line in lines]
    assert bodies == ["hello", "world"]


# 2. Level filtering

def test_sync_logger_respects_level_filter(clean_sync_logger, tmp_path):
    logger = clean_sync_logger
    logger.add_file(str(tmp_path), "x.log", level=logging.INFO)

    logger.debug("debug-msg")
    logger.info("info-msg")

    content = (tmp_path / "x.log").read_text(encoding="utf-8")
    bodies = [line.split("•")[-1].strip() for line in content.splitlines()]

    assert "info-msg" in bodies
    assert "debug-msg" not in bodies


# 3. Exception logging

def test_sync_logger_logs_exception_with_traceback(clean_sync_logger, tmp_path):
    file_details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(
            exc_info=True,
            stack_info=True,
        ),
    )

    logger = clean_sync_logger
    logger.add_file(str(tmp_path), "x.log", log_record_details=file_details)

    try:
        1 / 0
    except ZeroDivisionError:
        logger.error("boom", exc_info=True)

    content = (tmp_path / "x.log").read_text(encoding="utf-8")

    assert "boom" in content
    assert "ZeroDivisionError" in content
    assert "Traceback" in content


# 4. Structured JSON output

def test_sync_logger_json_output_is_valid(clean_sync_logger, tmp_path):
    logger = clean_sync_logger
    logger.add_file(
        str(tmp_path),
        "x.log",
        output_mode="json",
        log_record_details=LogRecordDetails(),
    )

    logger.info("hello-json")

    content = (tmp_path / "x.log").read_text(encoding="utf-8").strip()
    obj = json.loads(content)

    assert obj["message"] == "hello-json"
    assert obj["level"].upper() == "INFO"
    assert "timestamp" in obj


# 5. Structured NDJSON output

def test_sync_logger_ndjson_output_is_valid(clean_sync_logger, tmp_path):
    logger = clean_sync_logger
    logger.add_file(
        str(tmp_path),
        "x.log",
        output_mode="ndjson",
        log_record_details=LogRecordDetails(),
    )

    logger.info("line-1")
    logger.info("line-2")

    lines = (tmp_path / "x.log").read_text(encoding="utf-8").splitlines()
    objs = [json.loads(line) for line in lines]

    messages = [o["message"] for o in objs]
    assert messages == ["line-1", "line-2"]


# 6. ANSI stripping by default

def test_sync_logger_strips_ansi_by_default(clean_sync_logger, tmp_path):
    logger = clean_sync_logger
    logger.add_file(str(tmp_path), "x.log")

    ansi_msg = "\x1b[31mred-text\x1b[0m"
    logger.info(ansi_msg)

    content = (tmp_path / "x.log").read_text(encoding="utf-8")
    assert "red-text" in content
    assert "\x1b[31m" not in content
    assert "\x1b[0m" not in content


# 7. ANSI passthrough when enabled

def test_sync_logger_preserves_ansi_when_passthrough_enabled(clean_sync_logger, tmp_path):
    logger = clean_sync_logger
    logger.add_file(str(tmp_path), "x.log", preserve_colors_in_log_files=True)

    ansi_msg = "\x1b[31mred-text\x1b[0m"
    logger.info(ansi_msg)

    content = (tmp_path / "x.log").read_text(encoding="utf-8")
    assert "\x1b[31m" in content
    assert "\x1b[0m" in content


# 8. Extra fields / metadata

def test_sync_logger_handles_extra_fields(clean_sync_logger, tmp_path):
    logger = clean_sync_logger
    logger.add_file(
        str(tmp_path),
        "x.log",
        output_mode="json",
        log_record_details=LogRecordDetails(),
    )

    logger.info("with-extra", extra={"user_id": 123, "request_id": "abc"})

    content = (tmp_path / "x.log").read_text(encoding="utf-8").strip()
    obj = json.loads(content)

    assert obj["message"] == "with-extra"
    assert obj["named_args"]["extra"]["user_id"] == 123
    assert obj["named_args"]["extra"]["request_id"] == "abc"


# 9. TRACE level support (if registered in LEVELS)

def test_sync_logger_trace_level_if_available(clean_sync_logger, tmp_path):
    if "TRACE" not in LEVELS.all():
        pytest.skip("TRACE level not configured in LEVELS")

    logger = clean_sync_logger
    logger.add_file(str(tmp_path), "x.log", level=LEVELS.all()["TRACE"]["value"])

    logger.trace("trace-msg")  # dynamic method via SmartLogger

    content = (tmp_path / "x.log").read_text(encoding="utf-8")
    bodies = [line.split("•")[-1].strip() for line in content.splitlines()]

    assert "trace-msg" in bodies
