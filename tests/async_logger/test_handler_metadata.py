import logging
import pytest
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation import RotationLogic, When


@pytest.mark.asyncio
async def test_handler_info_console():
    logger = AsyncSmartLogger("test_handler_info_console", logging.INFO)
    logger.add_console()

    info = logger.handler_info
    assert len(info) == 1

    h = info[0]
    assert h["kind"] == "console"
    assert h["level"] == "INFO"
    assert h["formatter"] in ("color", "plain", "json", "ndjson")  # depends on mode
    assert h["path"] is None
    assert h["rotation"] is None


@pytest.mark.asyncio
async def test_handler_info_file_plain(tmp_path):
    logger = AsyncSmartLogger("test_handler_info_file_plain", logging.INFO)

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="plain.log",
        output_mode="plain",
    )

    info = logger.handler_info
    assert len(info) == 1

    h = info[0]
    assert h["kind"] == "file"
    assert h["level"] == "INFO"
    assert h["formatter"] == "plain"
    assert h["path"].endswith("plain.log")
    assert h["rotation"] is None


@pytest.mark.asyncio
async def test_handler_info_file_with_rotation(tmp_path):
    logger = AsyncSmartLogger("test_handler_info_file_rotation", logging.INFO)

    rotation_logic = RotationLogic(maxBytes=1000, backupCount=3)

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="rot.log",
        rotation_logic=rotation_logic,
    )

    info = logger.handler_info

    h = info[0]
    assert h["kind"] == "file"
    assert h["rotation"] is not None

    rot = h["rotation"]
    assert rot["maxBytes"] == 1000
    assert rot["when"] == "SECOND"
    assert rot["interval"] == 1
    assert rot["backupCount"] == 3


@pytest.mark.asyncio
async def test_output_targets_console():
    logger = AsyncSmartLogger("test_output_targets_console", logging.INFO)
    logger.add_console()

    assert logger.output_targets == ["console"]


@pytest.mark.asyncio
async def test_output_targets_file(tmp_path):
    logger = AsyncSmartLogger("test_output_targets_file", logging.INFO)

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="out.log",
        output_mode="plain",
    )

    targets = logger.output_targets
    assert len(targets) == 1
    assert targets[0].endswith("out.log")
