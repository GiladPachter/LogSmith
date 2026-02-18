# 🧩 Extras & Structured Fields

SmartLogger supports **structured logging** through named arguments and the `fields={}` parameter.
Structured fields appear at the end of the log entry as a compact, JSON‑like dictionary.

---

## 🔹 Named Arguments (Recommended)

```python
logger.info("User login", user="gilad", action="login")
```

Output:

```
{ user='gilad', action='login' }
```

---

## 🔹 Using `fields={}` Explicitly

```python
logger.info("Payment processed", fields={"amount": 49.99, "currency": "USD"})
```

---

## 🔹 Merging Rules

```python
logger.info(
    "Order shipped",
    order_id=123,
    fields={"status": "sent", "priority": "high"},
)
```

Result:
```
Order shipped { order_id=123, fields={'status': 'sent', 'priority': 'high'} }
```

Rules:
- Named arguments and `fields={}` are merged
- Duplicate keys → named arguments win
- Values are safely stringified

---

## 🔹 Structured Fields Formatting

- strings are quoted
- numbers/booleans are unquoted
- `None` → `null`
- nested structures serialized cleanly

Example:

```python
logger.debug("Metrics", fields={"latency_ms": 12.5, "ok": True})
```

---

## 🔹 Structured Fields + Exceptions

```python
try:
    1 / 0
except ZeroDivisionError:
    logger.error("Computation failed", task="division", exc_info=True)
```

---

## 🔹 Structured Fields in File Handlers

```python
logger.add_file("logs", "events.log")
logger.info("Event", id=42, type="heartbeat")
```

---

# 🧩 Summary

SmartLogger’s structured fields system provides:

- clean named‑argument metadata
- optional `fields={}` merging
- stable, readable formatting
- safe serialization
- compatibility with exceptions and file handlers
