# 📘 How to Use SmartLogger

This section provides a practical, code‑focused guide to SmartLogger, built directly from the examples in the `examples/` directory.  
Each subsection contains the essential code patterns you need to use SmartLogger effectively.

---

# 1. Initialization & Basic Logging

```python
from LogSmith import SmartLogger

levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["INFO"])

logger = SmartLogger.get("demo")
logger.add_console()

logger.trace("trace message")
logger.debug("debug message")
logger.info("info message")
logger.warning("warning message")
logger.error("error message")
logger.critical("critical message")
```

---

# 2. Formatting

```python
from LogSmith import LogRecordDetails, OptionalRecordFields

details = LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S",
    separator="•",
    optional_record_fields=OptionalRecordFields(
        process_id=True,
        thread_id=True,
    ),
    message_parts_order=[
        "process_id",
        "thread_id",
        "level",
    ],
    color_all_log_record_fields=True,
)

logger.add_console(log_record_details=details)
logger.info("Formatted message")
```

---

# 3. File Output

```python
from pathlib import Path
from project_definitions import ROOT_DIR

log_dir = Path(ROOT_DIR) / "Logs" / "file_demo"
log_dir.mkdir(parents=True, exist_ok=True)

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="output.log",
    log_record_details=details,
)

logger.info("This goes to console and file")
```

### Color‑preserving file output

```python
from LogSmith.colors import CPrint

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="color.log",
    do_not_sanitize_colors_from_string=True,
)

colored = CPrint.colorize("Colored text", fg=CPrint.FG.BRIGHT_MAGENTA)
logger.raw(colored)
```

---

# 4. Rotation

```python
from LogSmith import RotationLogic, When

rotation = RotationLogic(
    maxBytes=2000,  # size-based
    when=When.SECOND,  # time-based
    interval=1,
    backupCount=5,
)

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="rotating.log",
    rotation_logic=rotation,
)
```

---

# 5. Hierarchy

```python
parent = SmartLogger.get("myapp", level=levels["DEBUG"])
child = SmartLogger.get("myapp.api", level=levels["NOTSET"])
grandchild = SmartLogger.get("myapp.api.users", level=levels["NOTSET"])

parent.add_console()
child.add_console()
grandchild.add_console()

parent.debug("parent")
child.debug("child inherits DEBUG")
grandchild.debug("grandchild inherits DEBUG")

parent.setLevel(levels["WARNING"])
grandchild.debug("now suppressed")
grandchild.warning("now visible")
```

---

# 6. Auditing

```python
from LogSmith import RotationLogic, When, LogRecordDetails, OptionalRecordFields

audit_details = LogRecordDetails(
    optional_record_fields=OptionalRecordFields(
        logger_name=True,
        lineno=True,
    ),
    message_parts_order=["level", "logger_name", "lineno"],
)

rotation = RotationLogic(
    maxBytes=3000,
    when=When.SECOND,
    interval=1,
    backupCount=5,
)

SmartLogger.audit_everything(
    log_dir="absolute/path/to/audit",
    logfile_name="audit.log",
    rotation_logic=rotation,
    details=audit_details,
)

logger.info("This will appear in the audit log")

SmartLogger.terminate_auditing()
```

---

# 7. Themes

```python
from LogSmith import NEON_THEME

SmartLogger.apply_color_theme(NEON_THEME)

logger = SmartLogger.get("themes")
logger.add_console()

logger.info("Neon theme active")
```

Restore defaults:

```python
SmartLogger.apply_color_theme(None)
```

---

# 8. Gradients

```python
from LogSmith.colors import CPrint, GradientPalette, GradientDirection

logger.raw(
    CPrint.gradient(
        "Rainbow gradient",
        fg_codes=GradientPalette.RAINBOW,
    )
)

logger.raw(
    CPrint.gradient(
        "Vertical gradient\nLine 2\nLine 3",
        fg_codes=[GradientPalette.CYAN, GradientPalette.MAGENTA, GradientPalette.BLUE],
        direction=GradientDirection.VERTICAL,
    )
)
```

Palette blending:

```python
from LogSmith.colors import blend_palettes

tropical = blend_palettes(GradientPalette.SUNSET, GradientPalette.OCEAN)
logger.raw(CPrint.gradient("Tropical", fg_codes=tropical))
```

---

# 9. Diagnostics & Safeguards

## get_record()

```python
logger.info("test")
record = logger.get_record()
print(record.__dict__)
```

## exc_info and stack_info

```python
details = LogRecordDetails(
    optional_record_fields=OptionalRecordFields(
        exc_info=True,
        stack_info=True,
    ),
    message_parts_order=None,
)

logger.add_console(log_record_details=details)

try:
    1 / 0
except ZeroDivisionError:
    logger.error("Exception occurred", exc_info=True)

logger.debug("Stack info example", stack_info=True)
```

## retire() and destroy()

```python
temp = SmartLogger.get("temp")
temp.add_console()

temp.retire()
temp.destroy()
```

## Invalid configurations (examples)

```python
# invalid message_parts_order
LogRecordDetails(message_parts_order=["timestamp"])

# invalid log_dir
logger.add_file(log_dir="relative/path")

# invalid rotation
RotationLogic(maxBytes=-1)

# invalid level registration
SmartLogger.register_level("INFO", 20)

# invalid theme
SmartLogger.apply_color_theme({"INFO": "not a LevelStyle"})
```

---

# 10. Stress Test (Thread Safety)

```python
import threading

def worker(i):
    for n in range(1000):
        logger.info(f"[{i}] message {n}")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(32)]

for t in threads: t.start()
for t in threads: t.join()
```

---

# ✔ Summary

This section provides all essential SmartLogger usage patterns:

- Initialization  
- Formatting  
- File output  
- Rotation  
- Hierarchy  
- Auditing  
- Themes  
- Gradients  
- Diagnostics  
- Safeguards  
- Thread safety  

Each code block is directly derived from the runnable examples in the repository.
