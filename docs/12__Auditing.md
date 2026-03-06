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

1. All loggers propagate upward to the root audit logger.  
2. The audit logger writes to a dedicated audit file.  
3. The audit file uses a special `AuditFormatter`.  
4. Rotation and retention apply normally.  
5. Console handlers are unaffected unless you choose otherwise.  

Auditing does **not** modify existing handlers — it adds a new global sink.

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
- enables propagation for all loggers  
- ensures every log entry flows into the audit file  

You can still attach normal handlers to individual loggers.

---

## ▶️ Enabling Auditing (Async)

AsyncSmartLogger includes an async‑aware auditing system:

```python
from LogSmith import AsyncSmartLogger

AsyncSmartLogger.audit_everything(
    log_dir      = "audit",
    logfile_name = "audit_async.log",
)
```

This creates a dedicated async audit worker that:

- receives all log events  
- writes them in order  
- performs rotation in a thread pool  
- flushes cleanly on shutdown

---

## 🧾 Audit Formatter
Audit logs use a special formatter optimized for:

- machine parsing  
- chronological analysis  
- security auditing  
- ingestion pipelines  

Audit entries include:

- timestamp  
- level  
- logger name  
- message  
- structured fields  
- file, line, and function  
- thread and process IDs  
- exception information  

Audit formatting is intentionally strict and consistent to ensure reliable ingestion.

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

Rotated audit files remain valid structured logs, and retention rules apply normally. Rotation is concurrency‑safe and works identically to standard file handlers.

---

## 🧾 Audit + JSON / NDJSON

Audit handlers can output JSON or NDJSON:

```python
SmartLogger.audit_everything(
    log_dir      = "audit",
    logfile_name = "audit.ndjson",
    output_mode  = OutputMode.NDJSON,
)
```

This is ideal for:

- ELK  
- Loki  
- BigQuery  
- SIEM pipelines  
- Compliance frameworks.
Each line is a standalone JSON object, making it easy to stream and index.

---

## 🚫 Audit + Raw Output

Audit handlers ignore raw output.<br/>
> >Raw output is intended for console‑only use and is not included in audit files. This ensures audit logs remain clean, structured, and machine‑friendly.

---

## 🛑 Disabling Auditing

Disable auditing cleanly:

```python
SmartLogger.stop_auditing()
```

Async version:

```python
await AsyncSmartLogger.stop_auditing()
```

This:

- flushes the audit queue  
- closes the audit file  
- removes the audit handler  
- restores normal propagation behavior  

---

## 🌳 Auditing and Logger Hierarchy

When auditing is enabled:

- all loggers propagate upward  
- the audit logger becomes the root sink  
- individual handlers still work normally  
- logger levels still apply  
- dynamic levels are included automatically  

Auditing does **not** change how loggers behave — it only adds a global listener.

---

## 🧵 Auditing in Multi‑Process Environments

Audit files are concurrency‑safe:

- fcntl locks on Unix  
- msvcrt locks on Windows  
- atomic renaming  
- safe rotation  

However, on Windows, multiple processes should not write to the same audit file. Use per‑process audit files if needed.

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
- JSON / NDJSON support  
- clean enable/disable lifecycle  
