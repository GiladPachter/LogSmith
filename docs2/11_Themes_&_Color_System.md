# 🎭 Themes & Color System  

LogSmith includes a full ANSI color engine with solid colors, gradients, palettes, and theme support. Themes let you redefine how log levels appear in the console, while the color engine gives you fine‑grained control over styling, intensity, and gradients.<br/>
This chapter explains how themes work, how to customize them, and how the color system integrates with structured formatting.

---

## 💡 Why Themes Matter

Color is one of the fastest ways to make logs readable. Themes let you:

- standardize color usage across your application  
- switch between light/dark modes  
- create expressive visual styles  
- highlight important levels  
- improve scanning and debugging  

Themes affect **only console output** — file handlers remain clean and machine‑friendly unless raw ANSI is explicitly enabled.

---

## Built‑In Themes  
LogSmith ships with several built‑in themes designed for different environments and visual preferences:

- **LIGHT_THEME** — bright, high‑contrast colors  
- **DARK_THEME** — muted, dark‑mode‑friendly palette  
- **NEON_THEME** — vibrant, saturated colors  
- **PASTEL_THEME** — soft, low‑intensity colors  
- **FIRE_THEME** — warm reds, oranges, and yellows  
- **OCEAN_THEME** — cool blues and greens  

Apply a theme globally:

```python
from LogSmith import SmartLogger, DARK_THEME

SmartLogger.apply_color_theme(DARK_THEME)
```

All console handlers created afterward use the new theme automatically.

---

## 🧩 LevelStyle — The Building Block

Each log level is styled using a `LevelStyle` object. It defines:

- foreground color  
- background color  
- intensity (bold, dim)  
- text styles (underline, italic, strike)  

Example:

```python
from LogSmith import LevelStyle, CPrint

style = LevelStyle(
    fg   = CPrint.FG.BRIGHT_MAGENTA,
    bg   = CPrint.BG.BLACK,
    bold = True,
)
```

Themes are dictionaries mapping level names to `LevelStyle` objects.

---

## 🏗️ Creating a Custom Theme

A theme is simply a dictionary mapping level names to styles:

```python
from LogSmith import LevelStyle, CPrint

MY_THEME = {
    "TRACE":    LevelStyle(fg = CPrint.FG.CYAN),
    "DEBUG":    LevelStyle(fg = CPrint.FG.BLUE),
    "INFO":     LevelStyle(fg = CPrint.FG.GREEN),
    "WARNING":  LevelStyle(fg = CPrint.FG.YELLOW),
    "ERROR":    LevelStyle(fg = CPrint.FG.RED),
    "CRITICAL": LevelStyle(fg = CPrint.FG.WHITE, bg = CPrint.BG.RED, bold = True),
}
```

Apply it:

```python
SmartLogger.apply_color_theme(MY_THEME)
```

Themes can be switched at any time, and all new console handlers will use the active theme.

---

## 🎨 CPrint — The Color Engine

`CPrint` is LogSmith’s ANSI engine. It provides the low‑level building blocks that themes use to render colors and styles. It supports:

- 16‑color ANSI  
- 256‑color extended palette  
- bold, dim, underline, italic, strike  
- foreground and background colors  
- gradients  
- palette blending  

Example:

```python
from LogSmith import CPrint

text = CPrint.colorize("Hello", fg = CPrint.FG.BRIGHT_GREEN, bold = True)
logger.raw(text)
```

`CPrint` is used internally by themes, but you can also use it directly for banners, headers, and artistic output.

---

## 🌈 Gradients

Gradients are one of LogSmith’s most expressive features. They allow multi‑color transitions across text, with automatic stretching and palette blending.

Example:

```python
from LogSmith import CPrint, GradientPalette

logger.raw(CPrint.gradient(
    "Rainbow!",
    fg_codes = GradientPalette.RAINBOW
))
```

Gradient features include:

- foreground gradients  
- background gradients  
- multi‑stop palettes  
- palette blending  
- automatic scaling to text length  

Gradients are available only in raw output, not structured log messages.

---

## 🎨 Gradient Palettes

LogSmith includes several predefined gradient palettes:

- **RAINBOW**  
- **FIRE**  
- **OCEAN**  
- **FOREST**  
- **SUNSET**  
- **PASTEL**  

You can also define custom palettes:

```python
from LogSmith import GradientPalette

MY_PALETTE = GradientPalette([196, 202, 208, 214, 220])
```

Palettes can be used for both foreground and background gradients.

---

## 🚫 Themes and Raw Output

Themes affect only structured console output. Raw output bypasses themes entirely:

```python
logger.raw("This text ignores themes")
```

This is intentional. Raw output is meant for banners, headers, ASCII art, and gradient‑based visual elements. It should not be used for normal log messages.

---

## 🧱 Themes and Structured Formatting

Themes integrate seamlessly with `LogRecordDetails`. When structured formatting is enabled, themes colorize all log record fields unless configured otherwise.

Example:

```python
details = LogRecordDetails(
    color_all_log_record_fields = True,
    separator = "•",
)

logger.add_console(log_record_details = details)
SmartLogger.apply_color_theme(DARK_THEME)
```

This produces fully colorized structured logs.

---

## Themes + Dynamic Levels  
Dynamic levels automatically inherit theme colors if defined:

```python
SmartLogger.register_level("NOTICE", 25)
```

To style it:

```python
MY_THEME["NOTICE"] = LevelStyle(fg = CPrint.FG.BRIGHT_MAGENTA)
SmartLogger.apply_color_theme(MY_THEME)
```

If a dynamic level is not defined in the theme, it is unaffected by the applied theme.

---

## 📘 Summary

LogSmith’s theme and color system provides:

- built‑in themes  
- custom theme support  
- level‑aware styling  
- gradients and palettes  
- raw ANSI output  
- integration with structured formatting  
- dynamic level styling  

Themes make console output expressive, readable, and consistent across your application.
