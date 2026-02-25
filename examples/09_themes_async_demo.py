# examples/09_themes_async_demo.py

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import asyncio

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith import (
    DARK_THEME,
    LIGHT_THEME,
    NEON_THEME,
    PASTEL_THEME,
    FIRE_THEME,
    OCEAN_THEME,
)


async def main():
    # ------------------------------------------------------------------------------------------------------
    # Initialization — async version does not require global init
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    print("\nAsync Themes demo\n=================")

    # ------------------------------------------------------------------------------------------------------
    # Create logger with console handler
    # ------------------------------------------------------------------------------------------------------
    logger = AsyncSmartLogger.get("themes_logger_async", levels["TRACE"])
    logger.add_console()

    # ------------------------------------------------------------------------------------------------------
    # Helper: demonstrate a theme
    # ------------------------------------------------------------------------------------------------------
    async def demo_theme(name, theme):
        AsyncSmartLogger.apply_color_theme(theme)

        await logger.a_trace(f"{name}: trace message")
        await logger.a_debug(f"{name}: debug message")
        await logger.a_info(f"{name}: info message")
        await logger.a_warning(f"{name}: warning message")
        await logger.a_error(f"{name}: error message")
        await logger.a_critical(f"{name}: critical message")

    # ------------------------------------------------------------------------------------------------------
    # Theme demonstrations
    # ------------------------------------------------------------------------------------------------------
    print("\n--- LIGHT THEME ---")
    await asyncio.sleep(0.2)
    await demo_theme("light", LIGHT_THEME)
    await asyncio.sleep(0.2)

    print("\n--- DARK THEME ---")
    await asyncio.sleep(0.2)
    await demo_theme("dark", DARK_THEME)
    await asyncio.sleep(0.2)

    print("\n--- NEON THEME ---")
    await asyncio.sleep(0.2)
    await demo_theme("neon", NEON_THEME)
    await asyncio.sleep(0.2)

    print("\n--- PASTEL THEME ---")
    await asyncio.sleep(0.2)
    await demo_theme("pastel", PASTEL_THEME)
    await asyncio.sleep(0.2)

    print("\n--- FIRE THEME ---")
    await asyncio.sleep(0.2)
    await demo_theme("fire", FIRE_THEME)
    await asyncio.sleep(0.2)

    print("\n--- OCEAN THEME ---")
    await asyncio.sleep(0.2)
    await demo_theme("ocean", OCEAN_THEME)
    await asyncio.sleep(0.2)

    print("\n--- RESTORING DEFAULTS ---")
    await asyncio.sleep(0.2)
    await demo_theme("default", None)
    await asyncio.sleep(0.2)

    print("\nAsync Themes demo complete.\n")

    # Ensure all logs are flushed
    await logger.flush()


if __name__ == "__main__":
    asyncio.run(main())
