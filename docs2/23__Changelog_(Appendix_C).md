# Appendix C — 📜 Changelog  
A chronological record of LogSmith’s evolution, reordered to reflect the actual progression of architectural, functional, and ecosystem‑level development up to version **1.8.3**.

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

# Version 1.1.0 — Formatting Enhancements  
- Expanded `OptionalRecordFields` with new metadata fields.  
- Added full control over message parts ordering.  
- Added color‑all‑fields option.  
- Improved exception formatting in JSON / NDJSON.  
- Added module name and pathname metadata.  
- Improved structured formatting consistency.

---

# Version 1.2.0 — Rotation Improvements  
- Added timestamp anchors (`RotationTimestamp`).  
- Added weekly rotation (MONDAY–SUNDAY).  
- Improved hybrid rotation logic.  
- Added concurrency‑safe rotation on Windows and Unix.  
- Improved retention cleanup performance.

---

# Version 1.3.0 — Async Logging  
- Introduced **AsyncSmartLogger** with async logging methods.  
- Added async queue and worker system.  
- Implemented async rotation and async file handling.  
- Added `a_stdout()` for synchronized async printing.  
- Improved ordering guarantees across tasks.  
- Added async‑aware diagnostics.

---

# Version 1.4.0 — Auditing System  
- Added global auditing for SmartLogger and AsyncSmartLogger.  
- Introduced audit handlers and audit formatter.  
- Added NDJSON audit output.  
- Added async audit worker for async auditing.  
- Improved propagation model (enabled only during auditing).

---

# Version 1.5.0 — Dynamic Log Levels  
- Added runtime level registration (`register_level`).  
- Automatically generated new logger methods (sync + async).  
- Added theme integration for dynamic levels.  
- Updated JSON / NDJSON to include dynamic levels.  
- Improved level inheritance logic.

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

# Version 1.8.3 — Stability & Metadata Refinement  
- Improved metadata extraction performance.  
- Added robust metadata exposure (`__metadata__`).  
- Added license text extraction with multi‑layout support.  
- Improved wheel packaging consistency.  
- Minor fixes for edge‑case lifecycle behavior.

---

# Summary  
LogSmith’s development path reflects a progression from a foundational structured logger into a mature, high‑performance logging framework with:

- synchronous + asynchronous engines  
- advanced formatting and color systems  
- rotation + retention with concurrency safety  
- auditing and dynamic log levels  
- diagnostics and lifecycle management  
- robust metadata and packaging  
- strong performance characteristics  

This appendix documents that evolution up to **v1.8.3**.  
The next appendix covers **Appendix D: License**, containing the full license text.
