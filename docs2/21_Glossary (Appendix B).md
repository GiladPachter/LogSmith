# Appendix B — Glossary  
This glossary defines all key terms used throughout the LogSmith documentation. It serves as a quick reference for concepts, components, and terminology that appear across the system.

---

# A

### **ANSI**
A standard for terminal color and formatting codes used to colorize console output.

### **Async Logging**
A logging model where log events are queued and processed by a background worker, preventing blocking in asyncio applications.

### **Audit Log**
A global log file that captures all log events from all loggers, used for compliance, debugging, and forensics.

---

# B

### **Backup Count**
The maximum number of rotated log files to keep before older ones are deleted.

---

# C

### **CPrint**
LogSmith’s ANSI color engine, responsible for colorizing text, applying styles, and generating gradients.

### **Console Handler**
A handler that writes logs to the terminal, optionally with color and structured formatting.

### **Critical Level**
The highest built‑in log level, used for severe errors requiring immediate attention.

---

# D

### **Dynamic Level**
A user‑defined log level created at runtime, complete with its own name, numeric value, and logger method.

### **Date Format (datefmt)**
A formatting string that controls how timestamps appear in log entries.

---

# E

### **Effective Level**
The final log level used by a logger, determined by its explicit level or inherited from its parent.

### **Expiration Rule**
A retention policy that deletes rotated files older than a specified time interval.

---

# F

### **File Handler**
A handler that writes logs to a file, optionally with rotation, retention, and structured formatting.

### **Flush**
The process of ensuring all queued or buffered log events are written to disk before shutdown.

---

# G

### **Gradient**
A multi‑color ANSI effect applied to text, often used in banners or decorative output.

### **Gradient Palette**
A predefined or custom list of ANSI color codes used to generate gradients.

---

# H

### **Handler**
A component responsible for outputting log entries to a destination (console, file, audit file, etc.).

### **Hybrid Rotation**
A rotation mode where logs rotate when either a size threshold OR a time interval is reached.

---

# I

### **Inheritance (Level Inheritance)**
The mechanism by which a logger without an explicit level uses its parent’s level.

---

# J

### **JSON Output**
Pretty‑printed JSON log entries, ideal for debugging or human inspection.

---

# L

### **Level**
A numeric severity value associated with a log message (e.g., INFO, ERROR, custom levels).

### **LevelStyle**
A configuration object defining the color and style of a log level in console output.

### **LogRecordDetails**
A configuration object that controls structured formatting of log entries.

---

# M

### **Message Parts Order**
The order in which metadata fields appear in structured log output.

### **Metadata Fields**
Optional fields such as logger name, file name, line number, thread ID, etc.

---

# N

### **NDJSON**
Newline‑Delimited JSON — one JSON object per line, ideal for ingestion pipelines.

### **NOTSET**
A special level value indicating that a logger should inherit its level from its parent.

---

# O

### **Output Mode**
Determines how logs are formatted: COLOR, PLAIN, JSON, or NDJSON.

### **OptionalRecordFields**
A configuration object enabling or disabling metadata fields in structured output.

---

# P

### **Propagation**
The process of forwarding log events to parent loggers. Disabled by default; enabled only during auditing.

### **Pretty JSON**
Human‑readable JSON with indentation and whitespace.

---

# R

### **Raw Output**
Unformatted text written directly to a handler, bypassing structured formatting.

### **Retention**
The policy controlling how long rotated log files are kept.

### **Rotation**
The process of renaming and replacing log files when size or time thresholds are reached.

### **Rotation Logic**
A configuration object defining rotation rules (size, time, interval, retention).

### **Rotation Timestamp**
A time anchor used for daily or weekly rotation schedules.

---

# S

### **Sanitization**
The removal of ANSI codes from file output to prevent corruption or ingestion issues.

### **Separator**
The character or string used to separate metadata fields in structured output.

### **SmartLogger**
The primary synchronous logger class in LogSmith.

### **Structured Fields**
Named arguments passed to log methods that appear as key‑value pairs in structured output.

### **Structured Formatting**
A formatting model that uses explicit configuration instead of format strings.

---

# T

### **Theme**
A mapping of log levels to LevelStyle objects, controlling console color schemes.

### **Thread ID**
A metadata field indicating which thread emitted the log.

### **Timestamp Anchor**
A specific time of day used for scheduled rotation.

---

# U

### **User Fields**
Custom structured fields provided via named arguments in log calls.

---

# V

### **Verbose Level**
A common dynamic level used for highly detailed logs.

---

# W

### **When**
An enum defining time‑based rotation intervals (SECOND, MINUTE, HOUR, EVERYDAY, MONDAY, etc.).

---

# Summary  
This glossary defines all terminology used throughout LogSmith, covering logging concepts, configuration objects, rotation mechanics, async behavior, themes, structured formatting, and more. It serves as a quick reference for developers working with the framework.

The next appendix covers **Appendix C: Changelog**, documenting version history and major changes across releases.
