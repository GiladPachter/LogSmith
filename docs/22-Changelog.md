# 📝 Changelog

This section summarizes major changes across LogSmith versions.

---

## v1.0.0 — Initial Release

- Core `SmartLogger` class
- Console and file handlers
- Basic rotation
- Structured fields
- Exception logging
- Basic color support
- Logger hierarchy
- Logger lifecycle

---

## v1.1.0 — Formatting System

- Added `LogRecordDetails`
- Added `OptionalRecordFields`
- Added `message_parts_order`
- Added fractional timestamp formatting
- Added strict validation

---

## v1.2.0 — Color Engine Upgrade

- Introduced `CPrint`
- Added ANSI‑256 support
- Added gradients
- Added multi‑line gradients
- Added ANSI sanitization
- Added reverse‑video utilities

---

## v1.3.0 — Themes

- Introduced theme system (`apply_color_theme`)
- Added LIGHT, DARK, NEON, PASTEL
- Added FIRE and OCEAN

---

## v1.4.0 — Rotation Enhancements

- Added time‑based rotation
- Added `interval` and `utc`
- Added retention logic
- Added multi‑process safe rotation

---

## v1.5.0 — Auditing System

- Added `SmartLogger.audit_everything()`
- Added global propagation in audit mode
- Added audit file handler

---

## v1.6.0 — Performance Improvements

- Lazy formatting
- Faster level checks
- Optimized handler dispatch
- Reduced memory footprint
- Faster ANSI stripping

---

## v1.7.0 — Miscellaneous Improvements

- Better lifecycle management
- Improved error messages
- More robust file handling
- Expanded structured field serialization
- More consistent color behavior
