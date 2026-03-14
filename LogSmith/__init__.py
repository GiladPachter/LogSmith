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

# Version metadata
# noinspection PyBroadException
try:
    from importlib.metadata import version
    __version__ = version("LogSmith")
except Exception:
    __version__ = "1.9.1"


# LogSmith's calling card
from .metadata import get_metadata, get_license_text, get_file_tree



# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

# Core logger
from .smartlogger import SmartLogger, stdout

# Formatting
from .formatter import LogRecordDetails, OptionalRecordFields, OutputMode

# Rotation & retention
from .rotation_base import (
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


# ----------------------------------------------------------------------
# Calling Card
# ----------------------------------------------------------------------

__metadata__ = get_metadata()

__license_text__ = get_license_text()

__package_content__ = get_file_tree()

__all__.append("__metadata__")
__all__.append("__license_text__")
__all__.append("__package_content__")
