# examples/09_themes_async_demo.py

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import asyncio

from LogSmith.async_smartlogger import AsyncSmartLogger, a_stdout
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

    await a_stdout("\nAsync Themes demo\n=================")

    # ------------------------------------------------------------------------------------------------------
    # Create logger with console handler
    # ------------------------------------------------------------------------------------------------------
    logger = AsyncSmartLogger("themes_logger_async", levels["TRACE"])
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
    await a_stdout("\n--- LIGHT THEME ---")
    await demo_theme("light", LIGHT_THEME)

    await a_stdout("\n--- DARK THEME ---")
    await demo_theme("dark", DARK_THEME)

    await a_stdout("\n--- NEON THEME ---")
    await demo_theme("neon", NEON_THEME)

    await a_stdout("\n--- PASTEL THEME ---")
    await demo_theme("pastel", PASTEL_THEME)

    await a_stdout("\n--- FIRE THEME ---")
    await demo_theme("fire", FIRE_THEME)

    await a_stdout("\n--- OCEAN THEME ---")
    await demo_theme("ocean", OCEAN_THEME)

    await a_stdout("\n--- RESTORING DEFAULTS ---")
    await demo_theme("default", None)

    await a_stdout("\nAsync Themes demo complete.\n")

    # Ensure all logs are flushed
    await logger.flush()


if __name__ == "__main__":
    asyncio.run(main())
