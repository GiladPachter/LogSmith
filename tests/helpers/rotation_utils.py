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
