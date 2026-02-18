# ❓ FAQ — Frequently Asked Questions

---

## 🔹 1. Why SmartLogger instead of Python’s logging?

SmartLogger fixes common issues:

- handler inheritance
- confusing propagation
- cumbersome formatting
- awkward structured fields
- fragile rotation
- limited color support

---

## 🔹 2. Does SmartLogger replace Python logging?

No — it wraps Python logging with a cleaner API.

---

## 🔹 3. Are SmartLogger loggers compatible with Python handlers?

Yes. They are just better.

---

## 🔹 4. Why no handler inheritance?

To avoid duplicate logs and unpredictable behavior.

---

## 🔹 5. How do I change the colors of logged messages?

```python
SmartLogger.apply_color_theme("fire", THEME_FIRE)
```

---

## 🔹 6. Can I define my own theme?

Yes — themes are dictionaries.

---

## 🔹 7. JSON logging?

Planned.

---

## 🔹 8. Async support?

Thread‑safe and multi‑process‑safe, async planned.

---

## 🔹 9. Multi‑process file logging?

Yes — safe via advisory locks and atomic renames.

---

## 🔹 10. Why strip ANSI in files?

To keep logs clean and parser‑friendly.

---

## 🔹 11. Disable a logger?

```python
logger.retire()
```

---

## 🔹 12. Remove a logger?

```python
logger.destroy()
```

---

## 🔹 13. Why structured fields at the end?

For readability and consistency.

---

## 🔹 14. Production‑ready?

Yes.

---

## 🔹 15. Windows color support?

Yes — Windows 10+ supports ANSI.
