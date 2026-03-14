from pathlib import Path
from LogSmith import SmartLogger
from LogSmith.rotation_base import RotationLogic

def test_plain_output(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    logger = SmartLogger("fs.plain", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=RotationLogic())

    logger.info("hello", user="gilad")

    content = (log_dir / "app.log").read_text(encoding="utf-8")
    assert "hello" in content
    assert "{user='gilad'}" in content
