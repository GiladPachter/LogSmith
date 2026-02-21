# ⚡ Performance & Efficiency

LogSmith is designed to be **fast**, **predictable**, and **low‑overhead**, even in high‑volume or multi‑process environments.

---

## 🔹 Lazy Message Formatting

```python
logger.debug("Expensive: %s", compute_heavy())
```

If the logger’s level is above DEBUG, the message is never formatted and the function is never executed.

---

## 🔹 Efficient Structured Fields

- merged only when needed
- serialized only when emitted
- no unnecessary allocations

---

## 🔹 Fast Level Checks

- integer comparisons
- pre‑cached values
- no string comparisons

---

## 🔹 Lightweight Formatters

- no regex
- no repeated parsing
- pre‑validated `LogRecordDetails`
- pre‑computed ordering

---

## 🔹 Efficient Handler Dispatch

- no parent handler traversal
- no propagation unless auditing
- compact handler lists

---

## 🔹 Rotation Efficiency

- lightweight threshold checks
- atomic renames
- short‑duration locks
- retention only after rotation

---

## 🔹 ANSI Handling Efficiency

- console preserves ANSI
- file handlers strip ANSI with fast patterns
- no repeated regex compilation

---

## 🔹 Multi‑Process Safety

- advisory locks
- atomic operations
- minimal contention

---

## 🔹 Memory Efficiency

- no large buffers
- no global caches
- lightweight loggers

---

# 🧩 Summary

LogSmith provides:

- lazy formatting
- efficient structured fields
- fast level checks
- lightweight formatters
- minimal handler overhead
- safe, efficient rotation
- optimized ANSI handling
- multi‑process safety
