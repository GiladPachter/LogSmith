import os
import time

from LogSmith import SmartLogger
from LogSmith.rotation_base import RotationLogic, ExpirationRule, ExpirationScale


def test_expiration(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=50, backupCount=10,
                             expiration_rule=ExpirationRule(scale=ExpirationScale.Seconds, interval=1))

    logger = SmartLogger("fs.expire", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    # First rotation
    logger.info("A" * 100)
    first = log_dir / "app.log.1"

    # Make it old
    old_time = time.time() - 10
    os.utime(first, (old_time, old_time))

    # Second rotation
    logger.info("B" * 100)

    rotated = [
        p for p in log_dir.iterdir()
        if p.name.startswith("app.log.") and not p.name.endswith(".lock")
    ]

    # Only the new rotated file should remain
    assert len(rotated) == 1
