# 🛠️ Troubleshooting

---

## 🔹 1. Duplicate log lines

Cause: multiple console handlers.
Fix: check `logger.console_handler` or remove with `logger.remove_console()`.

---

## 🔹 2. Child logger not inheriting handlers

SmartLogger does not inherit handlers.
Add handlers explicitly or use auditing.

---

## 🔹 3. ANSI codes in log files

Remove `do_not_sanitize_colors_from_string=True`.

---

## 🔹 4. Log files not rotating

Check thresholds, rotation frequency, write activity, or lock contention.

---

## 🔹 5. Rotated files not deleted

Set `backupCount`.

---

## 🔹 6. Structured fields missing

Use named arguments after the logged message.
Do not use `extra`.

---

## 🔹 7. Theme not applying

Use:

```python
SmartLogger.apply_color_theme("fire", FIRE_THEME)
```

---

## 🔹 8. Logger stopped logging

You retired it. Find and disable or Destroy and recreate.

---

## 🔹 9. Wrong timestamp format

Use `%1f`–`%6f` for fractional seconds.

---

## 🔹 10. Missing traceback

Add `exc_info=True`.

---

## 🔹 11. Logs out of order

Normal in multi‑threaded environments.
Use auditing for ordering.

---

## 🔹 12. Custom formatter ignored

Pass `log_record_details` to the correct handler.

---

## 🔹 13. Logger name missing

Enable in `OptionalRecordFields`.

---

## 🔹 14. Gradient breaks across lines

Use multi‑line gradient utilities.
