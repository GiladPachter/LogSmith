# ⚠️ Diagnostics & Debugging

LogSmith includes built‑in diagnostics to help you understand how loggers behave, how handlers are configured, and why certain logs appear—or don’t appear. This chapter covers introspection tools, debugging rotation, analyzing async behavior, and detecting misconfiguration in large applications.

---

## 💡 Purpose of Diagnostics  
Diagnostics help you answer questions like:

- Why isn’t this log appearing?  
- Which handlers are attached to this logger?  
- What is the logger’s effective level?  
- Are rotation & retention working correctly?  
- Are async logs being flushed?  
- Is auditing enabled?
- Are ANSI codes being sanitized?  
- Is the hierarchy valid?

LogSmith provides explicit tools to inspect and debug all of these.

---

## 🔍 Logger Introspection

Every logger can describe itself:

```python
print(logger.handler_info)
print(logger.console_handler)
print(logger.file_handlers)
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
- ANSI sanitization mode
- async queue status (for AsyncSmartLogger)  
- auditing status  
- hierarchy validity

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

- resolved file path  
- output mode  
- rotation logic  
- retention policy  
- sanitization settings  
- formatter configuration  
- whether colors are preserved
- whether the handler is retired

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
print(logger.handler_info)
```

Common issues:

- no console handler attached  
- file handler pointing to a non‑existent directory  
- logger level too high  
- handler level too high  
- auditing enabled but audit file not writable  
- logger was retired
- logger was destroyed
- hierarchy invalid (parent missing or wrong type)

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
- timestamp anchors misconfigured
- hybrid rotation triggering earlier than expected

Rotation debugging almost always comes down to configuration or filesystem permissions.

---

## 🌀 Debugging Async Behavior

AsyncSmartLogger includes several diagnostics:

```python
print(logger.handler_info)
```

Async diagnostics include:

- queue_size  
- worker_alive
- messages_processed
- pending_flush
- rotation_scheduled

If logs appear out of order or not at all, check:

- whether `await logger.flush()` was called  
- whether the event loop is still running  
- whether the worker task is alive  
- whether the logger was destroyed prematurely

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
- ensure the theme is applied correctly

Use synchronized printing:

### Sync

```python
logger.stdout("Hello")
```

### Async

```python
await logger.a_stdout("Hello")
```

---

## ⚠️ Avoid using print()

`print()` interleaves with both sync and async logs.

Use:

```python
logger.stdout(text)
```

or:

```python
await logger.a_stdout(text)
```

These guarantee ordering with log output.

---

## 🧾 Debugging JSON / NDJSON Output

If JSON logs look malformed:

- ensure `output_mode=OutputMode.NDJSON` or `OutputMode.JSON`
- ensure ANSI sanitization is enabled (default)  
- ensure raw output is not mixed with JSON output  
- ensure structured fields (`named_args`) are JSON‑serializable
- check for stray newline characters in messages  
- ensure exceptions are serializable (LogSmith handles this automatically)

NDJSON requires one JSON object per line — malformed entries usually come from raw output or non‑serializable fields.

---

## 🎨 Debugging Theme Behavior

Themes are simple to debug:

```python
SmartLogger.apply_color_theme(...)
```

Then call:

```python
logger.trace()
logger.debug()
logger.info()
logger.warning()
logger.error()
logger.critical()
```

Async:

```python
await logger.a_info()
```

If colors don’t appear:

- ensure output mode is COLOR
- ensure ANSI is not sanitized
- ensure console supports ANSI
- ensure theme maps level **numbers**, not names

---

## 🛰️ Debugging Auditing

If audit logs are missing:

- check if auditing is enabled  
- check audit file permissions  
- check rotation settings  
- check async audit worker status (async only)  

Restart auditing:

### Sync

```python
SmartLogger.terminate_auditing()
SmartLogger.audit_everything(log_dir = "audit", logfile_name = "audit.log")
```

### Async

```python
await AsyncSmartLogger.terminate_auditing()
await AsyncSmartLogger.audit_everything(log_dir = "audit", logfile_name = "audit_async.log")
```

---

## 🧵 Debugging Multi‑Process Behavior

If logs are missing or corrupted:

- ensure each process writes to its own base file (Windows limitation)  
- ensure directories exist  
- ensure rotation is concurrency‑safe (it is by default)  
- ensure file handlers are not duplicated across processes

---

## 🚀 Performance Diagnostics

If logging feels slow:

- check if JSON pretty printing is enabled  
- check if too many handlers are attached  
- check if rotation is happening too frequently  
- check if async queue is overloaded  
- check if gradients or heavy ANSI output are used excessively  
- check if auditing is enabled (adds overhead)

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
- hierarchy validity  
- performance bottlenecks  

These tools make it easy to understand why logs behave the way they do and how to fix issues quickly.
