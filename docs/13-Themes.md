# 🎭 Themes

SmartLogger includes a simple but powerful theming system that lets you instantly restyle the colors used for each log level.</br>
A theme is just a dictionary:

```
Dict[int, LevelStyle]
```

where the keys are numeric log levels:

```
5  = TRACE
10 = DEBUG
20 = INFO
30 = WARNING
40 = ERROR
50 = CRITICAL
```

and the values are `LevelStyle` objects defining:

- foreground color
- background color (optional)
- intensity (normal, bold, dim)
- styles (underline, italic, etc.)

Themes apply globally and affect all SmartLogger instances unless overridden manually.

---

## 🔹 Built‑In Themes

SmartLogger ships with several ready‑made themes:

- **LIGHT_THEME** — bright, readable colors for light terminals
- **DARK_THEME** — high‑contrast colors for dark terminals
- **NEON_THEME** — vibrant ANSI‑256 colors
- **PASTEL_THEME** — soft, muted tones
- **Fire_THEME** — red colors
- **OCEAN_THEME** — blue colors

Example:

```python
THEME_DARK = {
    5:  LevelStyle(fg=CPrint.FG.BRIGHT_BLACK),
    10: LevelStyle(fg=CPrint.FG.BLUE),
    20: LevelStyle(fg=CPrint.FG.GREEN),
    30: LevelStyle(fg=CPrint.FG.ORANGE),
    40: LevelStyle(fg=CPrint.FG.RED),
    50: LevelStyle(
            fg=CPrint.FG.YELLOW,
            bg=CPrint.BG.RED,
            styles=(CPrint.Style.UNDERLINE,)
        ),
}
```

---

## 🔹 Applying a Theme Globally

```python
from LogSmith import SmartLogger
from LogSmith.themes import DARK_THEME

SmartLogger.apply_theme(DARK_THEME)
```

---

## 🔹 Creating Your Own Theme

```python
from LogSmith import LevelStyle, CPrint

MY_THEME = {
    5: LevelStyle(fg=CPrint.FG.CYAN),
    10: LevelStyle(fg=CPrint.FG.BLUE),
    20: LevelStyle(fg=CPrint.FG.GREEN),
    30: LevelStyle(fg=CPrint.FG.YELLOW),
    40: LevelStyle(fg=CPrint.FG.RED),
    50: LevelStyle(
        fg=CPrint.FG.WHITE,
        bg=CPrint.BG.RED,
        intensity=CPrint.Intensity.BOLD,
        styles=(CPrint.Style.UNDERLINE,)
    ),
}
```

Apply it:

```python
SmartLogger.apply_color_theme(MY_THEME)
```
---

## 🔹 Resetting to Default Theme

```python
SmartLogger.apply_color_theme(None)
```

---

# 🧩 Summary

SmartLogger’s theme system is:

- simple (just dictionaries)
- flexible (customize any level)
- expressive (supports ANSI‑256 colors)
- global (affects all loggers)

Themes let you instantly change the visual identity of your logs.
