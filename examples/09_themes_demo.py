# examples/09_themes_demo.py

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

from LogSmith import SmartLogger
from LogSmith import DARK_THEME, LIGHT_THEME, NEON_THEME, PASTEL_THEME, FIRE_THEME, OCEAN_THEME

# ----------------------------------------------------------------------------------------------------------
# 1. Initialization
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()

# ----------------------------------------------------------------------------------------------------------

logger = SmartLogger("themes_logger", levels["TRACE"])
logger.add_console()

def demo_theme(name, theme):
    SmartLogger.apply_color_theme(theme)

    logger.trace(f"{name}: trace message")
    logger.debug(f"{name}: debug message")
    logger.info(f"{name}: info message")
    logger.warning(f"{name}: warning message")
    logger.error(f"{name}: error message")
    logger.critical(f"{name}: critical message")


logger.stdout("\n--- LIGHT THEME ---")
demo_theme("light", LIGHT_THEME)

logger.stdout("\n--- DARK THEME ---")
demo_theme("dark", DARK_THEME)

logger.stdout("\n--- NEON THEME ---")
demo_theme("neon", NEON_THEME)

logger.stdout("\n--- PASTEL THEME ---")
demo_theme("pastel", PASTEL_THEME)

logger.stdout("\n--- FIRE THEME ---")
demo_theme("fire", FIRE_THEME)

logger.stdout("\n--- OCEAN THEME ---")
demo_theme("ocean", OCEAN_THEME)

logger.stdout("\n--- RESTORING DEFAULTS ---")
demo_theme("default", None)
