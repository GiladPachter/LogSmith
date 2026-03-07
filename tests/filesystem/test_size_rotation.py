import time
from pathlib import Path
from LogSmith import SmartLogger
from LogSmith.rotation import RotationLogic

def test_size_rotation(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=200, backupCount=3)
    logger = SmartLogger("fs.size", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    # generate enough logs to trigger rotation
    for i in range(100):
        logger.info("X" * 50, index=i)

    base = log_dir / "app.log"
    assert base.exists()

    rotated = [p for p in log_dir.iterdir() if p.name.startswith("app.log.") and not p.name.endswith(".lock")]
    assert len(rotated) <= 3
