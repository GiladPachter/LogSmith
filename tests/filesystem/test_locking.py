import multiprocessing
from pathlib import Path
from LogSmith import SmartLogger
from LogSmith.rotation import RotationLogic

def worker(log_dir):
    logger = SmartLogger("fs.lock", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=RotationLogic(maxBytes=200))
    for i in range(200):
        logger.info("hello from worker", index=i)

def test_locking(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    procs = [multiprocessing.Process(target=worker, args=(log_dir,)) for _ in range(3)]
    for p in procs: p.start()
    for p in procs: p.join()

    assert (log_dir / "app.log").exists()
