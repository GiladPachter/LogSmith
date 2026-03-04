"""
LogSmith:
=========
    A high‑performance logging framework with:
    - structured formatting
    - color and gradient output
    - size/time‑based rotation
    - retention policies
    - global auditing
    - concurrency‑safe file handlers
"""

from pathlib import Path
import tomllib


# Version metadata
# noinspection PyBroadException
try:
    from importlib.metadata import version
    __version__ = version("LogSmith")
except Exception:
    __version__ = "1.8.3"


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

# Core logger
from .smartlogger import SmartLogger, stdout

# Formatting
from .formatter import LogRecordDetails, OptionalRecordFields, OutputMode

# Rotation & retention
from .rotation import (
    RotationLogic,
    When,
    RotationTimestamp,
    ExpirationRule,
    ExpirationScale,
)

# Colors & gradients
from .colors import CPrint, GradientDirection, GradientPalette, blend_palettes

# Levels & themes
from .levels import LevelStyle
from .themes import DARK_THEME, LIGHT_THEME, NEON_THEME, PASTEL_THEME, FIRE_THEME, OCEAN_THEME

# async logger
from .async_smartlogger import AsyncSmartLogger, a_stdout


__all__ = [
    # Core
    "SmartLogger",
    "stdout",

    # Formatting
    "LogRecordDetails",
    "OptionalRecordFields",
    "OutputMode",

    # Rotation & retention
    "RotationLogic",
    "When",
    "RotationTimestamp",
    "ExpirationRule",
    "ExpirationScale",

    # Colors & gradients
    "CPrint",
    "GradientDirection",
    "GradientPalette",
    "blend_palettes",

    # Levels & themes
    "LevelStyle",
    "DARK_THEME",
    "LIGHT_THEME",
    "NEON_THEME",
    "PASTEL_THEME",
    "FIRE_THEME",
    "OCEAN_THEME",

    # Metadata
    "__version__",

    # async
    "AsyncSmartLogger",
    "a_stdout",
]


def _build_tree_from_paths(paths: list[str]):
    tree: dict[str, dict] = {}
    for p in paths:
        parts = Path(p).parts
        node = tree
        for part in parts:
            node = node.setdefault(part, {})
    return tree


def _render_tree_ascii(tree: dict, prefix: str = "") -> list[str]:
    lines = []
    entries = list(tree.items())
    for i, (name, subtree) in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "\\-- " if is_last else "+-- "
        lines.append(prefix + connector + name)
        if subtree:
            extension = "    " if is_last else "|   "
            lines.extend(_render_tree_ascii(subtree, prefix + extension))
    return lines


def get_logsmith_file_tree(file_list: list[str]) -> str:
    tree = _build_tree_from_paths(file_list)
    return "\n".join(_render_tree_ascii(tree))



def _load_project_metadata():
    root = Path(__file__).resolve().parent.parent
    pyproject = root / "pyproject.toml"

    # Load pyproject metadata
    try:
        data = tomllib.loads(pyproject.read_text("utf-8"))
        project = data.get("project", {})
    except Exception:
        project = {}

    # Extract author email
    authors = project.get("authors", [])
    author_name = None
    author_email = None
    if authors and isinstance(authors, list):
        first = authors[0]
        if isinstance(first, dict):
            author_name = first.get("name")
            author_email = first.get("email")

    # Extract license
    license_info = project.get("license")
    if isinstance(license_info, dict):
        license_value = license_info.get("text") or license_info.get("file")
    else:
        license_value = license_info

    # Collect file list (source tree)
    file_list = []
    for path in root.rglob("*"):
        rel_root = str(path.relative_to(root)).replace("/", "\\")
        if "venv" in path.__str__().lower():
            continue
        if rel_root.startswith("venv\\") or rel_root.startswith(".venv\\"):
            continue
        if rel_root.startswith(".idea\\"):
            continue
        if rel_root.startswith(".git"):
            continue
        if rel_root.startswith("dist\\"):
            continue
        if rel_root.startswith("LogSmith.egg-info\\"):
            continue
        if "__pycache__" in rel_root:
            continue
        if path.is_file():
            file_list.append(rel_root)

    return {
        "name": project.get("name"),
        "version": project.get("version"),
        "description": project.get("description"),
        "author": author_name,
        "author_email": author_email,
        "urls": project.get("urls", {}),
        "license": license_value,
        "requires-python": project.get("requires-python"),
        "files": get_logsmith_file_tree(file_list).splitlines(),
    }

__metadata__ = _load_project_metadata()
