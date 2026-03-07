from pathlib import Path
from LogSmith import SmartLogger
from LogSmith.rotation import RotationLogic

def test_suffixes(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=50, append_filename_pid=True, append_filename_timestamp=True)
    logger = SmartLogger("fs.suffix", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    logger.info("hello")

    files = list(log_dir.iterdir())
    assert any("app" in f.name and ("_" in f.name or "." in f.name) for f in files)
