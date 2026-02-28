# Dynamic Log Levels  
LogSmith allows you to define entirely new log levels at runtime. These levels behave exactly like built‑in levels: they have numeric values, names, colors, methods (`logger.notice()`, `logger.verbose()`, etc.), and full integration with themes, handlers, JSON/NDJSON, and auditing.

This chapter explains how dynamic levels work, how to register them, how to style them, and how they interact with the rest of the logging system.

---

## Why Dynamic Levels Matter  
Built‑in levels (TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL) cover most use cases, but real applications often need more nuance:

- distinguishing between *normal* INFO and *important* INFO  
- adding NOTICE, VERBOSE, SUCCESS, SECURITY, AUDIT, or DATA levels  
- creating domain‑specific levels (e.g., SQL, CACHE, EVENT)  
- improving readability by separating categories of logs  
- integrating with custom themes  

Dynamic levels give you expressive power without hacks or workarounds.

---

## Registering a New Level  
Register a new level globally:

```python
from LogSmith import SmartLogger

SmartLogger.register_level(
    name="NOTICE",
    value=25,
)
```

This creates:

- a new level named `NOTICE`  
- a numeric value of 25  
- a new logger method: `logger.notice()`  
- theme support for NOTICE  
- JSON/NDJSON support  
- auditing support  

You can now log:

```python
logger.notice("This is a NOTICE message")
```

---

## Choosing a Level Value  
Level values determine ordering and filtering.

Common patterns:

- VERBOSE → 5  
- TRACE → 10  
- DEBUG → 20  
- NOTICE → 25  
- INFO → 30  
- SUCCESS → 35  
- WARNING → 40  
- ERROR → 50  
- CRITICAL → 60  

You can choose any integer, but avoid collisions with existing levels unless you intentionally want identical behavior.

---

## Styling Dynamic Levels  
Dynamic levels automatically inherit theme colors if defined.

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

Now NOTICE logs appear in bright magenta.

---

## Dynamic Levels in AsyncSmartLogger  
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

---

## Dynamic Levels + JSON / NDJSON  
Dynamic levels appear naturally in JSON output:

```json
{
  "timestamp": "...",
  "level": "NOTICE",
  "message": "User logged in",
  "fields": {}
}
```

NDJSON:

```
{"timestamp":"...","level":"NOTICE","message":"User logged in"}
```

No extra configuration required.

---

## Dynamic Levels + Auditing  
Audit logs include dynamic levels automatically:

```
2026‑02‑15 01:08:46.035 • NOTICE • User logged in
```

Audit formatters treat them like any other level.

---

## Dynamic Levels + Structured Fields  
Dynamic levels support structured fields:

```python
logger.notice("User login", username="Gilad", action="login")
```

JSON:

```json
"fields": {
  "username": "Gilad",
  "action": "login"
}
```

---

## Dynamic Levels + Themes  
Themes can style dynamic levels just like built‑in ones:

```python
MY_THEME["SECURITY"] = LevelStyle(
    fg=CPrint.FG.BRIGHT_RED,
    bold=True,
)
```

Apply:

```python
SmartLogger.apply_color_theme(MY_THEME)
```

---

## Dynamic Levels + Handlers  
Dynamic levels work with:

- console handlers  
- file handlers  
- JSON/NDJSON  
- rotation  
- retention  
- raw output  
- async logging  
- auditing  

Handlers do not need special configuration.

---

## Removing Dynamic Levels  
Dynamic levels cannot be removed at runtime.  
This is intentional to avoid breaking existing loggers.

---

## Best Practices  
- Choose numeric values that fit between existing levels.  
- Use dynamic levels for domain‑specific events.  
- Style them with themes for readability.  
- Avoid creating too many levels — clarity matters.  
- Use JSON/NDJSON for ingestion pipelines.  

---

## Summary  
Dynamic log levels give you:

- new level names  
- new numeric values  
- new logger methods  
- theme integration  
- JSON/NDJSON support  
- async support  
- auditing support  
- structured fields  

The next chapter covers **Logger Hierarchy**, explaining how loggers inherit levels, how propagation works, and how to organize large applications cleanly.
