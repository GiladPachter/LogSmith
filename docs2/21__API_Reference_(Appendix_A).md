# Appendix A — 🛠️ API Reference  
A compact index of all LogSmith entities and the members they expose.  
Each bullet names a public member and states its purpose in one line.

---

# 🧠 SmartLogger  
Synchronous, high‑level logger built on Python’s logging system (composition).

## Core Members

```
- `name`                      —  logger’s name.  
- `level`                     —  logger’s current log level (inherits via hierarchy when NOTSET).  
- `add_console()`             —  attach a console handler with structured or colored output.  
- `remove_console()`          —  remove the console handler.  
- `add_file(...)`             —  attach a file handler with optional rotation and retention.  
- `remove_file_handler(...)`  —  remove a file handler by directory + filename.  
- `handler_info`              —  list of metadata dictionaries describing all handlers.  
- `handler_info_json`         —  JSON representation of handler_info.  
- `console_handler`           —  metadata for the console handler, if present.  
- `file_handlers`             —  metadata for all file handlers.  
- `output_targets`            —  list of output destinations (“console” or file paths).  
- `raw`                       —  write unformatted text directly to handlers.  
- `retire`                    —  close handlers and disable the logger.  
- `destroy`                   —  remove logger entirely from logging system.
```

## Logging Members

```
- `trace`
- `debug`
- `info`
- `warning`
- `error`
- `critical`
- `raw`                    —  pure-text message-only log entry (no log-record metadata fields)
- <dynamic level methods>  —  programmatically added log levels.
```

## Static Members

```
- `levels`              —  dictionary of all registered log levels.  
- `register_level`      —  define a new log level at runtime.  
- `apply_color_theme`   —  override color/style for built‑in and dynamic levels.  
- `audit_everything`    —  enable global auditing of all SmartLogger output.  
- `terminate_auditing`  —  disable global auditing.  
- `get_record`          —  extract a strongly‑typed `RetrievedRecord` from a LogRecord.
```

---

# ⚡ AsyncSmartLogger  
Fully asynchronous logger with queue, worker task, and async‑safe rotation.

## Core Members
```

- `name`                   —  logger’s name.  
- `level`                  —  logger’s current log level.  
- `queue_size`             —  number of pending log entries in the async queue.  
- `messages_enqueued`      —  number of log entries submitted to the queue.  
- `messages_processed`     —  total processed entries across all instances.  
- `add_console`            —  attach async‑safe console handler.  
- `remove_console`         —  remove console handler.  
- `add_file`               —  attach async‑safe file handler with async rotation.  
- `remove_file_handler`    —  remove file handler by directory + filename.  
- `handler_info`           —  metadata for all handlers.  
- `handler_info_json`      —  JSON representation of handler_info.  
- `output_targets`         —  list of output destinations.  
- `enable_profiling`       —  enable/disable internal performance profiling.  
- `get_profiling_details`  —  return profiling statistics.  
- `flush`                  —  wait until queue is empty.  
- `shutdown`               —  stop worker and flush queue.  
```

## Async Logging Members

```
- `a_trace`
- `a_debug`
- `a_info`
- `a_warning`
- `a_error`
- `a_critical`
- `a_raw`                  —  pure-text message-only log entry (no log-record metadata fields)
- <dynamic level methods>  —  programmatically added log levels.
```

## Static Members

```
- `levels`             —  dictionary of all registered log levels.  
- `register_level`     —  define a new async log level.  
- `apply_color_theme`  —  override color/style for async log levels.  
- `audit_everything`   —  enable async global auditing.  
- `stop_auditing`      —  disable async auditing.
```

---

# 🧾 LogRecordDetails  

Controls structured formatting for console/file output.

## Members
```
- `datefmt`                      —  timestamp format (supports %1f–%6f fractional seconds).  
- `separator`                    —  single‑character separator between fields.  
- `optional_record_fields`       —  which metadata fields to include.  
- `message_parts_order`          —  ordering of inline metadata fields.  
- `color_all_log_record_fields`  —  colorize all fields, not just level/message.
```

---

# 🧩 OptionalRecordFields  

Enable/disable individual metadata fields.

## Members
```
- `relative_created`             —  include relative timestamp.  
- `logger_name`                  —  include logger name.  
- `file_path`                    —  include full file path.  
- `file_name`                    —  include filename only.  
- `lineno`                       —  include line number.  
- `func_name`                    —  include function name.  
- `thread_id` / `thread_name`    —  include thread metadata.  
- `task_name`                    —  include asyncio task name.  
- `process_id` / `process_name`  —  include process metadata.  
- `exc_info`                     —  include exception traceback.  
- `stack_info`                   —  include stack trace.
```

---

# 🎨 OutputMode  

Enum controlling formatter type.

## Members
```
- `PLAIN`   —  plain structured text.  
- `COLOR`   —  colored structured text.  
- `JSON`    —  pretty‑printed JSON.  
- `NDJSON`  —  newline‑delimited JSON.
```

---

# 🎨 LevelStyle  

Defines color/style for a log level.

## Members
```
- `fg`         —  foreground color code.  
- `bg`         —  background color code.  
- `intensity`  —  bold/dim/normal.  
- `styles`     —  tuple of additional ANSI styles.
```

---

# 🌈 CPrint  

ANSI color and gradient engine.

## Members
```
- `colorize`                           —  apply solid color and style.  
- `gradient`                           —  apply 256‑color gradient (fg/bg).  
- `reverse`                            —  swap foreground/background.  
- `strip_ansi`                         —  remove ANSI codes.  
- `escape_ansi_for_display`            —  escape only color/style codes.  
- `escape_control_chars`               —  escape all control sequences.  
- `FG` / `BG` / `Intensity` / `Style`  —  color/style constant groups.
```

---

# 🌈 GradientPalette  

Predefined 256‑color palettes for gradients.

## Members
``` 
- `RAINBOW` / `FIRE` / `OCEAN` / `FOREST` / `SUNSET` / `PASTEL` / `NEON` / `GREYSCALE`  —  ready‑made palettes.  
- **custom palettes** — create via `GradientPalette([...])`.
```

---

# 🔄 RotationLogic  

Describes rotation and retention behavior.

## Members
```
- `when`                       —  time‑based rotation mode (SECOND, MINUTE, HOUR, EVERYDAY, weekday).  
- `interval`                   —  rotation interval for SECOND/MINUTE/HOUR.  
- `timestamp`                  —  daily/weekly rotation anchor.  
- `maxBytes`                   —  size‑based rotation threshold.  
- `backupCount`                —  number of rotated files to keep.  
- `expiration_rule`            —  retention policy for deleting old rotated files.  
- `append_filename_pid`        —  append process ID to filename.  
- `append_filename_timestamp`  —  append timestamp to filename.  
- `create_handler`             —  produce a rotation‑aware file handler.
```

---

# 🕒 RotationTimestamp  

Defines time‑of‑day anchors for daily/weekly rotation.

## Members
```
- `hour` / `minute` / `second`  —  rotation trigger time.  
- `to_seconds`                  —  convert to seconds since midnight.
```

---

# 🧹 ExpirationRule  

Defines retention policy for rotated files.

## Members
```
- `Seconds`, `Minutes`, `Hours`, `Days`, `MonthDay`  —  scale.  
- `interval`                                         — how long to keep rotated files.
```

---

# 🧱 When  

Enum for time‑based rotation modes.

## Members
```
- `SECOND` / `MINUTE` / `HOUR`  — periodic rotation.  
- `EVERYDAY`                    — daily rotation.  
- `MONDAY` … `SUNDAY`           — weekly rotation.
```

---

# 🧩 RetrievedRecord  

Strongly‑typed representation of a log record.

## Members
```
- `timestamp` / level — core fields.  
- `relative_created` / `logger_name` / `file_path` / `file_name` / `lineno` / `func_name`  —  metadata.  
- `thread_id` / `thread_name` / `task_name` / `process_id` / `process_name`                —  concurrency metadata.  
- `exc_info` / `stack_info` — diagnostics.
```

---

# 📘 Summary  
This appendix lists all LogSmith entities and the members they expose, providing a compact map of the entire API surface: loggers, handlers, formatting, rotation, colors, themes, auditing, and dynamic levels.
