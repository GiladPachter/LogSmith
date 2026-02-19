# examples/09_themes_demo.py

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import time

from LogSmith import SmartLogger
from LogSmith import DARK_THEME, LIGHT_THEME, NEON_THEME, PASTEL_THEME, FIRE_THEME, OCEAN_THEME

# ----------------------------------------------------------------------------------------------------------
# critically essential initialization first thing at application entry point, for consistent logger behavior
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["TRACE"])
# ----------------------------------------------------------------------------------------------------------

logger = SmartLogger.get("themes_logger", levels["TRACE"])
logger.add_console()

def demo_theme(name, theme):
    SmartLogger.apply_color_theme(theme)

    logger.trace(f"{name}: trace message")
    logger.debug(f"{name}: debug message")
    logger.info(f"{name}: info message")
    logger.warning(f"{name}: warning message")
    logger.error(f"{name}: error message")
    logger.critical(f"{name}: critical message")

print("\n--- LIGHT THEME ---")
time.sleep(0.2)
demo_theme("light", LIGHT_THEME)
time.sleep(0.2)

print("\n--- DARK THEME ---")
time.sleep(0.2)
demo_theme("dark", DARK_THEME)
time.sleep(0.2)

print("\n--- NEON THEME ---")
time.sleep(0.2)
demo_theme("neon", NEON_THEME)
time.sleep(0.2)

print("\n--- PASTEL THEME ---")
time.sleep(0.2)
demo_theme("pastel", PASTEL_THEME)
time.sleep(0.2)

print("\n--- FIRE THEME ---")
time.sleep(0.2)
demo_theme("fire", FIRE_THEME)
time.sleep(0.2)

print("\n--- OCEAN THEME ---")
time.sleep(0.2)
demo_theme("ocean", OCEAN_THEME)
time.sleep(0.2)

print("\n--- RESTORING DEFAULTS ---")
time.sleep(0.2)
demo_theme("default", None)
time.sleep(0.2)
