# 🎨 Color & Gradient System

SmartLogger includes a full ANSI color engine (`CPrint`) that supports:

- solid foreground colors
- solid background colors
- 256‑color gradients
- foreground + background gradients
- multi‑line vertical gradients
- auto‑stretching of palettes
- named palettes (`GradientPalette`)
- palette blending (`blend_palettes`)
- reverse‑video transformations
- ANSI stripping and escaping

This makes SmartLogger ideal for expressive console output, banners, demos, and debugging tools.

---

# 🔹 Solid Colors

Use `CPrint.colorize()` to apply foreground, background, intensity, and styles:

```python
from LogSmith import CPrint

text = CPrint.colorize(
    "Hello",
    fg=CPrint.FG.BRIGHT_RED,
    bg=CPrint.BG.BLACK,
    intensity=CPrint.Intensity.BOLD,
)
logger.raw(text)
```

Supported style groups:

- `FG` — foreground colors
- `BG` — background colors
- `Intensity` — normal, bold, dim
- `Style` — underline, italic, strike

---

# 🔹 Foreground Gradients

```python
from LogSmith import CPrint, GradientPalette

logger.raw(CPrint.gradient(
    "Rainbow text!",
    fg_codes=GradientPalette.RAINBOW,
))
```

Gradients automatically stretch to match the text length.

---

# 🔹 Background Gradients

```python
logger.raw(CPrint.gradient(
    "Background gradient",
    bg_codes = GradientPalette.ICE,
))
```

Foreground and background gradients can be combined.

---

# 🔹 Vertical Gradients (Multi‑Line)

```python
logger.raw(CPrint.gradient(
    "Line 1\nLine 2\nLine 3",
    fg_codes = [21, 51, 231],
    direction = GradientDirection.VERTICAL,
))
```

SmartLogger automatically detects multi‑line text when using `AUTO`.

---

# 🔹 Combined FG + BG Gradients

```python
logger.raw(CPrint.gradient(
    "Dual gradient",
    fg_codes = GradientPalette.FIRE,
    bg_codes = GradientPalette.OCEAN,
))
```

Foreground and background palettes are auto‑stretched independently.

---

# 🔹 Named Palettes

SmartLogger includes many built‑in palettes:

- `RAINBOW`
- `SUNSET`
- `OCEAN`
- `FIRE`
- `ICE`
- `GREYSCALE`
- `FOREST`
- `NEON`
- `PASTEL`

Example preview:

```python
logger.raw(CPrint.gradient("████████████████████████", fg_codes = GradientPalette.SUNSET))
```

---

# 🔹 Palette Blending

Blend two palettes into a new one:

```python
from LogSmith import blend_palettes

tropical = blend_palettes(GradientPalette.SUNSET, GradientPalette.OCEAN)
logger.raw(CPrint.gradient("Tropical!", fg_codes=tropical))
```

You can specify the number of steps:

```python
cyberfire = blend_palettes(GradientPalette.NEON, GradientPalette.FIRE, steps = 12)
```

---

# 🔹 Reverse Video

Swap foreground and background colors:

```python
rev = CPrint.reverse(colored_text)
logger.raw(rev)
```

---

# 🔹 ANSI Utilities

SmartLogger includes helpers for debugging ANSI output:

```python
CPrint.strip_ansi(text)              # remove ANSI codes
CPrint.escape_ansi_for_display(text) # show \x1b sequences
CPrint.escape_control_chars(text)    # escape all control chars
```

These are extremely useful when inspecting log files or debugging color issues.

---

# 🧩 Summary

SmartLogger’s color engine provides:

- expressive solid colors
- powerful gradient rendering
- named palettes and blending
- multi‑line vertical gradients
- reverse‑video transformations
- ANSI debugging utilities

This makes SmartLogger ideal for demos, CLI tools, dashboards, and any application that benefits from expressive console output.
