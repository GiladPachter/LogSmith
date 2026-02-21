# examples/01_basic_logging.py

"""
Basic demonstration of LogSmith:
- Initialization (critically important)
- Creating a logger
- Basic log messages
- Named arguments
- Dynamic level registration
- RAW text (plain + colored)
- Synchronization between print() and logger output
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import time
import json

from LogSmith import SmartLogger, CPrint, LevelStyle

# ----------------------------------------------------------------------------------------------------------
# 1. Initialization — MUST be done at application entry point
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["TRACE"])

print("\nBuiltin logger levels:")
print(json.dumps(levels, indent = 4))

# ----------------------------------------------------------------------------------------------------------
# 2. Create a logger and attach a console handler
# ----------------------------------------------------------------------------------------------------------
print("\nCreating logger 'basic'...\n")
logger = SmartLogger.get("basic", level=levels["TRACE"])
logger.add_console(level=levels["TRACE"])

# NOTE:
# print() writes to stdout, SmartLogger console writes to stderr.
# To avoid interleaving, we add tiny sleeps before/after print().
time.sleep(0.1)

# ----------------------------------------------------------------------------------------------------------
# 3. Basic log messages
# ----------------------------------------------------------------------------------------------------------
print("\nBasic log messages:\n-------------------")
time.sleep(0.1)

logger.trace("trace message")
logger.debug("debug message")
logger.info("info message")
logger.warning("warning message")
logger.error("error message")
logger.critical("critical message")

# ----------------------------------------------------------------------------------------------------------
# 4. Named arguments (structured message parameters)
# ----------------------------------------------------------------------------------------------------------
time.sleep(0.1)
print("\nMessages with named arguments:\n------------------------------")
time.sleep(0.1)

logger.info("User login event", username="Gilad", action="login")
logger.warning("Suspicious activity detected", reason="multiple failed attempts")

# ----------------------------------------------------------------------------------------------------------
# 5. Dynamic level registration
# ----------------------------------------------------------------------------------------------------------
time.sleep(0.1)
print("\nRegistering new logging levels on-the-fly:\n------------------------------------------")
time.sleep(0.1)

SmartLogger.register_level(
    name="NOTICE",
    value=25,
    style=LevelStyle(fg=CPrint.FG.BRIGHT_MAGENTA, intensity=CPrint.Intensity.BOLD),
)
logger.notice("This is a NOTICE-level message")

SmartLogger.register_level(
    name="ALERT",
    value=45,
    style=LevelStyle(
        fg=CPrint.FG.BRIGHT_YELLOW,
        bg=CPrint.BG.RED,
        intensity=CPrint.Intensity.BOLD,
    ),
)
logger.alert("This is an ALERT-level message")

# ----------------------------------------------------------------------------------------------------------
# 6. RAW text (plain + colored)
# ----------------------------------------------------------------------------------------------------------
time.sleep(0.1)
print("\nRAW text output:\n----------------")
time.sleep(0.1)
logger.raw("SmartLogger loggers can log raw text (no formatting, no prefix)."
           "\nRAW text syncs perfectly with other logging operations."
           "\nNote: DON'T SPAM !"
           "\n      Meaning, don't use logger.raw() as convenient replacement for print()"
           "\n      It's not good practice to call logger.raw() if your logger writes to a log file meant for parsing later on."
           "\n      Use logger.raw() only in cases where you intentionally..."
           "\n      ...mean for your log file to break the typical structure of   line = log-entry")

time.sleep(0.1)
print("\nRAW colored text:\n------------------")
time.sleep(0.1)

colored = [
    CPrint.colorize("RAW",      fg=CPrint.FG.BRIGHT_RED),
    CPrint.colorize("text",     fg=CPrint.FG.ORANGE),
    CPrint.colorize("rocks",    fg=CPrint.FG.BRIGHT_YELLOW),
    CPrint.colorize("in",       fg=CPrint.FG.BRIGHT_GREEN),
    CPrint.colorize("multiple", fg=CPrint.FG.BRIGHT_BLUE),
    CPrint.colorize("colors",   fg=CPrint.FG.SOFT_PURPLE)
]

logger.raw(" ".join(colored))

# ----------------------------------------------------------------------------------------------------------
# 7. Safeguards & validations (informational)
# ----------------------------------------------------------------------------------------------------------
time.sleep(0.1)
print("\nSmartLogger safeguards:"
      "\n-----------------------\n"
      "- Prevents duplicate handlers\n"
      "- Validates log_dir paths (absolute + normalized)\n"
      "- Ensures consistent initialization\n"
      "\n\n"
      "Basic logging demo complete."
      )
