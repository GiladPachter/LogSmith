# LogSmith/level_registry.py

from typing import Any, Dict
import logging

from .colors import CPrint
from .levels import LevelStyle, TRACE


class LevelRegistry:
    def __init__(self) -> None:
        self._levels: Dict[str, Dict[str, Any]] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._init_builtin_levels()

    def _init_builtin_levels(self) -> None:
        self._levels.clear()

        self.register("TRACE", TRACE,
                      LevelStyle(fg=CPrint.FG.SOFT_PURPLE, intensity=CPrint.Intensity.NORMAL),
                      )
        self.register("DEBUG", logging.DEBUG,
                      LevelStyle(fg=CPrint.FG.CYAN, intensity=CPrint.Intensity.NORMAL),
                      )
        self.register("INFO", logging.INFO,
                      LevelStyle(fg=CPrint.FG.NEON_GREEN, intensity=CPrint.Intensity.NORMAL),
                      )
        self.register("WARNING", logging.WARNING,
                      LevelStyle(fg=CPrint.FG.NEON_YELLOW, intensity=CPrint.Intensity.NORMAL),
                      )
        self.register("ERROR", logging.ERROR,
                      LevelStyle(fg=CPrint.FG.NEON_RED, intensity=CPrint.Intensity.BOLD),
                      )
        self.register("CRITICAL", logging.CRITICAL,
                      LevelStyle(fg=CPrint.FG.NEON_YELLOW, bg=CPrint.BG.NEON_RED, intensity=CPrint.Intensity.BOLD,
                                 styles=(CPrint.Style.UNDERLINE,),
                                 ),
                      )

    def register(self, name: str, value: int, style: LevelStyle | None = None) -> None:
        import re

        if not re.fullmatch(r"[A-Z][A-Z0-9_][A-Z0-9]*", name):
            raise ValueError(f"Invalid level name {name!r}. Must be uppercase letters, digits, underscores.")

        for existing in self._levels.values():
            if existing["value"] == value:
                raise ValueError(f"Level value {value} already assigned to another level.") # pragma: no cover

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


def reset_levels_for_tests():
    # noinspection PyProtectedMember
    LEVELS._init_builtin_levels()
