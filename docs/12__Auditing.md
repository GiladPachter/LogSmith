# 🛰️ Auditing  
Auditing is LogSmith’s mechanism for capturing **all logs from all loggers** into a single unified audit file. It is designed for security‑sensitive environments, debugging large systems, compliance logging, and any situation where you need a complete, authoritative record of everything the application emits.

This chapter explains how auditing works, how to enable it, how it interacts with logger hierarchy, and how it behaves in both synchronous and asynchronous applications.

---

## 💡 Purpose of Auditing
Auditing solves several real‑world problems:

- capturing logs from *every* logger, even those you didn’t create  
- enforcing a single, centralized audit trail  
- ensuring logs cannot be silently dropped  
- providing a complete chronological record  
- enabling compliance and forensic logging  
- debugging large applications with many modules  

Auditing is **opt‑in** and must be enabled explicitly.

---

## 🧬 How Auditing Works

When auditing is enabled:

1. A dedicated audit handler is attached to the root logger.  
2. All SmartLogger instances have propagation enabled.  
3. Every log record flows into the audit handler.  
4. The audit handler uses `AuditFormatter` for strict, structured output.  
5. Rotation and retention apply normally.  

Auditing does **not** modify existing handlers — it adds a global sink.

Console handlers remain unaffected unless you explicitly add them.

---

## ▶️ Enabling Auditing (Sync)

Enable auditing for SmartLogger:

```python
from LogSmith import SmartLogger

SmartLogger.audit_everything(
    log_dir      = "audit",
    logfile_name = "audit.log",
)
```

This:

- creates `audit/audit.log`  
- attaches a global audit handler  
- enables propagation for all SmartLogger instances  
- ensures every log entry flows into the audit file  

You can still attach normal handlers to individual loggers.

---

## ▶️ Enabling Auditing (Async)

AsyncSmartLogger includes an async‑aware auditing system:

```python
from LogSmith import AsyncSmartLogger

await AsyncSmartLogger.audit_everything(
    log_dir="audit",
    logfile_name="audit_async.log",
)
```

This creates a dedicated **AsyncSmartLogger audit logger** that:

- receives all log events  
- writes them in order  
- performs rotation in a thread pool  
- flushes cleanly on shutdown  

The audit logger has its own queue and worker.

---

## 🧾 Audit Formatter

Audit logs use a special formatter optimized for:

- machine parsing  
- chronological analysis  
- security auditing  
- ingestion pipelines  

`AuditFormatter` wraps either:

- `StructuredPlainFormatter` (default), or  
- `StructuredNDJSONFormatter` (if `NDJSON_output=True`)  

Audit entries include:

- timestamp  
- level  
- logger name  
- message  
- structured fields (`named_args`)  
- file path, file name, line number  
- function name  
- thread and process IDs  
- exception information  
- stack info (if enabled)  

Audit formatting is intentionally strict and consistent.

---

## 🔄 Audit File Rotation

Audit files support full rotation:

```python
SmartLogger.audit_everything(
    log_dir = "audit",
    logfile_name = "audit.log",
    rotation_logic = RotationLogic(
        maxBytes    = 50_000,
        backupCount = 10,
    ),
)
```

Rotated audit files remain valid structured logs.  
Retention rules apply normally.

Rotation is concurrency‑safe and identical to standard file handlers.

---

## 🧾 Audit + JSON / NDJSON

Audit handlers do **not** use the regular JSON/NDJSON output modes.

Instead:

- `AuditFormatter` always produces structured plain text  
- unless `NDJSON_output=True`, in which case it produces NDJSON  

Example:

```python
SmartLogger.audit_everything(
    log_dir        = "audit",
    logfile_name   = "audit.ndjson",
    rotation_logic = RotationLogic(maxBytes=50_000),
    output_mode    = OutputMode.NDJSON,
)
```

This is ideal for:

- ELK  
- Loki  
- BigQuery  
- SIEM pipelines  
- Compliance frameworks  

Each line is a standalone JSON object.

---

## 🚫 Audit + Raw Output

Audit handlers **ignore raw output**.

Raw output is intended for console‑only use and is not included in audit files.  
This ensures audit logs remain clean, structured, and machine‑friendly.

---

## 🛑 Disabling Auditing

Disable auditing cleanly:

### Sync:

```python
SmartLogger.terminate_auditing()
```

### Async:

```python
await AsyncSmartLogger.terminate_auditing()
```

This:

- flushes the audit queue  
- closes the audit file  
- removes the audit handler  
- restores normal propagation behavior  

---

## 🌳 Auditing and Logger Hierarchy

When auditing is enabled:

- all SmartLogger instances propagate upward  
- the audit handler becomes the global sink  
- individual handlers still work normally  
- logger levels still apply  
- dynamic levels are included automatically  

Auditing does **not** change how loggers behave — it only adds a global listener.

---

## 🧵 Auditing in Multi‑Process Environments

Audit files are concurrency‑safe:

- `fcntl` locks on Unix  
- `msvcrt` locks on Windows  
- atomic renaming  
- safe rotation  

However:

- On **Windows**, multiple processes should not write to the same audit file.  
- Use per‑process audit files if needed.

Async audit logging is safe across tasks but not across processes.

---

## 🎯 When to Use Auditing

Auditing is ideal for:

- production services  
- security‑sensitive systems  
- financial or medical applications  
- debugging large async systems  
- compliance logging  
- forensic analysis  
- capturing logs from third‑party libraries  

Avoid auditing when:

- performance is extremely sensitive  
- you only need per‑module logs  
- you want minimal disk usage  

---

## 📘 Summary

Auditing provides:

- a unified audit file for all loggers  
- strict, structured formatting  
- rotation and retention  
- async‑aware behavior  
- concurrency‑safe writes  
- NDJSON support via `NDJSON_output=True`  
- clean enable/disable lifecycle  
