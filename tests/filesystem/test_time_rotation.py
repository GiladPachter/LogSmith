import time
from pathlib import Path
from LogSmith import SmartLogger
from LogSmith.rotation import RotationLogic, When, RotationTimestamp

def test_time_rotation(tmp_path: Path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    fake_time = [1000]

    def fake_now():
        return fake_time[0]

    monkeypatch.setattr(time, "time", fake_now)

    rotation = RotationLogic(when=When.SECOND, interval=1)
    logger = SmartLogger("fs.time", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    logger.info("first")
    fake_time[0] += 2
    logger.info("second")

    rotated = [p for p in log_dir.iterdir() if p.name.startswith("app.log.") and not p.name.endswith(".lock")]
    assert len(rotated) >= 1
