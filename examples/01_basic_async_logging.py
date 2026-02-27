# examples/01_basic_async_logging.py

"""
Basic demonstration of AsyncSmartLogger:
- Initialization (async-friendly)
- Creating an async logger
- Basic async log messages
- Named arguments (structured fields)
- Dynamic level registration
- RAW text (plain + colored)
- Synchronization between print() and async logger output
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import asyncio
import json

from LogSmith import CPrint, LevelStyle
from LogSmith import AsyncSmartLogger, a_stdout


async def main():
    # ------------------------------------------------------------------------------------------------------
    # 1. Initialization — AsyncSmartLogger does not require global init
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    await a_stdout("\nBuiltin async logger levels:")
    await a_stdout(json.dumps(levels, indent=4))

    # ------------------------------------------------------------------------------------------------------
    # 2. Create an async logger and attach a console handler
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nCreating async logger 'basic_async'...\n")

    logger = AsyncSmartLogger("basic_async", level=levels["TRACE"])
    logger.add_console(level=levels["TRACE"])

    # ------------------------------------------------------------------------------------------------------
    # 3. Basic async log messages
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nBasic async log messages:\n-------------------------")

    await logger.a_trace("trace message")
    await logger.a_debug("debug message")
    await logger.a_info("info message")
    await logger.a_warning("warning message")
    await logger.a_error("error message")
    await logger.a_critical("critical message")

    # ------------------------------------------------------------------------------------------------------
    # 4. Named arguments (structured message parameters)
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nMessages with named arguments:\n------------------------------")

    await logger.a_info("User login event", username="Gilad", action="login")
    await logger.a_warning("Suspicious activity detected", reason="multiple failed attempts")

    # ------------------------------------------------------------------------------------------------------
    # 5. Dynamic level registration
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nRegistering new logging levels on-the-fly:\n------------------------------------------")

    AsyncSmartLogger.register_level(
        name="NOTICE",
        value=25,
        style=LevelStyle(fg=CPrint.FG.BRIGHT_MAGENTA, intensity=CPrint.Intensity.BOLD),
    )
    await logger.a_notice("This is a NOTICE-level message")

    AsyncSmartLogger.register_level(
        name="ALERT",
        value=45,
        style=LevelStyle(
            fg=CPrint.FG.BRIGHT_YELLOW,
            bg=CPrint.BG.RED,
            intensity=CPrint.Intensity.BOLD,
        ),
    )
    await logger.a_alert("This is an ALERT-level message")

    await a_stdout("\nExpanded logger levels:")
    levels = AsyncSmartLogger.levels()
    sorted_levels = dict(sorted(levels.items(), key=lambda item: item[1]))
    await a_stdout(json.dumps(sorted_levels, indent=4))

    # ------------------------------------------------------------------------------------------------------
    # 6. RAW text (plain + colored)
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nRAW text output:\n----------------")

    await logger.a_raw(
        "AsyncSmartLogger can log raw text (no formatting, no prefix)."
        "\nRAW text syncs perfectly with other async logging operations."
        "\nNote: DON'T SPAM !"
        "\n      Meaning, don't use logger.a_raw() as a replacement for print()"
        "\n      It's not good practice to call logger.a_raw() if your logger writes to a log file meant for parsing."
        "\n      Use logger.a_raw() only when you intentionally break the structured log format."
    )

    await a_stdout("\nRAW colored text:\n------------------")

    colored = [
        CPrint.colorize("RAW",      fg=CPrint.FG.BRIGHT_RED),
        CPrint.colorize("text",     fg=CPrint.FG.ORANGE),
        CPrint.colorize("rocks",    fg=CPrint.FG.BRIGHT_YELLOW),
        CPrint.colorize("in",       fg=CPrint.FG.BRIGHT_GREEN),
        CPrint.colorize("multiple", fg=CPrint.FG.BRIGHT_BLUE),
        CPrint.colorize("colors",   fg=CPrint.FG.SOFT_PURPLE),
    ]

    await logger.a_raw(" ".join(colored))

    # ------------------------------------------------------------------------------------------------------
    # 7. Safeguards & validations (informational)
    # ------------------------------------------------------------------------------------------------------
    await a_stdout(
        "\nAsyncSmartLogger safeguards:"
        "\n----------------------------\n"
        "- Prevents duplicate handlers\n"
        "- Validates log_dir paths (absolute + normalized)\n"
        "- Ensures consistent async behavior\n"
        "\n\n"
        "Basic async logging demo complete."
    )

    # Ensure all logs are flushed before exit
    await logger.flush()


if __name__ == "__main__":
    asyncio.run(main())