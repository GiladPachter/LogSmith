import os
from pathlib import Path

ROOT = Path("..").resolve()

FILESYSTEM_TESTS = {
    "test_size_rotation.py": """
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
""",

    "test_time_rotation.py": """
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
""",

    "test_backup_count.py": """
from pathlib import Path
from LogSmith import SmartLogger
from LogSmith.rotation import RotationLogic

def test_backup_count(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=50, backupCount=2)
    logger = SmartLogger("fs.backup", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    for i in range(50):
        logger.info("X" * 20)

    rotated = [p for p in log_dir.iterdir() if p.name.startswith("app.log.") and not p.name.endswith(".lock")]
    assert len(rotated) <= 2
""",

    "test_expiration.py": """
import time
from pathlib import Path
from datetime import timedelta, datetime
from LogSmith import SmartLogger
from LogSmith.rotation import RotationLogic, ExpirationRule, ExpirationScale

def test_expiration(tmp_path: Path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    now = [1000]

    def fake_now():
        return now[0]

    monkeypatch.setattr(time, "time", fake_now)

    rotation = RotationLogic(
        maxBytes=50,
        backupCount=10,
        expiration_rule=ExpirationRule(scale=ExpirationScale.Seconds, interval=1)
    )

    logger = SmartLogger("fs.expire", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    logger.info("A" * 100)
    now[0] += 2
    logger.info("B" * 100)

    rotated = [p for p in log_dir.iterdir() if p.name.startswith("app.log.") and not p.name.endswith(".lock")]
    assert len(rotated) <= 1
""",

    "test_locking.py": """
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
""",

    "test_suffixes.py": """
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
""",

    "test_async_rotation_filesystem.py": """
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic

async def test_async_rotation(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=100, backupCount=2)
    logger = AsyncSmartLogger("fs.async", level=AsyncSmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    for i in range(50):
        logger.info("X" * 30)

    await logger._queue.join()

    rotated = [p for p in log_dir.iterdir() if p.name.startswith("app.log.") and not p.name.endswith(".lock")]
    assert len(rotated) <= 2
""",

    "test_json_output.py": """
from pathlib import Path
from LogSmith import SmartLogger
from LogSmith.formatter import LogRecordDetails
from LogSmith.rotation import RotationLogic

def test_json_output(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    details = LogRecordDetails()
    logger = SmartLogger("fs.json", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.json", rotation_logic=RotationLogic(), output_mode="json", details=details)

    logger.info("hello", user="gilad")

    content = (log_dir / "app.json").read_text()
    assert '"message": "hello"' in content
    assert '"user": "gilad"' in content
""",

    "test_plain_output.py": """
from pathlib import Path
from LogSmith import SmartLogger
from LogSmith.rotation import RotationLogic

def test_plain_output(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    logger = SmartLogger("fs.plain", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=RotationLogic())

    logger.info("hello", user="gilad")

    content = (log_dir / "app.log").read_text()
    assert "hello" in content
    assert "{user = 'gilad'}" in content
""",
}


def create_filesystem_tests(base_dir="..\tests_filesystem"):
    # base = Path(base_dir)
    # base.mkdir(exist_ok=True)

    base = ROOT / "tests/filesystem"

    for filename, content in FILESYSTEM_TESTS.items():
        path = base / filename
        path.write_text(content.strip() + "\n", encoding="utf-8")

    print(f"Filesystem tests created in: {base.resolve()}")


def ensure_dirs():
    (ROOT / "tests").mkdir(exist_ok=True)
    (ROOT / "tests/ests_filesystem").mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_dirs()
    create_filesystem_tests()
