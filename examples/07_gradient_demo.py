# examples/07_gradient_demo.py

"""
Demonstrates SmartLogger's gradient capabilities:
- Palette previews
- Foreground gradients (2‑stop, 3‑stop, multi‑stop)
- Vertical gradients
- Background gradients
- Combined FG + BG gradients
- Palette blending
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import time

from smartlogger import SmartLogger
from smartlogger.colors import (
    CPrint,
    GradientDirection,
    GradientPalette,
    blend_palettes,
)


# ----------------------------------------------------------------------------------------------------------
# 1. Initialization — MUST be done at application entry point
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["TRACE"])

print("\nGradient demo\n=============")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 2. Create logger with console handler
# ----------------------------------------------------------------------------------------------------------
print("\nCreating logger 'gradient.demo'...")
time.sleep(0.1)

lg = SmartLogger.get("gradient.demo", level=levels["TRACE"])
lg.add_console(level=levels["TRACE"])


# ----------------------------------------------------------------------------------------------------------
# Helper: section header
# ----------------------------------------------------------------------------------------------------------
def section(title: str):
    print(f"\n{title}\n" + "-" * len(title))
    time.sleep(0.1)
    lg.raw("")  # visual spacing


# ----------------------------------------------------------------------------------------------------------
# Helper: palette preview
# ----------------------------------------------------------------------------------------------------------
def preview_palette(name: str, colors: list[int]):
    lg.raw(f"{name}:")
    lg.raw(CPrint.gradient("█" * 40, fg_codes=colors))
    lg.raw("")


# ==========================================================================================================
# 0. Palette previews
# ==========================================================================================================
section("0. Palette previews")

preview_palette("Rainbow",   GradientPalette.RAINBOW)
preview_palette("Sunset",    GradientPalette.SUNSET)
preview_palette("Ocean",     GradientPalette.OCEAN)
preview_palette("Fire",      GradientPalette.FIRE)
preview_palette("Ice",       GradientPalette.ICE)
preview_palette("Greyscale", GradientPalette.GREYSCALE)
preview_palette("Forest",    GradientPalette.FOREST)
preview_palette("Neon",      GradientPalette.NEON)
preview_palette("Pastel",    GradientPalette.PASTEL)


# ==========================================================================================================
# 1. Basic two‑color foreground gradient
# ==========================================================================================================
section("1. Basic two‑color foreground gradient")

lg.raw(CPrint.gradient(
    "Red → Yellow gradient",
    fg_codes=[GradientPalette.RED, GradientPalette.YELLOW],
))


# ==========================================================================================================
# 2. Three‑stop foreground gradient
# ==========================================================================================================
section("2. Three‑stop foreground gradient")

lg.raw(CPrint.gradient(
    "Red → Green → Blue",
    fg_codes=[GradientPalette.RED, GradientPalette.GREEN, GradientPalette.BLUE],
))


# ==========================================================================================================
# 3. Rainbow foreground gradient
# ==========================================================================================================
section("3. Rainbow foreground gradient")

lg.raw(CPrint.gradient(
    "Full rainbow gradient",
    fg_codes=GradientPalette.RAINBOW,
))


# ==========================================================================================================
# 4. Vertical foreground gradient
# ==========================================================================================================
section("4. Vertical foreground gradient")

lg.raw(CPrint.gradient(
    "Line 1\nLine 2\nLine 3",
    fg_codes=[GradientPalette.CYAN, GradientPalette.MAGENTA, GradientPalette.DEEP_BLUE],
    direction=GradientDirection.VERTICAL,
))


# ==========================================================================================================
# 5. Background gradient
# ==========================================================================================================
section("5. Background gradient (ICE palette)")

lg.raw(CPrint.gradient(
    "Background gradient example.",
    bg_codes=GradientPalette.ICE,
))


# ==========================================================================================================
# 6. Combined FG + BG gradient
# ==========================================================================================================
section("6. Combined FG + BG gradient")

lg.raw(CPrint.gradient(
    "Foreground + Background gradient",
    fg_codes=[GradientPalette.RED, GradientPalette.YELLOW, GradientPalette.GREEN],
    bg_codes=[GradientPalette.DEEP_BLUE, GradientPalette.BLUE_4, GradientPalette.CYAN],
))


# ==========================================================================================================
# 7. Rainbow FG + Greyscale BG
# ==========================================================================================================
section("7. Rainbow FG + Greyscale BG (auto‑stretch)")

lg.raw(CPrint.gradient(
    "Rainbow FG + Greyscale BG",
    fg_codes=GradientPalette.RAINBOW,
    bg_codes=GradientPalette.GREYSCALE,
))


# ==========================================================================================================
# 8. Palette blending
# ==========================================================================================================
section("8. Blended palette: SUNSET + OCEAN → Tropical")

tropical = blend_palettes(GradientPalette.SUNSET, GradientPalette.OCEAN)
preview_palette("Tropical (blended)", tropical)
lg.raw(CPrint.gradient("Tropical blended gradient", fg_codes=tropical))


section("9. Blended palette: NEON + FIRE → CyberFire")

cyberfire = blend_palettes(GradientPalette.NEON, GradientPalette.FIRE, steps=12)
preview_palette("CyberFire (blended)", cyberfire)
lg.raw(CPrint.gradient("CyberFire blended gradient", fg_codes=cyberfire))


# ==========================================================================================================
# 10. Done
# ==========================================================================================================
section("10. Done")

lg.raw("All gradient features demonstrated.")

time.sleep(0.1)
print("Gradient demo complete.\n")
