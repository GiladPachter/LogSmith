# Appendix C — 📜 Changelog

Starting off LogSmith as a personal experimental project, versioning was quite neglected until the later stages of its development.<br/>
This means that the GIT records will not show an orderly even version progression.<br/>
The below "timeline" specifies how things had progressed in actuality during the evolution of the LogSmith ecosystem and assigns version labels according to the spirit of that progression, all the way to the stabilized version **1.8.3**.

---

# Version 1.0.0 — Initial Release
- Introduced **SmartLogger**, a synchronous logging engine.
- Added console and file handlers.
- Time-based & Size-based Rotation control with `RotationLogic`, `When` & `RotationTimestamp` entities
- Concurrency-safe rotation.
- Structured formatting with `LogRecordDetails` and `OptionalRecordFields`.
- ANSI color support via `CPrint`.
- Dynamic Log-Levels

---

# Version 1.1.0 — Formatting Enhancements
- Added raw output support.  
- Implemented structured fields (named arguments).
- Added full control over message parts ordering.
- Added color_all_log_record_fields option.
- Added optional timestamp & pid suffix for rotating files.

---

# Version 1.2.0 — Theme & Color Engine Upgrade
- Color Themes - substitute color definitions for console output.
- Added built-in themes (LIGHT, DARK, NEON, PASTEL, FIRE, OCEAN).
- Added gradient palettes and multi-stop gradients.
- Improved ANSI sanitization for file handlers.
- Added ANSI preservation for file handlers.
- Added background gradients.
- Improved raw output performance.

---

# Version 1.3.0 — Hierarchy & Auditing
- Level-inheritance logic, for controling logging level of multiple loggers via a single ancestor logger.
- Global Auditing for SmartLogger via specialized audit handlers & audit formatter.

---

# Version 1.4.0 — Async Logging  
- Introduced **AsyncSmartLogger** with async logging methods.  
- Async queue and worker system.  
- Async rotation and async file handling.  
- `a_stdout()` print() wrapper for synchronized console output with AsyncSmartLogger logging.
- `stdout()` print() wrapper for synchronized console output with SmartLogger logging.
- Improved ordering guarantees across tasks.  
- Global `flush()' & `shutdown()` for async logging.

---

# Version 1.5.0 — JSON / NDJSON logs
- JSON output to console.
- NDJSON output to file.
- Updated JSON / NDJSON to include dynamic levels.  

---

# Version 1.6.0 — Improvements & Refinements
- Added `retire()` and `destroy()` for loggers.  
- Added exception formatting.  
- Added async audit worker for async auditing.  
- Tweaked audit for JSON / NDJSON logging.  

---

# Version 1.7.0 — Diagnostics Expansion  
- Added handler introspection for console and file handlers.  
- Added async queue diagnostics.  
- Improved error messages for misconfiguration.

---

# Version 1.8.0 — Stability & Metadata Refinement  
- Added async-aware introspection & performance diagnostics.
- Added LogSmith package introspection: __metadata__, __license_text__ & __package_content__.
- Improved wheel packaging consistency.  
- Minor fixes for edge-case lifecycle behavior.


---

# 📘 Summary  
LogSmith’s development path reflects a progression from a foundational structured logger into a mature, high-performance logging framework with:

- synchronous + asynchronous engines  
- advanced formatting and color systems  
- rotation + retention with concurrency safety  
- auditing and dynamic log levels  
- robust metadata and packaging  
- diagnostics and lifecycle management  
- strong performance characteristics  

This appendix documents that evolution up to **v1.8.3**.  
