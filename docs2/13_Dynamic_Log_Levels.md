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
    name="NOTICE",
    value=25,
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

You can choose any integer, but you cannot assign existing level names or level values.

---

## 🎨 Styling Dynamic Levels

Example:

```python
from LogSmith import LevelStyle, CPrint

MY_THEME = {
    "NOTICE": LevelStyle(fg=CPrint.FG.BRIGHT_MAGENTA),
}
```

Apply it:

```python
SmartLogger.apply_color_theme(MY_THEME)
```

Dynamic levels behave exactly like built‑in ones in theme mappings.

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
- and so on  

Dynamic levels integrate seamlessly with async logging, including ordering guarantees and async rotation.

---

## 🧾 Dynamic Levels in JSON / NDJSON

Dynamic levels appear naturally in JSON and NDJSON output without any additional configuration. Log entries include the dynamic level name exactly as registered:

```json
{
  "timestamp": "...",
  "level": "NOTICE",
  "message": "User logged in",
  "fields": {}
}
```

NDJSON example:

```
{"timestamp":"...","level":"NOTICE","message":"User logged in"}
```

This makes dynamic levels fully compatible with ingestion pipelines such as ELK, Loki, BigQuery, and SIEM systems.

---

## 🛰️ Dynamic Levels in Auditing

Audit logs include dynamic levels automatically:

```
2026‑02‑15 01:08:46.035 • NOTICE • User logged in
```

The audit formatter treats dynamic levels exactly like built‑in ones. No special configuration is required.

---

## 🧩 Dynamic Levels and Structured Fields

Dynamic levels support structured fields the same way built‑in levels do:

```python
logger.notice("User login", username="Gilad", action="login")
```

JSON output:

```json
"fields": {
  "username": "Gilad",
  "action": "login"
}
```

Structured fields remain fully compatible with themes, JSON, NDJSON, and auditing.

---

## Dynamic Levels + Themes  
Themes can style dynamic levels just like built‑in ones:

```python
MY_THEME["SECURITY"] = LevelStyle(
    fg=CPrint.FG.BRIGHT_RED,
    bold=True,
)
```

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

Handlers do not require any special configuration to support dynamic levels.

---

## 🚫 Removing Dynamic Levels

Dynamic levels cannot be removed at runtime.<br/>
This is intentional to avoid breaking existing loggers.

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
