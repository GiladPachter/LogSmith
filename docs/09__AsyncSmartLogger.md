# 🧵 AsyncSmartLogger
AsyncSmartLogger is LogSmith’s asynchronous logging engine. It is designed for asyncio applications that need high‑throughput logging without blocking the event loop, while still guaranteeing ordering, safe rotation, and consistent formatting.

This chapter explains how AsyncSmartLogger works, how to use it, and how it integrates with the rest of LogSmith.

---

## 💡 Why Async Logging Matters
Async applications often suffer from logging problems:

- `print()` interleaves output across tasks  
- synchronous logging blocks the event loop  
- rotation can freeze the loop during file operations  
- ordering becomes unpredictable  
- exceptions inside tasks are hard to trace  

AsyncSmartLogger solves all of these with:

- an asyncio queue  
- a dedicated worker task  
- ordered delivery  
- async rotation scheduling  
- safe shutdown via `flush()`  
- synchronized printing via `a_stdout()`  
- strict hierarchy validation  
- duplicate‑handler prevention  

---

## 🔹 Creating an AsyncSmartLogger
AsyncSmartLogger mirrors SmartLogger’s API:

```python
from LogSmith import AsyncSmartLogger

levels = AsyncSmartLogger.levels()
logger = AsyncSmartLogger("demo.async", level = levels["INFO"])
logger.add_console()
```

Hierarchy rules apply:

- ancestors must exist  
- ancestors must be AsyncSmartLogger instances  
- mixed‑type hierarchies are rejected  

You can start logging immediately.

---

## 🔹 Async Logging Methods
AsyncSmartLogger provides async versions of all log methods:

```python
await logger.a_trace("trace")
await logger.a_debug("debug")
await logger.a_info("info")
await logger.a_warning("warning")
await logger.a_error("error")
await logger.a_critical("critical")
```

Each method:

- enqueues the log record  
- returns immediately  
- never blocks the event loop  

The worker task handles formatting and output.

---

## 🔹 Ordering Guarantees
AsyncSmartLogger guarantees:

- **FIFO ordering per logger**  
- **ordering preserved across tasks using the same logger**  
- **no interleaving** between tasks for that logger  

Each logger has its own queue and worker.

---

## 🔹 The Worker Task
Internally, AsyncSmartLogger runs a worker task that:

- pulls log events from an asyncio queue  
- formats them  
- writes them to handlers  
- performs rotation checks  
- flushes on shutdown  

The worker:

- starts lazily when the first log is enqueued  
- auto‑starts only when running inside the logger’s event loop  
- is thread‑safe when scheduling rotation from external threads  

You never interact with the worker directly.

---

## 🔹 Flushing and Shutdown
Before shutting down your application, call:

```python
await logger.flush()
```

This ensures:

- all queued logs are written  
- rotation is completed  
- file handles are flushed  

To fully shut down the logger:

```python
await logger.shutdown()
```

Shutdown:

- flushes  
- cancels worker tasks  
- closes handlers  
- drains the queue  

A retired or destroyed logger cannot be used again.

---

## 🔹 Adding Handlers
AsyncSmartLogger supports the same handler types as SmartLogger, with async‑aware rotation.

### Console handler

```python
logger.add_console()
```

### File handler

```python
logger.add_file(
    log_dir = "/absolute/normalized/path",
    logfile_name = "async.log",
)
```

**Important:**  
`log_dir` must be a normalized absolute path.  
Relative or non‑normalized paths raise an error.

### JSON / NDJSON

```python
logger.add_file(
    log_dir      = "logs",
    logfile_name = "events.ndjson",
    output_mode  = OutputMode.NDJSON,
)
```

### Rotation

```python
logger.add_file(
    log_dir        = "logs",
    logfile_name   = "rotating.log",
    rotation_logic = RotationLogic(maxBytes = 50_000),
)
```

Rotation is handled in the worker thread, not the event loop.

Duplicate file handlers are prevented process‑wide.

---

## 🔹 a_stdout(): Synchronized Printing
Mixing `print()` with logging causes interleaving.

AsyncSmartLogger provides a synchronized print replacement:

```python
await logger.a_stdout("This prints in sync with async logs")
```

This ensures:

- no interleaving  
- consistent ordering  
- clean and sensible console output  

If no console handler exists, `a_stdout()` falls back to normal printing.

---

## 🔹 Structured Fields
Async logging supports structured fields exactly like SmartLogger:

```python
await logger.a_info("User login", username="Gilad", action="login")
```

These fields appear in:

- console output  
- file output  
- JSON  
- NDJSON  

They are stored under `named_args` in structured formats.

---

## 🔹 Exceptions in Async Logging
Exceptions inside async tasks are common.  
AsyncSmartLogger captures them cleanly:

```python
try:
    await risky_operation()
except Exception:
    await logger.a_error("Async failure", exc_info = True)
```

Output includes:

- exception type  
- message  
- traceback  
- structured fields  

Stack traces (`stack_info=True`) are also supported.

---

## 🔹 Async Rotation
Rotation is fully async‑aware:

- rotation checks run in the worker  
- file operations run in a thread pool  
- no blocking of the event loop  
- ordering is preserved  
- per‑handler debounce prevents redundant rotations  

Example:

```python
rotation = RotationLogic(maxBytes=100_000, backupCount=5)

logger.add_file(
    log_dir = "/logs",
    logfile_name = "async_rotating.log",
    rotation_logic = rotation,
)
```

---

## 🔹 Performance Characteristics
AsyncSmartLogger is optimized for:

- high‑throughput logging  
- minimal overhead  
- predictable ordering  
- safe rotation  

Typical performance:

- enqueue cost: extremely low  
- worker throughput: thousands of logs/sec  
- rotation overhead: offloaded to threads  
- backpressure: minimal exponential retry  

---

## 🔹 When to Use AsyncSmartLogger
Use AsyncSmartLogger when:

- your application uses asyncio  
- you need non‑blocking logging  
- you want ordered logs across tasks  
- you need async‑safe rotation  
- you want synchronized printing  

Use SmartLogger when:

- your application is synchronous  
- you don’t use asyncio  
- you want simpler lifecycle management  

Both loggers share the same API and formatting model.

---

## 📘 Summary
AsyncSmartLogger provides:

- async logging methods (`a_info`, `a_error`, etc.)  
- FIFO ordering per logger  
- non‑blocking behavior  
- async rotation  
- structured fields  
- JSON / NDJSON support  
- synchronized printing (`a_stdout`)  
- safe shutdown via `flush()` and `shutdown()`  
- strict hierarchy validation  
- duplicate‑handler prevention  

The next chapter covers **Rotation & Retention** in depth — including hybrid rotation, expiration rules, timestamp anchors, and concurrency guarantees.
