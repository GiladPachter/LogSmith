# LogSmith/level_registry.py

from typing import Any, Dict
import logging
from .levels import LevelStyle

class LevelRegistry:
    def __init__(self) -> None:
        self._levels: Dict[str, Dict[str, Any]] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, value: int, style: LevelStyle | None = None) -> None:
        import re

        if not re.fullmatch(r"[A-Z][A-Z0-9_][A-Z0-9]*", name):
            raise ValueError(f"Invalid level name {name!r}. Must be uppercase letters, digits, underscores.")

        for existing in self._levels.values():
            if existing["value"] == value:
                raise ValueError(f"Level value {value} already assigned to another level.")

        logging.addLevelName(value, name)

        # --- store default_style so themes can be reset ---
        self._levels[name] = {
            "value": value,
            "style": style,
            "default_style": style,   # <--- added
        }

    def get(self, name: str) -> Dict[str, Any]:
        if name in self._cache:
            return self._cache[name]

        value = self._levels[name]
        self._cache[name] = value
        return value

    def all(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._levels)


LEVELS = LevelRegistry()
