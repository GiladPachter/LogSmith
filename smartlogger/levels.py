# smartlogger/levels.py

import logging
from dataclasses import dataclass
from typing import Tuple

from smartlogger.colors import Code

TRACE = 5
logging.addLevelName(TRACE, "TRACE")


@dataclass(frozen=True)
class LevelStyle:
    """
    Defines how a log level should be colored.
    """
    fg: Code | None = None
    bg: Code | None = None
    intensity: Code | None = None
    styles: Tuple[Code, ...] = ()
