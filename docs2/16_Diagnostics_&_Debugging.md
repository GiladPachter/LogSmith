# ⚠️ Diagnostics & Debugging  
LogSmith includes built‑in diagnostics to help you understand how loggers behave, how handlers are configured, and why certain logs appear (or don’t appear). This chapter covers introspection tools, debugging rotation, analyzing async behavior, and detecting misconfiguration in large applications.

---

## � Purpose of Diagnostics  
Diagnostics help you answer questions like:

- Why isn’t this log appearing?  
- Which handlers are attached to this logger?  
- What is the logger’s effective level?  
- Is rotation working correctly?  
- Are async logs being flushed?  
- Is auditing enabled?  
- Are ANSI codes being sanitized?  

LogSmith provides explicit tools to inspect and debug all of these.

---

## Logger Introspection  
Every logger can describe itself:

```python
print(logger.describe())
```

This returns a structured dictionary containing:

- logger name  
- explicit level  
- inherited level  
- handlers  
- output modes  
- rotation settings  
- retention settings  
- theme state  
- async queue status (for AsyncSmartLogger)  
- auditing status  

This is the single most useful debugging tool in LogSmith.

---

## Inspecting Handlers  
You can inspect handlers individually:

### Console handler

```python
print(logger.console_handler)
```

### File handlers

```python
print(logger.file_handlers)
```

Each handler reports:

- path  
- output mode  
- rotation logic  
- retention policy  
- sanitization settings  
- formatter configuration  

This makes it easy to detect misconfiguration.

---

## Checking Effective Log Level  
A logger’s effective level may come from:

- its own explicit level  
- its parent’s level  
- the default INFO level  

Check it:

```python
print(logger.getEffectiveLevel())
```

This is essential when logs aren’t appearing.

---

## Detecting Missing Handlers  
If logs aren’t showing up, check:

```python
logger.describe()
```

Common issues:

- no console handler attached  
- file handler pointing to a non‑existent directory  
- logger level too high  
- handler level too high  
- auditing enabled but audit file not writable  

---

## Debugging Rotation  
Rotation issues usually come from:

- insufficient permissions  
- multiple processes writing to the same file (Windows)  
- timestamp anchors misconfigured  
- retention rules deleting files too aggressively  

Inspect rotation:

```python
for handler in logger.file_handlers:
    print(handler.rotation_logic)
```

You can also check the next scheduled rotation time:

```python
handler.rotation_logic.next_rotation_time
```

---

## Debugging Async Logging  
AsyncSmartLogger includes queue diagnostics:

```python
logger.describe()
```

Async diagnostics include:

- queue size  
- worker status  
- pending writes  
- rotation state  
- audit queue status (if auditing is enabled)  

If logs appear out of order or not at all, check:

- whether `await logger.flush()` was called  
- whether the event loop is still running  
- whether the worker task is alive  

---

## Debugging a_stdout()  
If `print()` interleaves with async logs, replace it with:

```python
await a_stdout("message")
```

If output still interleaves:

- ensure only one AsyncSmartLogger is active  
- ensure no raw writes bypass the logger  
- check for third‑party libraries printing directly  

---

## Debugging JSON / NDJSON  
If JSON logs look malformed:

- ensure ANSI sanitization is enabled (default)  
- ensure raw output is not mixed with JSON output  
- ensure structured fields are JSON‑serializable  
- check for stray newline characters in messages  

NDJSON requires one JSON object per line — malformed entries usually come from raw output or non‑serializable fields.

---

## Debugging Themes  
If colors look wrong:

- check if a theme is applied  
- check if the terminal supports ANSI  
- check if output mode is COLOR  
- ensure file handlers are not sanitizing ANSI (unless intended)  

Reset theme:

```python
SmartLogger.reset_color_theme()
```

---

## Debugging Auditing  
If audit logs are missing:

- check if auditing is enabled  
- check audit file permissions  
- check rotation settings  
- check async audit worker status (async only)  

Disable and re‑enable auditing:

```python
SmartLogger.stop_auditing()
SmartLogger.audit_everything(log_dir="audit", logfile_name="audit.log")
```

Async:

```python
await AsyncSmartLogger.stop_auditing()
AsyncSmartLogger.audit_everything(log_dir="audit", logfile_name="audit_async.log")
```

---

## Debugging Multi‑Process Logging  
If logs are missing or corrupted:

- ensure each process writes to its own base file (Windows)  
- ensure directories exist  
- ensure rotation is concurrency‑safe (it is by default)  
- avoid mixing raw output with structured logs  

---

## Debugging Performance  
If logging feels slow:

- check if JSON pretty printing is enabled  
- check if too many handlers are attached  
- check if rotation is happening too frequently  
- check if async queue is overloaded  
- check if gradients or heavy ANSI output are used excessively  

Async logging usually improves performance dramatically.

---

## Summary  
Diagnostics & Debugging tools in LogSmith provide:

- full logger introspection  
- handler inspection  
- rotation analysis  
- async queue diagnostics  
- theme debugging  
- auditing verification  
- JSON / NDJSON validation  
- multi‑process safety checks  

The next chapter covers **Performance & Benchmarks**, showing how LogSmith behaves under load and how to optimize your logging configuration.
