# 💻 Console Logging  
Console output is where LogSmith really shines. You get structured, readable log entries with level‑aware colors, optional metadata, gradients, themes, and full control over formatting.

This chapter covers everything you can do with console logging — from basic usage to advanced customization.

---

## 🔹 Adding a Console Handler  
A logger may have **one** console handler. You attach it explicitly:

```python
logger.add_console(level = levels["INFO"])
```

This gives you:

- colorized output  
- structured formatting  
- level‑aware styling  
- predictable behavior  

No global configuration, no format strings.

---

## 🔹 Basic Console Output  
Once the console handler is attached:

```python
logger.trace("trace message")
logger.debug("debug message")
logger.info("info message")
logger.warning("warning message")
logger.error("error message")
logger.critical("critical message")
```

Each level is styled by default according to its `LevelStyle`:

- TRACE → soft purple  
- DEBUG → cyan  
- INFO → neon green  
- WARNING → neon yellow  
- ERROR → neon red
- CRITICAL → neon yellow on neon red  

Themes can override these colors (covered later on).

---

## 🔹 Structured Console Output  
Console logs are structured by default:

```
2026‑02‑15 01:08:46.035 • INFO • User login {username = 'Gilad', action = 'login'}
```

You control the structure using `LogRecordDetails`.

---

## 🔹 Customizing Console Formatting  
You can choose:

- which metadata fields appear  
- the order of fields  
- the separator character  
- timestamp format  
- whether to colorize all fields or only level + message  

Example:

```python
from LogSmith import LogRecordDetails, OptionalRecordFields

details = LogRecordDetails(
    datefmt = "%Y-%m-%d %H:%M:%S.%2f",
    separator = "•",
    optional_record_fields = OptionalRecordFields(
        logger_name = True,
        file_name   = True,
        lineno      = True,
        func_name   = True,
    ),
    message_parts_order=[
        "level",        # level must be positioned vs. optional record fields
        "logger_name",
        "file_name",
        "lineno",
        "func_name",
    ],
    color_all_log_record_fields = True,
)

logger.add_console(level = levels["TRACE"], log_record_details = details)
```

This produces a fully colorized, structured entry.

---

## 🔹 Named Arguments (Structured Fields)  
Named arguments become structured fields:

```python
logger.info("User login", username = "Gilad", action = "login")
```

Console output:

```
… • INFO • User login {username = 'Gilad', action = 'login'}
```

These fields also appear in JSON / NDJSON output.

---

## 🔹 Raw Console Output  
Raw output bypasses formatting and writes directly to the console handler:

```python
logger.raw("This is raw text")
```

Raw output:

- preserves ANSI colors  
- does not include timestamp, level, named arguments or diagnostics (specified later on)
- is ideal for banners, headers, and gradient art  

Example:

```python
from LogSmith import CPrint

logger.raw(CPrint.colorize("RAW colored text", fg = CPrint.FG.BRIGHT_RED))
```

---

## 🔹 Gradient Output  
LogSmith integrates a full gradient engine:

```python
from LogSmith import CPrint, GradientPalette

logger.raw(CPrint.gradient(
    "Rainbow!",
    fg_codes = GradientPalette.RAINBOW
))
```

Out-of-the-box gradient styles:

- foreground gradients  
- background gradients  
- multi‑stop gradients  
- vertical gradients  
- auto‑stretching  
- palette blending  

Gradients work anywhere raw ANSI does.

---

## 🔹 Themes  
Themes redefine how levels are colored:

```python
from LogSmith import DARK_THEME

SmartLogger.apply_color_theme(DARK_THEME)
logger.info("Dark theme activated!")
```

Built‑in themes:

- LIGHT_THEME  
- DARK_THEME  
- NEON_THEME  
- PASTEL_THEME  
- FIRE_THEME  
- OCEAN_THEME  

Themes affect only console output.

---

## 🔹 Output Modes  
Console handlers support multiple output modes:

- **COLOR** — structured, colorized text (default)  
- **PLAIN** — structured text, no color  
- **JSON** — pretty‑printed JSON  
- **NDJSON** — compact JSON, one object per line  

Example:

```python
logger.add_console(output_mode = OutputMode.JSON)
```

This is great for debugging or piping logs into tools.

---

## 🔹 Handler Introspection  
You can inspect `logger.console_handler` to access metadata that describes a logger's console handler.

This returns a clean dictionary describing:
- handler type
- level
- formatter  
- output mode  

---

## 🔹 stdout(): Synchronized Printing
Python's built-in `print()` interleaves output and does not synchronize with logging.
LogSmith provides a synchronized replacement.

```python
from LogSmith import SmartLogger, stdout

stdout("This prints in sync with SmartLogger logs")
```

This ensures:
- no interleaving  
- consistent ordering  
- clean and sensible console output  

---

## 🧩 Summary  
Console logging in LogSmith gives you:

- structured, readable output  
- level‑aware colors  
- themes  
- gradients  
- raw ANSI output  
- JSON / NDJSON modes  
- full control over formatting  

The next chapter covers file logging — rotation, retention, sanitization, and concurrency safety.
