import pytest
import logging
from unittest.mock import patch
from LogSmith import SmartLogger, RotationLogic, When

def test_rotation_failure_does_not_crash(tmp_path):
    logger = SmartLogger("rotfail", logging.INFO)
    logic = RotationLogic(maxBytes=1, backupCount=1)

    logger.add_file(str(tmp_path), "r.log", rotation_logic=logic)

    with patch("os.rename", side_effect=OSError("fail")):
        logger.info("x" * 100)

    # Should not crash; file should exist
    assert (tmp_path / "r.log").exists()
