# ⚠️ Diagnostics & Debugging

LogSmith includes built‑in diagnostics to help you understand how loggers behave, how handlers are configured, and why certain logs appear—or don’t appear. This chapter covers introspection tools, debugging rotation, analyzing async behavior, and detecting misconfiguration in large applications.

---

## � Purpose of Diagnostics  
Diagnostics help you answer questions like:

- Why isn’t this log appearing?  
- Which handlers are attached to this logger?  
- What is the logger’s effective level?  
- Are rotation & retention working correctly?  
- Are async logs being flushed?  
- Is auditing enabled?
- Are ANSI codes being sanitized?  

LogSmith provides explicit tools to inspect and debug all of these.

---

## 🔍 Logger Introspection

Every logger can describe itself:

```python
print(logger.handler_info())
print(logger.console_handler())
print(logger.file_handlers())
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

## 🧰 Inspecting Handlers

You can inspect handlers individually.

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

This makes it easy to detect misconfiguration or missing components.

---

## 🔢 Checking Effective Log Level

A logger’s effective level may come from:

- its own explicit level  
- its parent’s level  
- the default INFO level  

Check it:

```python
print(logger.getEffectiveLevel())
```

This is essential when logs aren’t appearing due to level filtering.

---

## 🚫 Detecting Missing Handlers

If logs aren’t showing up, inspect the logger:

```python
logger.describe()
```

Common issues:

- no console handler attached  
- file handler pointing to a non‑existent directory  
- logger level too high  
- handler level too high  
- auditing enabled but audit file not writable  

Most logging issues come from handler misconfiguration rather than logger logic.

---

## 🔄 Debugging Rotation

Rotation issues usually fall into a few categories:

- rotation never triggers  
- rotation triggers too early  
- rotated files are empty  
- rotated files overwrite each other  
- retention deletes files too aggressively  

Inspect rotation logic:

```python
for handler in logger.file_handlers:
    print(handler.rotation_logic)
```

Common causes:

- `maxBytes` too high or too low  
- `backupCount` set to 0  
- log directory not writable  
- multiple processes writing to the same file on Windows  
- async rotation not flushed before shutdown  

Rotation debugging almost always comes down to configuration or filesystem permissions.

---

## 🌀 Debugging Async Behavior

AsyncSmartLogger includes several diagnostics:

```python
logger.describe()
```

Async diagnostics include:

- queue_size  
- messages_processed

If logs appear out of order or not at all, check:

- whether `await logger.flush()` was called  
- whether the event loop is still running  
- whether the worker task is alive  


Flush manually:

```python
await logger.flush()
```

This resolves most async issues.

---

## 📤 Debugging stdout / stderr Output

If console logs are not appearing:

- ensure a console handler is attached  
- ensure the console handler is not retired  
- ensure the logger level allows the message  
- ensure the console stream is not redirected  
- ensure ANSI sanitization is not stripping output  
- Check the handler:


---

## ⚠️ Avoid using print()
`print()` interleaves with both sync and async logs:

When using Smartlogger, also import stdout() and just use like you would use print()

```python
stdout(text)
```

When using AsyncSmartlogger, also import a_stdout() and use it as follows:

```python
await a_stdout(text)
```

---

## 🧾 Debugging JSON / NDJSON Output

If JSON logs look malformed:

- ensure `output_mode=OutputMode.NDJSON` when calling add_console() or add_file()
- ensure ANSI sanitization is enabled (default)  
- ensure raw output is not mixed with JSON output  
- ensure structured fields (named arguments) are JSON‑serializable  
- check for stray newline characters in messages  

NDJSON requires one JSON object per line — malformed entries usually come from raw output or non‑serializable fields.

---

## 🎨 Debugging Theme Behavior

There isn't really anything to do regarding debugging themes.
call SmartLogger.apply_color_theme(...) or AsyncSmartLogger.apply_color_theme(...)
Then immediately call all logging methods and verify the output colors in the console

```python
logger.trace() / await logger.a_trace()
logger.debug() / await logger.a_debug()
logger.info() / await logger.a_info()
logger.warning() / await logger.a_warning()
logger.error() / await logger.a_error()
logger.critical() / await logger.a_critical()
```

---

## 🛰️ Debugging Auditing

If audit logs are missing:

- check if auditing is enabled  
- check audit file permissions  
- check rotation settings  
- check async audit worker status (async only)  

```python
SmartLogger.stop_auditing()
SmartLogger.audit_everything(log_dir="audit", logfile_name="audit.log")
```

Async:

```python
await AsyncSmartLogger.stop_auditing()
await AsyncSmartLogger.audit_everything(log_dir="audit", logfile_name="audit_async.log")
```

---

## 🧵 Debugging Multi‑Process Behavior
If logs are missing or corrupted:

- ensure each process writes to its own base file (Windows)  
- ensure directories exist  
- ensure rotation is concurrency‑safe (it is by default)  

---

## 🚀 Performance Diagnostics

If logging feels slow:

- check if JSON pretty printing is enabled  
- check if too many handlers are attached  
- check if rotation is happening too frequently  
- check if async queue is overloaded  
- check if gradients or heavy ANSI output are used excessively  

Async logging usually improves performance dramatically.

---

## 📘 Summary

Diagnostics in LogSmith provide tools to inspect:

- logger configuration  
- handler state  
- rotation logic  
- async queues  
- JSON / NDJSON formatting  
- theme behavior  
- auditing state  
- multi‑process safety  
- performance bottlenecks  

These tools make it easy to understand why logs behave the way they do and how to fix issues quickly.
