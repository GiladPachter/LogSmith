# 🆕 Custom Log Levels

SmartLogger allows you to define **new log levels at runtime**, complete with:

- a numeric severity
- a name
- a color/style theme
- an auto‑generated logger method (e.g., `logger.notice()`)

This is far more flexible than Python’s built‑in logging system.

---

# 🔹 Registering a New Level

```python
from LogSmith import SmartLogger

SmartLogger.register_level("NOTICE", 25)
```

This creates:

- a new level named `NOTICE`
- severity `25`
- a new method:
  ```python
  logger.notice("Hello!")
  ```

---

# 🔹 Customizing Level Style

```python
from LogSmith import LevelStyle, CPrint

SmartLogger.register_level(
    "ALERT",
    45,
    style=LevelStyle(
        fg=CPrint.FG.BRIGHT_YELLOW,
        bg=CPrint.BG.RED,
        intensity=CPrint.Intensity.BOLD,
    ),
)
```

Now you can log:

```python
logger.alert("System temperature critical")
```

---

# 🔹 Overriding Existing Levels

```python
SmartLogger.register_level("WARNING", 30, style=LevelStyle(...))
```

This updates:

- the level’s numeric value
- its color/style
- its method (`logger.warning`)

---

# 🔹 Listing All Levels

```python
levels = SmartLogger.levels()
print(levels)
```

This returns a dictionary:

```
{
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "NOTICE": 25,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "ALERT": 45,
}
```

---

# 🔹 Using Custom Levels in Handlers

Handlers accept custom levels just like built‑ins:

```python
logger.add_console(level=levels["NOTICE"])
logger.add_file(level=levels["ALERT"])
```

---

# 🧩 Summary

LogSmith’s dynamic level system provides:

- runtime level creation
- custom color/style themes
- auto‑generated logger methods
- full integration with handlers
- ability to override built‑in levels

This makes LogSmith ideal for applications that need domain‑specific severity levels.
