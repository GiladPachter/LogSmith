import logging
from LogSmith import SmartLogger, RotationLogic, When
import time

def test_rotation_retention_cleanup(tmp_path):
    logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        backupCount=1,
    )

    logger = SmartLogger("retention", logging.INFO)
    logger.add_file(str(tmp_path), "r.log", rotation_logic=logic)

    # force multiple rotations
    for _ in range(4):
        logger.info("x" * 5000)
        time.sleep(1.1)

    files = [
        f for f in tmp_path.glob("r.log*")
        if not f.name.endswith(".lock")
    ]

    # only base + 1 backup should remain
    assert len(files) <= 2
