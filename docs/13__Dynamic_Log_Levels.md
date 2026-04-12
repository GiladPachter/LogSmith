# 🆕 Dynamic Log Levels

LogSmith allows you to define entirely new log levels at runtime. These levels behave exactly like built‑in levels: they have numeric values, names, colors, methods (`logger.notice()`, `logger.verbose()`, etc.), and full integration with themes, handlers, JSON / NDJSON, and auditing.<br/>
This chapter explains how dynamic levels work, how to register them, how to style them, and how they interact with the rest of the logging system.

---

## 💡 Why Dynamic Levels Matter

Built‑in levels (TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL) cover most use cases, but real applications often need more nuance:

- distinguishing between *normal* INFO and *important* INFO  
- adding NOTICE, VERBOSE, SUCCESS, SECURITY, AUDIT, or DATA levels  
- creating domain‑specific levels (e.g., SQL, CACHE, EVENT)  
- improving readability by separating categories of logs  
- integrating with custom themes  

Dynamic levels give you expressive power without hacks or workarounds.

---

## 🏗️ Registering a New Level

Register a new level globally:

```python
from LogSmith import SmartLogger

SmartLogger.register_level(
    name  = "NOTICE",
    value = 25,
)
```

This:

- creates a new level named `NOTICE`  
- assigns it a numeric value of 25  
- generates a new logger method: `logger.notice()`  
- integrates it with themes, JSON / NDJSON, and auditing

You can now log:

```python
logger.notice("This is a NOTICE message")
```

Dynamic levels behave exactly like built‑in ones.

---

## 🔢 Choosing a Level Value

Common patterns:

- TRACE    → 5
- DEBUG    → 10  
- INFO     → 20  
- SUCCESS  → 22  
- NOTICE   → 25  
- WARNING  → 30  
- ERROR    → 40
- CRITICAL → 50  

Rules enforced by LogSmith:

- level names must be uppercase alphanumeric with underscores  
- level values must be unique  
- level names must be unique  
- level values must be non‑negative  
- internal SmartLogger attributes cannot be overridden  

---

## 🎨 Styling Dynamic Levels

Themes map **level numbers**, not names.

Example:

```python
from LogSmith import LevelStyle, CPrint

MY_THEME = {
    25: LevelStyle(
        fg C Print.FG.BRIGHT_MAGENTA,
        intensity = CPrint.Intensity.BOLD,
    ),
}
```

Apply it:

```python
SmartLogger.apply_color_theme(MY_THEME)
```

Dynamic levels integrate seamlessly with theme styling.

---

## 🌀 Dynamic Levels in AsyncSmartLogger

AsyncSmartLogger supports dynamic levels identically:

```python
from LogSmith import AsyncSmartLogger

AsyncSmartLogger.register_level("SUCCESS", 35)
await logger.a_success("Operation completed")
```

Async logging methods are generated automatically:

- `a_notice()`  
- `a_success()`  
- `a_verbose()`  
- etc.  

Dynamic levels integrate with:

- async ordering  
- async rotation  
- async auditing  
- structured formatting  

---

## 🧾 Dynamic Levels in JSON / NDJSON

Dynamic levels appear naturally in JSON and NDJSON output:

```json
{
  "timestamp": "...",
  "level": "NOTICE",
  "message": "User logged in",
  "named_args": {}
}
```

NDJSON example:

```
{"timestamp":"...","level":"NOTICE","message":"User logged in"}
```

No extra configuration required.

---

## 🛰️ Dynamic Levels in Auditing

Audit logs include dynamic levels automatically:

```
2026‑02‑15 01:08:46.035 • NOTICE • User logged in
```

`AuditFormatter` treats dynamic levels exactly like built‑in ones.

---

## 🧩 Dynamic Levels and Structured Fields

Dynamic levels support structured fields the same way built‑in levels do:

```python
logger.notice("User login", username = "Gilad", action = "login")
```

JSON output:

```json
"named_args": {
  "username": "Gilad",
  "action": "login"
}
```

Structured fields remain fully compatible with themes, JSON, NDJSON, and auditing.

---

## Dynamic Levels + Themes  

Themes can style dynamic levels just like built‑in ones:

```python
MY_THEME[60] = LevelStyle(
    fg = CPrint.FG.BRIGHT_RED,
    intensity = CPrint.Intensity.BOLD,
    styles = (CPrint.Style.UNDERLINE,),
)
```

Apply it:

```python
SmartLogger.apply_color_theme(MY_THEME)
```

If a dynamic level is not defined in the theme, it uses its default style.

---

## 🧰 Dynamic Levels and Handlers

Dynamic levels work seamlessly with all handler types:

- console handlers  
- file handlers  
- JSON / NDJSON handlers  
- rotation and retention  
- raw output  
- async logging  
- auditing  

Handlers require no special configuration.

---

## 🚫 Removing Dynamic Levels

Dynamic levels **cannot be removed** at runtime.<br/>
This prevents breaking existing loggers or handlers.

---

## 🧠 Best Practices for Dynamic Levels

- Choose numeric values that fit between existing levels.  
- Use dynamic levels for domain‑specific events (e.g., SQL, CACHE, EVENT).  
- Style dynamic levels with themes for readability.  
- Avoid creating too many levels — clarity matters.  
- Use JSON / NDJSON for ingestion pipelines.  
- Keep level names short, descriptive, and consistent.  

Dynamic levels should enhance clarity, not create noise.

---

## 📘 Summary

Dynamic log levels give you:

- new level names  
- new numeric values  
- new logger methods  
- theme integration  
- JSON / NDJSON support  
- async support  
- auditing support  
- structured fields  
- seamless handler compatibility  

Dynamic levels provide expressive power and flexibility, allowing you to tailor LogSmith to your application’s domain and logging needs.
