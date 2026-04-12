# Appendix C — 📜 Changelog

Starting off LogSmith as a personal experimental project, versioning was quite neglected until the later stages of its development.<br/>
This means that the GIT records will not show an orderly even version progression.<br/>
The below "timeline" specifies how things had progressed in actuality during the evolution of the LogSmith ecosystem and assigns version labels according to the spirit of that progression, all the way to the stabilized version **1.8.3**.

---

# Version 1.0.0 — Initial Release
- Introduced **SmartLogger**, a synchronous logging engine.
- Added console and file handlers.
- Time‑based & size‑based rotation with `RotationLogic`, `When`, and `RotationTimestamp`.
- Concurrency‑safe rotation.
- Structured formatting with `LogRecordDetails` and `OptionalRecordFields`.
- ANSI color support via `CPrint`.
- Dynamic log levels.

---

# Version 1.1.0 — Formatting Enhancements
- Added raw output support.  
- Implemented structured fields (`named_args`).
- Added full control over message parts ordering.
- Added `color_all_log_record_fields`.
- Added optional timestamp & PID suffix for rotating files.

---

# Version 1.2.0 — Theme & Color Engine Upgrade
- Introduced color themes for console output.
- Added built‑in themes (LIGHT, DARK, NEON, PASTEL, FIRE, OCEAN).
- Added gradient palettes and multi‑stop gradients.
- Improved ANSI sanitization for file handlers.
- Added ANSI preservation for file handlers.
- Added background gradients.
- Improved raw output performance.

---

# Version 1.3.0 — Hierarchy & Auditing
- Added strict level‑inheritance logic for hierarchical loggers.
- Introduced global auditing for SmartLogger via dedicated audit handlers and audit formatter.
- Added propagation‑only‑during‑auditing behavior.

---

# Version 1.4.0 — Async Logging
- Introduced **AsyncSmartLogger** with async logging methods.  
- Added async queue and worker system.  
- Added async rotation and async file handling using thread‑pool offloading.
- Added `logger.a_stdout()` for synchronized async printing.
- Added `logger.stdout()` for synchronized sync printing.
- Improved ordering guarantees across tasks.  
- Added global async `flush()` and `shutdown()`.

---

# Version 1.5.0 — JSON / NDJSON Logs
- Added JSON output to console.
- Added NDJSON output to file handlers.
- Updated JSON/NDJSON to include dynamic levels.
- Added structured exception output to JSON/NDJSON.

---

# Version 1.6.0 — Improvements & Refinements
- Added `retire()` and `destroy()` lifecycle operations.
- Added structured exception formatting.
- Added async audit worker for async auditing.
- Improved audit formatting for JSON/NDJSON.
- Added hierarchy validation (parent must exist, type must match).
- Added duplicate file‑handler prevention.

---

# Version 1.7.0 — Diagnostics Expansion
- Added handler introspection for console and file handlers.
- Added async queue diagnostics (queue size, processed count).
- Improved error messages for misconfiguration.
- Added `handler_info_json`.
- Added improved rotation diagnostics.

---

# Version 1.8.0 — Stability & Metadata Refinement
- Added async‑aware introspection & performance diagnostics.
- Added LogSmith package introspection: `__metadata__`, `__license_text__`, `__package_content__`.
- Improved wheel packaging consistency.
- Added `LargeLogEntryBehavior` for oversized log entries.
- Improved lifecycle edge‑case handling.
- Improved NDJSON formatting stability.
- Improved hierarchy safety and logger destruction behavior.

---

# Version 1.9.0 — Stabilized Release
- Finalized rotation behavior across sync + async engines.
- Finalized auditing lifecycle (`terminate_auditing`).
- Finalized theme behavior and level‑number mapping.
- Finalized async worker debounce logic.
- Minor bug fixes and documentation alignment.
- Marked the API surface as stable.

---

# 📘 Summary
LogSmith’s development path reflects a progression from a foundational structured logger into a mature, high‑performance logging framework with:

- synchronous + asynchronous engines
- advanced formatting and color systems
- rotation + retention with concurrency safety
- auditing and dynamic log levels
- robust metadata and packaging
- diagnostics and lifecycle management
- strong performance characteristics

This appendix documents that evolution up to **v1.9.6**.
