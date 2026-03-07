from pathlib import Path

ROOT = Path("..").resolve()

HARNESS_FILES = {
    "tests/conftest.py": """\
# Auto-generated pytest fixtures for LogSmith

import asyncio
import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def temp_logs_dir(tmp_path: Path) -> Path:
    d = tmp_path / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def temp_audit_dir(tmp_path: Path) -> Path:
    d = tmp_path / "audit"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def ndjson_loader():
    def _load(path: Path):
        records = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records
    return _load


@pytest.fixture
def force_rotation():
    def _force(handler, *, size_bytes: int | None = None):
        if size_bytes is not None:
            handler.baseFilename and Path(handler.baseFilename).write_text("x" * size_bytes)
        if hasattr(handler, "doRollover"):
            handler.doRollover()
    return _force
""",

    "tests/helpers/__init__.py": """\
# Helper utilities for LogSmith tests (no tests here on purpose).
""",

    "tests/helpers/file_utils.py": """\
from pathlib import Path


def list_files_sorted(dir_path: Path) -> list[Path]:
    if not dir_path.exists():
        return []
    return sorted(p for p in dir_path.iterdir() if p.is_file())
""",

    "tests/helpers/ndjson_utils.py": """\
import json
from pathlib import Path


def load_ndjson(path: Path):
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def is_valid_ndjson(path: Path) -> bool:
    try:
        _ = load_ndjson(path)
        return True
    except Exception:
        return False
""",

    "tests/helpers/async_utils.py": """\
import asyncio


async def drain_queue(queue: asyncio.Queue):
    items = []
    while not queue.empty():
        items.append(await queue.get())
    return items
""",

    "tests/helpers/logger_factory.py": """\
from pathlib import Path


def make_smart_logger(name: str, level: int, log_dir: Path | None = None):
    from LogSmith import SmartLogger  # type: ignore

    logger = SmartLogger(name, level=level)
    logger.add_console()
    if log_dir is not None:
        logger.add_file(log_dir=str(log_dir), logfile_name=f"{name}.log")
    return logger


async def make_async_logger(name: str, level: int, log_dir: Path | None = None):
    from LogSmith import AsyncSmartLogger  # type: ignore

    logger = AsyncSmartLogger(name, level=level)
    logger.add_console()
    if log_dir is not None:
        logger.add_file(log_dir=str(log_dir), logfile_name=f"{name}.log")
    return logger
""",

    "tests/helpers/rotation_utils.py": """\
from pathlib import Path
from LogSmith import RotationLogic, When  # type: ignore


def small_size_rotation(max_bytes: int = 1024) -> RotationLogic:
    return RotationLogic(maxBytes=max_bytes, backupCount=3)


def fast_time_rotation() -> RotationLogic:
    return RotationLogic(when=When.SECOND, interval=1, backupCount=3)


def count_rotated_files(base_path: Path) -> int:
    parent = base_path.parent
    stem = base_path.name
    return sum(1 for p in parent.iterdir() if p.name.startswith(stem + "."))
""",

    "tests/helpers/concurrency_utils.py": """\
import threading
from pathlib import Path
from typing import Callable


def hammer_logger(fn: Callable[[], None], threads: int = 10, iterations: int = 100):
    def worker():
        for _ in range(iterations):
            fn()

    ts = [threading.Thread(target=worker) for _ in range(threads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0
""",
}


def ensure_dirs():
    (ROOT / "tests").mkdir(exist_ok=True)
    (ROOT / "tests/helpers").mkdir(parents=True, exist_ok=True)


def write_file_safe(path: Path, content: str):
    if path.exists():
        print(f"[SKIP] {path} (already exists)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[NEW]  {path}")


def main():
    print(f"\nCreating LogSmith test harness in: {ROOT}\n")
    ensure_dirs()
    for rel, content in HARNESS_FILES.items():
        write_file_safe(ROOT / rel, content)
    print("\nDone.\n")


if __name__ == "__main__":
    main()
