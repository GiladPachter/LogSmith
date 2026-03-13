import logging

import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation import RotationLogic
from LogSmith.formatter import OutputMode


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
