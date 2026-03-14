import logging
import sys

import pytest
from rich import json

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic
from LogSmith.formatter import OutputMode, StructuredJSONFormatter, LogRecordDetails, StructuredNDJSONFormatter


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
    await logger._queue.join()

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


