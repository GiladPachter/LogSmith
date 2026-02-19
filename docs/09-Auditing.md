# 🛰️ Global Auditing

SmartLogger includes a **global auditing system** that captures every log record emitted by **any** SmartLogger instance and duplicates it into a single audit log file.

Auditing is ideal for:

- security logging
- compliance
- debugging distributed systems
- capturing logs from multiple modules
- centralizing output from many loggers

Auditing is **opt‑in**, and can be enabled or disabled at any time.

---

## 🔹 Enabling Auditing

```python
from LogSmith import SmartLogger, RotationLogic

SmartLogger.audit_everything(
    log_dir="audit",
    logfile_name="audit.log",
    rotation_logic=RotationLogic(maxBytes=50_000, backupCount=5),
)
```

This:

- attaches an audit handler to the **root logger**
- enables propagation on all SmartLogger instances
- formats entries independent of formatters attached to any of the audited logger
- preserves ANSI colors
- supports rotation and retention

---

## 🔹 What Gets Logged?

**Everything** emitted by any SmartLogger instance:

- console‑only loggers
- file‑only loggers
- loggers with multiple handlers
- loggers created before or after auditing begins

Auditing **does not** interfere with existing handlers — it simply duplicates the records.

---

## 🔹 Disabling Auditing

```python
SmartLogger.terminate_auditing()
```

This:
- removes the audit handler from the root logger
- disables propagation on all SmartLogger instances
- restores normal logging behavior

---

## 🔹 Audit Log Formatting

Audit logs use `AuditFormatter`, which:

- prefixes each entry with its source logger name
- uses its own `LogRecordDetails`

Example:

```
[demo.console_only]: 2024-02-10 21:30:45 • INFO • Hello from demo
```

---

## 🔹 Using Custom Formatting for Auditing

```python
details = LogRecordDetails(
    optional_record_fields = OptionalRecordFields(
        file_path = True,
        func_name = True,
        lineno = True,
    ),
    message_parts_order = [
        "file_path",
        "func_name",
        "lineno",
        "level",
    ],
)

SmartLogger.audit_everything(
    log_dir = "audit",
    logfile_name = "audit.log",
    details = details,
)
```

This allows full control over:
- timestamp format
- optional fields
- ordering
- separators
- color behavior

---

## 🔹 Auditing + Rotation + Retention

Auditing supports:

- size‑based rotation
- time‑based rotation
- hybrid rotation
- retention policies

Example:

```python
rotation = RotationLogic(
    when = When.SECOND,
    interval = 1,
    backupCount = 50,
)
```

Audit logs rotate independently of other handlers.

---

## 🔹 How auditing works

SmartLogger can audit:

- console‑only loggers
- file‑only loggers
- loggers with multiple handlers
- loggers with no handlers

From the demo:

```
console_only
file_only
console_and_file
two_files
```

All four loggers propagate to:

```
audit/audit.log
```

---

# 🧩 Summary

SmartLogger’s auditing system provides:

- centralized logging for all SmartLogger instances
- ANSI‑preserving audit output
- structured formatting
- rotation and retention
- safe enable / disable at runtime
- zero interference with existing handlers

This makes auditing ideal for production systems that require unified log capture.
