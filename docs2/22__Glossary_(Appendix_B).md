# Appendix B — 📖 Glossary  
This glossary defines all key terms used throughout the LogSmith documentation. It serves as a quick reference for concepts, components, and terminology that appear across the system.

---

# A
```
ANSI                       —  Terminal escape‑code standard used for colors, styles, and gradients.
ANSI Sanitization          —  Removal of ANSI codes before writing to files to prevent corruption or ingestion issues.
Append Filename PID        —  Rotation option that appends the current process ID to the log filename.
Append Filename Timestamp  —  Rotation option that appends a timestamp to the log filename.
Async Logging              —  Logging model where events are queued and processed by a background worker.
Async Rotation             —  Rotation performed outside the main event loop by AsyncSmartLogger’s worker.
Audit Log                  —  A global log capturing all log events from all loggers.
Audit Handler              —  A handler used to collect all log events during auditing.

```
---

# B
```
Backup Count                 —  Maximum number of rotated log files retained before older ones are deleted.
Bleaching (Color Bleaching)  —  Process of recoloring non‑ANSI text to console default while preserving ANSI segments.
```

---

# C
```
CPrint               —  LogSmith’s ANSI color engine for solid colors, gradients, and style effects.
Caller Resolution    —  Determining the file, line, and function where a log call originated.
Color Theme          —  Mapping of log levels to LevelStyle objects.
Console Handler      —  Handler that outputs logs to stdout with optional color and structured formatting.
Concurrent Rotation  —  Rotation mechanism safe for multi‑process and multi‑threaded environments.
Critical Level       —  Highest built‑in severity level.
```

---

# D
```
Date Format (datefmt)  —  Formatting string controlling timestamp appearance.
Diagnostics Fields     —  Optional fields such as `exc_info` and `stack_info`.
Dynamic Level          —  User‑defined log level created at runtime.
```

---

# E
```
Effective Level  —  Final log level used after applying inheritance rules.
Emit             —  Handler method responsible for writing a formatted log record.
Expiration Rule  —  Retention policy for deleting rotated files based on age.
```

---

# F
```
File Handler                —  Handler that writes logs to a file with optional rotation and retention.
Fields (Structured Fields)  —  Named arguments passed to log methods that appear as key‑value pairs.
Flush                       —  Ensuring all queued or buffered log events are written before shutdown.
```

---

# G
```
Gradient          —  Multi‑color ANSI effect applied across text.
Gradient Palette  —  List of ANSI color indices used to generate gradients.
```

---

# H
```
Handler          —  Component responsible for outputting log entries to a destination.
Handler Info     —  Metadata describing a handler’s configuration.
Hybrid Rotation  —  Rotation triggered by either size or time thresholds.
```

---

# I
```
Inheritance (Level Inheritance)  —  Mechanism where a logger without an explicit level inherits from its parent.
Interval (Rotation Interval)     —  Time between scheduled rotations for SECOND/MINUTE/HOUR modes.
```

---

# J
```
JSON Output — Structured JSON representation of log entries.
```

---

# L
```
Level                 —  Numeric severity value associated with a log message.
Level Registry        —  Internal registry storing all built‑in and dynamic log levels.
LevelStyle            —  Color/style configuration for a log level.
Line Number (lineno)  —  Metadata field indicating the source line of the log call.
LogRecordDetails      —  Configuration object controlling structured formatting.
```

---

# M
```
Message Parts Order  —  Ordering of metadata fields in structured output.
Metadata Fields      —  Optional fields such as logger name, file name, thread ID, etc.
Module Name          —  Name of the module emitting the log (optional field).
```

---

# N
```
NDJSON  —  Newline‑Delimited JSON format for ingestion pipelines.
NOTSET  —  Special level indicating inheritance from parent logger.
```

---

# O
```
Output Mode           —  Formatting mode: COLOR, PLAIN, JSON, NDJSON.
OptionalRecordFields  —  Configuration object enabling/disabling metadata fields.
```

---

# P
```
Passthrough Formatter      —  Formatter that preserves ANSI codes and outputs raw messages.
Process ID / Process Name  —  Metadata fields indicating the emitting process.
Propagation                —  Forwarding log events to parent loggers (enabled only during auditing).
```

---

# Q
```
Queue (Async Queue)  —  Internal queue used by AsyncSmartLogger to buffer log events.
Queue Depth          —  Number of pending log events in the async queue.
```

---

# R
```
Raw Output          —  Unformatted text written directly to handlers.
Record (LogRecord)  —  Internal Python object representing a single log event.
Relative Created    —  Time in milliseconds since the logging system was initialized.
Retention           —  Policy controlling how long rotated files are kept.
Rotation            —  Process of renaming and replacing log files when thresholds are reached.
Rotation Logic      —  Configuration object defining rotation rules.
Rotation Timestamp  —  Time‑of‑day anchor for daily/weekly rotation.
```

---

# S
```
Sanitization                 —  Removal of ANSI codes from file output.
Separator                    —  Character used to separate metadata fields in structured output.
Should Rotate                —  Decision logic determining whether rotation should occur.
SmartLogger                  —  Primary synchronous logger class.
Stack Info                   —  Optional metadata containing a captured stack trace.
Structured Formatting        —  Formatting model using explicit configuration instead of format strings.
Structured JSON Formatter    —  Formatter producing JSON output.
Structured NDJSON Formatter  —  Formatter producing newline‑delimited JSON.
Structured Plain Formatter   —  Formatter producing plain structured text.
```

---

# T
```
Task Name                —  Asyncio task name included in async log records.
Theme                    —  Mapping of log levels to LevelStyle objects.
Thread ID / Thread Name  —  Metadata fields indicating the emitting thread.
Timestamp Anchor         —  Specific time used for scheduled rotation.
Trace Level              —  Lowest built‑in severity level (TRACE = 5).
```

---

# U
```
User Fields — Custom structured fields provided via named arguments.
```

---

# V
```
Verbose Level — Common dynamic level used for detailed logs.
```

---

# W
```
When         —  Enum defining time‑based rotation intervals.
Worker Task  —  Background task in AsyncSmartLogger that processes queued log events.
```

---

# 📘 Summary  
This glossary is a complete reference to all terminology used throughout LogSmith, covering synchronous and asynchronous logging, formatting, rotation, retention, colors, themes, auditing, and internal mechanics.
It ensures that every concept appearing in the documentation has a clear and accessible definition.
