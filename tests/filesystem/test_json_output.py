from pathlib import Path
from LogSmith import SmartLogger
from LogSmith.formatter import LogRecordDetails
from LogSmith.rotation import RotationLogic

def test_json_output(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    details = LogRecordDetails()
    logger = SmartLogger("fs.json", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir),
                    logfile_name="app.json",
                    log_record_details = details,
                    rotation_logic=RotationLogic(),
                    output_mode="json"
                    )

    logger.info("hello", user="gilad")

    content = (log_dir / "app.json").read_text()
    assert '"message": "hello"' in content
    assert '"user": "gilad"' in content
