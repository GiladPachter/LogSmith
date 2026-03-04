# examples/auditing_demo.py

"""
Demonstrates SmartLogger auditing:
- Auditing captures ALL loggers' output into a single audit file (or file rotation)
- Works regardless of each logger's own handlers
- Supports rotation (size, time, or both)
- Shows how to enable and disable auditing cleanly
"""
import json
# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Dict

from LogSmith import SmartLogger, stdout
from LogSmith import RotationLogic, When
from LogSmith import LogRecordDetails, OptionalRecordFields

from project_definitions import ROOT_DIR

# ----------------------------------------------------------------------------------------------------------
# 1. Initialization
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()

stdout("\nAuditing demo\n=============")

# ----------------------------------------------------------------------------------------------------------
# 2. Prepare audit directory
# ----------------------------------------------------------------------------------------------------------
stdout("\nPreparing audit directory...")

audit_dir = Path(ROOT_DIR) / "Logs" / "examples" / "auditing_demo"
audit_dir.mkdir(parents=True, exist_ok=True)

# Clean previous audit files
for f in audit_dir.iterdir():
    if f.is_file():
        f.unlink()

stdout("Old audit files removed.")

# ----------------------------------------------------------------------------------------------------------
# 3. Create several loggers with different handler setups
# ----------------------------------------------------------------------------------------------------------
stdout("\nCreating loggers...")

loggers: Dict[str, SmartLogger] = {}

# 1. console only
lg1 = SmartLogger("demo.console_only", level=levels["INFO"])
lg1.add_console(level=levels["INFO"])
loggers["console_only"] = lg1

# 2. file only
lg2 = SmartLogger("demo.file_only", level=levels["INFO"])
lg2.add_file(
    log_dir=str(audit_dir / "file_only"),
    logfile_name="file_only.log",
    level=levels["INFO"],
)
loggers["file_only"] = lg2

# 3. console + file
lg3 = SmartLogger("demo.console_and_file", level=levels["INFO"])
lg3.add_console(level=levels["INFO"])
lg3.add_file(
    log_dir=str(audit_dir / "console_and_file"),
    logfile_name="console_and_file.log",
    level=levels["INFO"],
)
loggers["console_and_file"] = lg3

# 4. two file handlers
lg4 = SmartLogger("demo.two_files", level=levels["INFO"])
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

stdout("Loggers created.")

# ----------------------------------------------------------------------------------------------------------
# 4. Show logger configurations (JSON-safe)
# ----------------------------------------------------------------------------------------------------------
stdout("\nOutput Targets by logger \"<NAME>\":")

for name, lg in loggers.items():
    stdout(f"\t\"{lg.name}\": ")
    for target in lg.output_targets:
        stdout(f"\t\t{target}")

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

stdout(f"\nEnabling auditing of 4 loggers... into '{audit_dir / 'audit.log'}'")

SmartLogger.audit_everything(
    log_dir=str(audit_dir),
    logfile_name="audit.log",
    rotation_logic=rotation,
    details=audit_details,
)

stdout("Auditing enabled.")

# ----------------------------------------------------------------------------------------------------------
# 6. Exercise all loggers
# ----------------------------------------------------------------------------------------------------------
stdout("\nLogging from all loggers...")

for name, lg in loggers.items():
    lg.info(f"[audit] logger '{name}' says hello")
    lg.warning(f"[audit] logger '{name}' warning example")
    lg.error(f"[audit] logger '{name}' error example")

# ----------------------------------------------------------------------------------------------------------
# 7. Disable auditing
# ----------------------------------------------------------------------------------------------------------
stdout("\nActive audit_handler_info:")
stdout(json.dumps(SmartLogger.audit_handler_info(), indent = 4))

stdout("\nDisabling auditing...")
SmartLogger.terminate_auditing()
stdout("Auditing disabled.")

stdout("\nDead audit_handler_info:")
stdout(json.dumps(SmartLogger.audit_handler_info(), indent = 4))


# ----------------------------------------------------------------------------------------------------------
# 8. Notes on adapting this demo
# ----------------------------------------------------------------------------------------------------------
stdout("\nNotes:\n"
      "- To demonstrate size-only rotation: remove 'when' and 'interval'.\n"
      "- To demonstrate time-only rotation: remove 'maxBytes'.\n"
      "- To demonstrate long-term rotation (daily/weekly):\n"
      "      use When.EVERYDAY or When.<WEEKDAY> and adjust timestamp.\n"
      "- Auditing captures ALL loggers (each logger once), regardless of their own handlers.\n"
      "\n"
      "Auditing demo complete.\n")
