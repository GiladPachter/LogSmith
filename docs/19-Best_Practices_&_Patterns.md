# 🧠 Best Practices & Patterns

LogSmith is designed to be expressive, predictable, and production‑ready.
These patterns help you get the most out of it.

---

## 🔹 1. Create Loggers by Module or Component

```python
logger = SmartLogger.get("myapp.api.users")
```

---

## 🔹 2. Add Handlers Explicitly

```python
logger.add_console()
logger.add_file(log_dir = "logs", logfile_name = "api.log")
```

---

## 🔹 3. Use Structured Fields

```python
logger.info("User login", user=user, ip=ip)
```

---

## 🔹 4. Apply Themes

```python
SmartLogger.apply_theme(DARK_THEME)
```

---

## 🔹 5. Always Use Rotation

```python
logger.add_file(
    "logs",
    "app.log",
    rotation_logic = RotationLogic(maxBytes=5_000_000, backupCount=10),
)
```

---

## 🔹 6. Use Auditing for Centralized Logs

```python
SmartLogger.audit_everything("audit", "audit.log")
```

---

## 🔹 7. Retire or Destroy Loggers When Reconfiguring

```python
logger.destroy()
```

---

## 🔹 8. Avoid Excessive Logger Creation

Reuse loggers instead of creating them repeatedly.

---

## 🔹 9. Use `exc_info=True` for Exceptions

```python
logger.error("Failed", exc_info=True)
```

---

## 🔹 10. Use `stack_info=True` for Debugging

```python
logger.debug("Snapshot", stack_info=True)
```

---

## 🔹 11. Keep Formatting Declarative

```python
logger.add_console(log_record_details=LogRecordDetails(...))
```

---

## 🔹 12. Prefer Named Arguments Over `fields={}`

---

## 🔹 13. Keep Messages Short and Actionable

---

## 🔹 14. Use Gradients Sparingly

---

## 🔹 15. Use File Sanitization Wisely

---

# 🧩 Summary

LogSmith’s best practices emphasize:

- explicit configuration
- structured metadata
- clean formatting
- safe lifecycle management
- predictable hierarchy behavior
- efficient file rotation
- expressive but controlled use of color
