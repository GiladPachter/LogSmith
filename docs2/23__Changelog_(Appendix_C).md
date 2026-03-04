# Appendix C — Changelog  
This appendix documents the version history of LogSmith, including major features, improvements, fixes, and behavioral changes across releases. It provides a chronological overview of how the framework evolved.

---

# Version 1.0.0 — Initial Release  
- Introduced **SmartLogger**, the synchronous logging engine.  
- Added console and file handlers.  
- Implemented structured formatting with `LogRecordDetails`.  
- Added ANSI color support via `CPrint`.  
- Introduced rotation (`RotationLogic`) and retention (`ExpirationRule`).  
- Added JSON and NDJSON output modes.  
- Implemented structured fields (named arguments).  
- Added exception formatting.  
- Introduced themes and `LevelStyle`.  
- Added raw output support.  
- Included basic diagnostics and introspection.

---

# Version 1.1.0 — Async Logging  
- Introduced **AsyncSmartLogger** with async logging methods.  
- Added async queue and worker system.  
- Implemented async rotation and async file handling.  
- Added `a_stdout()` for synchronized async printing.  
- Improved ordering guarantees across tasks.  
- Added async‑aware diagnostics.

---

# Version 1.2.0 — Auditing System  
- Added global auditing for SmartLogger and AsyncSmartLogger.  
- Introduced audit handlers and audit formatter.  
- Added NDJSON audit output.  
- Added async audit worker for async auditing.  
- Improved propagation model (enabled only during auditing).

---

# Version 1.3.0 — Dynamic Log Levels  
- Added runtime level registration (`register_level`).  
- Automatically generated new logger methods (sync + async).  
- Added theme integration for dynamic levels.  
- Updated JSON / NDJSON to include dynamic levels.  
- Improved level inheritance logic.

---

# Version 1.4.0 — Formatting Enhancements  
- Expanded `OptionalRecordFields` with new metadata fields.  
- Added full control over message parts ordering.  
- Added color‑all‑fields option.  
- Improved exception formatting in JSON / NDJSON.  
- Added module name and pathname metadata.

---

# Version 1.5.0 — Rotation Improvements  
- Added timestamp anchors (`RotationTimestamp`).  
- Added weekly rotation (MONDAY–SUNDAY).  
- Improved hybrid rotation logic.  
- Added concurrency‑safe rotation on Windows and Unix.  
- Improved retention cleanup performance.

---

# Version 1.6.0 — Theme & Color Engine Upgrade  
- Added new built‑in themes (NEON, PASTEL, FIRE, OCEAN).  
- Added gradient palettes and multi‑stop gradients.  
- Improved ANSI sanitization for file handlers.  
- Added background gradients.  
- Improved raw output performance.

---

# Version 1.7.0 — Diagnostics Expansion  
- Added `describe()` for detailed logger introspection.  
- Added handler introspection for console and file handlers.  
- Added rotation state reporting.  
- Added async queue diagnostics.  
- Improved error messages for misconfiguration.

---

# Version 1.8.0 — Lifecycle Management  
- Added `retire()` and `destroy()` for loggers.  
- Added `destroy_async()` for async loggers.  
- Added global shutdown (`shutdown()` / `shutdown_async()`).  
- Improved handler cleanup and file closing.  
- Added safe recreation of loggers with the same name.

---

# Version 1.9.0 — Performance Improvements  
- Optimized structured formatting to reduce allocations.  
- Improved NDJSON serialization speed.  
- Reduced overhead of async queue operations.  
- Improved rotation performance under heavy load.  
- Added micro‑optimizations for metadata extraction.

---

# Version 2.0.0 — Major Stability Release  
- Refactored internal architecture for clarity and maintainability.  
- Improved cross‑platform file locking.  
- Added safer fallback behavior for unexpected exceptions.  
- Improved compatibility with Python 3.12+.  
- Added comprehensive test suite for sync + async logging.  
- Updated documentation and examples.

---

# Summary  
This changelog captures the evolution of LogSmith from a simple structured logger into a full‑featured logging framework with:

- sync + async engines  
- auditing  
- dynamic levels  
- advanced formatting  
- rotation + retention  
- themes + gradients  
- diagnostics  
- lifecycle management  
- high‑performance architecture  

The next appendix covers **Appendix D: License**, providing the full license text for LogSmith.
