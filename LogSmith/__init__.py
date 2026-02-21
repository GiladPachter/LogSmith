"""
LogSmith
========

A high‑performance logging framework with:
- structured formatting
- color and gradient output
- size/time‑based rotation
- retention policies
- global auditing
- concurrency‑safe file handlers
"""

# Version metadata
# noinspection PyBroadException
try:
    from importlib.metadata import version
    __version__ = version("LogSmith")
except Exception:
    __version__ = "1.7.0"

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

# Core logger
from .smartlogger import SmartLogger

# Formatting
from .formatter import LogRecordDetails, OptionalRecordFields

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

__all__ = [
    # Core
    "SmartLogger",

    # Formatting
    "LogRecordDetails",
    "OptionalRecordFields",

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
]
