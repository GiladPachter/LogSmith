from pathlib import Path

from project_definitions import ROOT_DIR

# Directory where tests will be created
BASE_DIR = Path(ROOT_DIR) / "tests" / "async_tests"
BASE_DIR.mkdir(parents=True, exist_ok=True)

tests = {
    "test_async_backup_count.py": """
import time
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic

def test_async_backup_count(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=50, backupCount=2)
    logger = AsyncSmartLogger("async.backup", level=AsyncSmartLogger.levels()["INFO"])
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="app.log",
        rotation_logic=rotation,
    )

    for _ in range(50):
        logger.info("X" * 20)

    logger.flush()

    rotated = [
        p for p in log_dir.iterdir()
        if p.name.startswith("app.log.") and not p.name.endswith(".lock")
    ]
    assert len(rotated) <= 2
""",

    "test_async_time_rotation.py": """
import time
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic, When

def test_async_time_rotation(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(
        when=When.SECOND,
        interval=1,
        backupCount=3,
    )

    logger = AsyncSmartLogger("async.time", level=AsyncSmartLogger.levels()["INFO"])
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="app.log",
        rotation_logic=rotation,
    )

    logger.info("start")
    time.sleep(1.2)
    logger.info("after rollover")
    logger.flush()

    rotated = [
        p for p in log_dir.iterdir()
        if p.name.startswith("app.log.") and not p.name.endswith(".lock")
    ]
    assert len(rotated) >= 1
""",

    "test_async_expiration.py": """
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic, ExpirationRule, ExpirationScale

def test_async_expiration(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(
        maxBytes=30,
        backupCount=10,
        expiration_rule=ExpirationRule(ExpirationScale.Seconds, interval=0),
    )

    logger = AsyncSmartLogger("async.expire", level=AsyncSmartLogger.levels()["INFO"])
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="app.log",
        rotation_logic=rotation,
    )

    for _ in range(20):
        logger.info("X" * 20)

    logger.flush()

    rotated = [
        p for p in log_dir.iterdir()
        if p.name.startswith("app.log.") and not p.name.endswith(".lock")
    ]

    assert len(rotated) == 0
""",

    "test_async_thread_safety.py": """
import threading
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic

def test_async_thread_safety(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=200, backupCount=3)
    logger = AsyncSmartLogger("async.threads", level=AsyncSmartLogger.levels()["INFO"])
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="app.log",
        rotation_logic=rotation,
    )

    def worker():
        for _ in range(200):
            logger.info("thread message")

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()

    logger.flush()

    assert (log_dir / "app.log").exists()
""",

    "test_async_emit_non_blocking.py": """
import time
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic

def test_async_emit_non_blocking(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=20, backupCount=2)
    logger = AsyncSmartLogger("async.nonblock", level=AsyncSmartLogger.levels()["INFO"])
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="app.log",
        rotation_logic=rotation,
    )

    start = time.time()
    for _ in range(200):
        logger.info("X" * 50)
    end = time.time()

    logger.flush()

    assert (end - start) < 0.2
""",

    "test_async_rotation_callback.py": """
import time
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic

def test_async_rotation_callback(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=30, backupCount=2)
    logger = AsyncSmartLogger("async.callback", level=AsyncSmartLogger.levels()["INFO"])

    callback_hits = []

    def callback(handler):
        callback_hits.append(time.time())

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="app.log",
        rotation_logic=rotation,
        rotation_callback=callback,
    )

    for _ in range(20):
        logger.info("X" * 20)

    logger.flush()

    assert len(callback_hits) >= 1
""",

    "test_async_no_lock_file.py": """
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic

def test_async_no_lock_file(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=50, backupCount=2)
    logger = AsyncSmartLogger("async.nolock", level=AsyncSmartLogger.levels()["INFO"])
    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="app.log",
        rotation_logic=rotation,
    )

    for _ in range(20):
        logger.info("X" * 20)

    logger.flush()

    lock_files = [p for p in log_dir.iterdir() if p.name.endswith(".lock")]
    assert len(lock_files) == 0
"""
}

for filename, content in tests.items():
    path = BASE_DIR / filename
    path.write_text(content.strip() + "\n", encoding="utf-8")

print(f"Created {len(tests)} async test files in {BASE_DIR}")
