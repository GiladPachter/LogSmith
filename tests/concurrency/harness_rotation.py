# harness_rotation.py

"""
This is used in rotation tests to assert:
- backupCount respected
- no missing numbers
- no corruption
"""

from pathlib import Path


def inspect_rotation(log_dir: Path, base_name: str):
    """
    Returns:
        base_exists: bool
        rotated_files: list[Path]
        rotation_numbers: list[int]
    """

    base_file = log_dir / base_name

    rotated = [
        p for p in log_dir.iterdir()
        if p.name.startswith(base_name + ".") and not p.name.endswith(".lock")
    ]

    rotation_numbers = []
    for p in rotated:
        suffix = p.name.split(".")[-1]
        if suffix.isdigit():
            rotation_numbers.append(int(suffix))

    return base_file.exists(), rotated, sorted(rotation_numbers)
