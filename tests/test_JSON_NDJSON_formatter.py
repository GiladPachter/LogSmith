import logging
import sys
import pytest

from io import StringIO
from rich import json

from LogSmith import RotationLogic
from LogSmith.formatter import StructuredJSONFormatter, LogRecordDetails, StructuredNDJSONFormatter
from LogSmith import SmartLogger

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith import OutputMode



@pytest.mark.asyncio
async def test_json_formatter_deep_fields(tmp_path):
    logic = RotationLogic(maxBytes=1024, backupCount=1)

    logger = AsyncSmartLogger("json_deep", logging.INFO)
    logger.add_file(
        str(tmp_path),
        "jdeep.log",
        rotation_logic=logic,
        output_mode=OutputMode.JSON,
    )

    payload = {"a": {"b": {"c": 123, "d": ["x", "y"]}}}
    await logger.a_info("deep", extra={"fields": payload})
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    text = (tmp_path / "jdeep.log").read_text(encoding="utf-8").strip()
    assert "deep" in text
    assert '"a"' in text
    assert '"b"' in text
    assert '"c"' in text
    assert "123" in text


def test_json_formatter_with_exception():
    fmt = StructuredJSONFormatter(LogRecordDetails())
    # noinspection PyBroadException
    try:
        raise ValueError("boom")
    except Exception:
        r = logging.makeLogRecord({
            "msg": "test",
            "level": logging.ERROR,
            "exc_info": sys.exc_info(),
        })

    out = fmt.format(r)
    data = json.loads(out)

    assert data["exception"]["type"] == "ValueError"
    assert "boom" in data["exception"]["message"]


def test_ndjson_single_line_output():
    fmt = StructuredNDJSONFormatter(LogRecordDetails())
    r = logging.makeLogRecord({"msg": "hello", "level": logging.INFO})

    out = fmt.format(r)
    assert "\n" not in out  # NDJSON must be single-line
    json.loads(out)


def test_smartlogger_console_json(tmp_path):
    lg = SmartLogger("console_json_test")
    lg.add_console(output_mode=OutputMode.JSON)

    # Replace console handler stream with StringIO
    handler = lg._SmartLogger__py_logger.handlers[0]
    buf = StringIO()
    handler.stream = buf

    lg.info("HELLO JSON")

    handler.flush()
    text = buf.getvalue().strip()

    data = json.loads(text)
    assert data["level"] == "INFO"
    assert data["message"] == "HELLO JSON"

    lg.destroy()


def test_smartlogger_console_ndjson(tmp_path):
    lg = SmartLogger("console_ndjson_test")
    lg.add_console(output_mode=OutputMode.NDJSON)

    handler = lg._SmartLogger__py_logger.handlers[0]
    buf = StringIO()
    handler.stream = buf

    lg.info("HELLO NDJSON")

    handler.flush()
    text = buf.getvalue().strip()

    data = json.loads(text)
    assert data["level"] == "INFO"
    assert data["message"] == "HELLO NDJSON"

    lg.destroy()


@pytest.mark.asyncio
async def test_asyncsmartlogger_console_json(tmp_path):
    lg = AsyncSmartLogger("async_console_json_test")
    lg.add_console(output_mode=OutputMode.JSON)

    handler = lg._AsyncSmartLogger__py_logger.handlers[0]
    buf = StringIO()
    handler.stream = buf

    await lg.a_info("HELLO JSON")
    await lg.flush()

    text = buf.getvalue().strip()
    data = json.loads(text)

    assert data["level"] == "INFO"
    assert data["message"] == "HELLO JSON"

    await lg.shutdown()
    lg.destroy()


@pytest.mark.asyncio
async def test_asyncsmartlogger_console_ndjson(tmp_path):
    lg = AsyncSmartLogger("async_console_ndjson_test")
    lg.add_console(output_mode=OutputMode.NDJSON)

    handler = lg._AsyncSmartLogger__py_logger.handlers[0]
    buf = StringIO()
    handler.stream = buf

    await lg.a_info("HELLO NDJSON")
    await lg.flush()

    text = buf.getvalue().strip()
    data = json.loads(text)

    assert data["level"] == "INFO"
    assert data["message"] == "HELLO NDJSON"

    await lg.shutdown()
    lg.destroy()
