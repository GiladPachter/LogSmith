# 🧱 Structured Formatting  
LogSmith’s formatting engine is the heart of the entire framework. Instead of brittle format strings, LogSmith uses a declarative model that describes *what* a log entry should contain and *how* it should look. This chapter explains how structured formatting works, how to customize it, and how it integrates with console, file, JSON, and NDJSON output.

---

## � Why Structured Formatting Matters  
Traditional logging forces you to build format strings like:

```
"%(asctime)s - %(levelname)s - %(message)s"
```

These are:

- hard to read  
- hard to maintain  
- inconsistent across handlers  
- difficult to extend with new fields  
- incompatible with JSON / NDJSON  

LogSmith replaces this with a **structured, explicit, predictable and easy to use model**.

---

## 🔹 LogRecordDetails &nbsp; (the formatting blueprint)  
Every handler (console or file) uses a `LogRecordDetails` object to define:

- timestamp format  
- separator character  
- which metadata fields appear  
- the order of metadata fields  
- how colors are applied  
- how exceptions are formatted  
- how structured fields appear  
- how JSON / NDJSON is generated  

Example:

```python
from LogSmith import LogRecordDetails, OptionalRecordFields

details = LogRecordDetails(
    datefmt = "%Y-%m-%d %H:%M:%S.%3f",
    separator = "•",
    optional_record_fields = OptionalRecordFields(
        logger_name = True,
        file_name   = True,
        lineno      = True,
        func_name   = True,
    ),
    message_parts_order = [
        "level",
        "logger_name",
        "file_name",
        "lineno",
        "func_name",
    ],
    color_all_log_record_fields = True,
)
```

Attach it to a handler:

```python
logger.add_console(log_record_details = details)
```

---

## 🔹OptionalRecordFields  
This object controls which metadata fields appear in the log entry:

- logger_name  
- file_name  
- lineno  
- func_name  
- thread_id  
- process_id  
- module_name  
- pathname  

Example:

```python
OptionalRecordFields(
    logger_name = True,
    lineno      = True,
    thread_id   = True,
)
```

If a field is disabled, it simply doesn’t appear — no empty placeholders.

---

## 🔹Field Ordering  
`message_parts_order` defines the order of metadata fields.  
Two fields are *always* fixed:

- timestamp → always first  
- message → always last  

Everything else is up to you.

Example:

```python
message_parts_order = [
    "level",
    "logger_name",
    "lineno",
]
```

Produces:

```
2026‑02‑15 01:08:46.035 • INFO • myapp • 42 • User login
```

---

## 🔹Separator  
The separator appears between metadata fields:

```python
separator = "•"
```

Common choices:

- `"•"`  
- `"|"`  
- `"—"`  
- `"::"`  
- `"→"`  

---

## 🔹Coloring Rules  
You control how color is applied:

### Color only level + message (default)
```python
color_all_log_record_fields = False
```

### Color everything
```python
color_all_log_record_fields = True
```

### No color (PLAIN mode)
```python
output_mode = OutputMode.PLAIN
```

### JSON / NDJSON ignores color entirely
Color is not included in JSON output.

---

## 🔹Structured Fields (Named Arguments)  
Named arguments become structured fields:

```python
logger.info("User login", username = "Gilad", action = "login")
```

Console output:

```
… • INFO • User login {username = 'Gilad', action = 'login'}
```

JSON output:

```json
{
  "message": "User login",
  "fields": {
    "username": "Gilad",
    "action": "login"
  }
}
```

NDJSON output:

```
{"timestamp":"...","level":"INFO","message":"User login","fields":{"username":"Gilad","action":"login"}}
```

---

## 🔹Exception & Stack Formatting  
LogSmith formats exceptions cleanly:

```python
try:
    1 / 0
except Exception:
    logger.error("Something went wrong", exc_info = True)
```

Output includes:

- exception type  
- message  
- full traceback  
- structured fields (if any)  

JSON / NDJSON include structured exception objects.

---

## 🔹JSON Formatting  
Pretty JSON output:

```python
logger.add_console(output_mode = OutputMode.JSON)
```

Produces:

```json
{
  "timestamp": "2026-02-15T01:08:46.035Z",
  "level": "INFO",
  "message": "User login",
  "fields": {
    "username": "Gilad"
  }
}
```

---

## 🔹NDJSON Formatting  
NDJSON is compact and ingestion‑friendly:

```python
logger.add_file(
    log_dir      = Path(ROOT_DIR) / "Logs" / "examples" / "NDJSON_demo",
    logfile_name = "events.ndjson",
    output_mode  = OutputMode.NDJSON,
)
```

Each line is a complete JSON object:

```
{"timestamp":"...","level":"INFO","message":"User login","fields":{"username":"Gilad"}}
```

Perfect for:

- ELK  
- Loki  
- BigQuery  
- Data pipelines  
- Log processors  

---

## 🔹Raw Output  
Raw output bypasses formatting:

```python
logger.raw("This is raw text")
```

Useful for:

- banners  
- headers  
- gradient art  
- debugging dumps  

File handlers sanitize ANSI unless disabled.

---

## 🧱 Putting It All Together  
A fully customized handler:

```python
details = LogRecordDetails(
    datefmt = "%H:%M:%S",
    separator = "|",
    optional_record_fields = OptionalRecordFields(
        logger_name = True,
        lineno      = True,
    ),
    message_parts_order = [
        "level",
        "logger_name",
        "lineno",
    ],
    color_all_log_record_fields = True,
)

logger.add_console(
    level              = levels["DEBUG"],
    log_record_details = details,
    output_mode        = OutputMode.COLOR,  # default
)
```

Produces:

```
12:45:03 | DEBUG | myapp | 42 | User login {username = 'Gilad'}
```

---

## 🧩 Summary  
Structured formatting gives you:

- predictable, explicit control  
- clean, readable logs  
- consistent formatting across handlers  
- JSON / NDJSON compatibility  
- flexible metadata fields  
- customizable ordering  
- color control  
- exception structuring  
