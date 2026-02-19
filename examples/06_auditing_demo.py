# examples/auditing_demo.py

"""
Demonstrates SmartLogger auditing:
- Auditing captures ALL loggers' output into a single audit file (or file rotation)
- Works regardless of each logger's own handlers
- Supports rotation (size, time, or both)
- Shows how to enable and disable auditing cleanly
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
from typing import Dict

sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import time

from LogSmith import SmartLogger
from LogSmith import RotationLogic, When
from LogSmith import LogRecordDetails, OptionalRecordFields

from project_definitions import ROOT_DIR


# ----------------------------------------------------------------------------------------------------------
# 1. Initialization — MUST be done at application entry point
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["TRACE"])

print("\nAuditing demo\n=============")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 2. Prepare audit directory
# ----------------------------------------------------------------------------------------------------------
print("\nPreparing audit directory...")
time.sleep(0.1)

audit_dir = Path(ROOT_DIR) / "Logs" / "examples" / "auditing_demo"
audit_dir.mkdir(parents=True, exist_ok=True)

# Clean previous audit files
for f in audit_dir.iterdir():
    if f.is_file():
        f.unlink()

print("Old audit files removed.")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 3. Create several loggers with different handler setups
# ----------------------------------------------------------------------------------------------------------
print("\nCreating loggers...")
time.sleep(0.1)

loggers: Dict[str, SmartLogger] = {}

# 1. console only
lg1 = SmartLogger.get("demo.console_only", level=levels["INFO"])
lg1.add_console(level=levels["INFO"])
loggers["console_only"] = lg1

# 2. file only
lg2 = SmartLogger.get("demo.file_only", level=levels["INFO"])
lg2.add_file(
    log_dir=str(audit_dir / "file_only"),
    logfile_name="file_only.log",
    level=levels["INFO"],
)
loggers["file_only"] = lg2

# 3. console + file
lg3 = SmartLogger.get("demo.console_and_file", level=levels["INFO"])
lg3.add_console(level=levels["INFO"])
lg3.add_file(
    log_dir=str(audit_dir / "console_and_file"),
    logfile_name="console_and_file.log",
    level=levels["INFO"],
)
loggers["console_and_file"] = lg3

# 4. two file handlers
lg4 = SmartLogger.get("demo.two_files", level=levels["INFO"])
lg4.add_file(
    log_dir=str(audit_dir / "two_files_A"),
    logfile_name="A.log",
    level=levels["INFO"],
)
lg4.add_file(
    log_dir=str(audit_dir / "two_files_B"),
    logfile_name="B.log",
    level=levels["INFO"],
)
loggers["two_files"] = lg4

print("Loggers created.")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 4. Show logger configurations (JSON-safe)
# ----------------------------------------------------------------------------------------------------------
print("\nOutput Targets by logger \"<NAME>\":")
time.sleep(0.1)

for name, lg in loggers.items():
    print(f"\t\"{lg.name}\": ")
    for target in lg.output_targets:
        print(f"\t\t{target}")

time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 5. Enable auditing
# ----------------------------------------------------------------------------------------------------------
audit_details = LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S",
    separator="|",
    optional_record_fields=OptionalRecordFields(
        logger_name=True,   # auditing requires this
        lineno=True,
    ),
    message_parts_order=[
        "level",
        "logger_name",
        "lineno",
    ],
)

rotation = RotationLogic(
    maxBytes=3000,        # small size to demonstrate rotation
    when=When.SECOND,     # also rotate every second
    interval=1,
    backupCount=5,
)

print(f"\nEnabling auditing of 4 loggers... into '{audit_dir / 'audit.log'}'")
time.sleep(0.1)

SmartLogger.audit_everything(
    log_dir=str(audit_dir),
    logfile_name="audit.log",
    rotation_logic=rotation,
    details=audit_details,
)

print("Auditing enabled.")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 6. Exercise all loggers
# ----------------------------------------------------------------------------------------------------------
print("\nLogging from all loggers...")
time.sleep(0.1)

for name, lg in loggers.items():
    lg.info(f"[audit] logger '{name}' says hello")
    lg.warning(f"[audit] logger '{name}' warning example")
    lg.error(f"[audit] logger '{name}' error example")

# Give time-based rotation a chance to tick
time.sleep(1.2)


# ----------------------------------------------------------------------------------------------------------
# 7. Disable auditing
# ----------------------------------------------------------------------------------------------------------
print("\nDisabling auditing...")
time.sleep(0.1)

SmartLogger.terminate_auditing()

print("Auditing disabled.")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 8. Show audit handler info
# ----------------------------------------------------------------------------------------------------------
print("\nAudit handler info:")
time.sleep(0.1)

audit_logger = SmartLogger.get("_audit", levels["TRACE"])  # internal audit logger
print(audit_logger.handler_info_json)
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 9. Notes on adapting this demo
# ----------------------------------------------------------------------------------------------------------
print("\nNotes:")
time.sleep(0.1)

print(
    "- To demonstrate size-only rotation: remove 'when' and 'interval'.\n"
    "- To demonstrate time-only rotation: remove 'maxBytes'.\n"
    "- To demonstrate long-term rotation (daily/weekly):\n"
    "      use When.EVERYDAY or When.<WEEKDAY> and adjust timestamp.\n"
    "- Auditing captures ALL loggers (each handler once), regardless of their own handlers.\n"
)

print("\nAuditing demo complete.\n")
