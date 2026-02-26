# examples/07_gradient_async_demo.py

"""
Demonstrates AsyncSmartLogger's gradient capabilities:
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

import asyncio

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.colors import (
    CPrint,
    GradientDirection,
    GradientPalette,
    blend_palettes,
)


async def main():
    # ------------------------------------------------------------------------------------------------------
    # 1. Initialization
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    print("\nAsync Gradient demo\n===================")

    # ------------------------------------------------------------------------------------------------------
    # 2. Create logger with console handler
    # ------------------------------------------------------------------------------------------------------
    print("\nCreating async logger 'gradient.demo.async'...")
    await asyncio.sleep(0.1)

    lg = AsyncSmartLogger("gradient.demo.async", level=levels["TRACE"])
    lg.add_console(level=levels["TRACE"])

    # ------------------------------------------------------------------------------------------------------
    # Helper: section header
    # ------------------------------------------------------------------------------------------------------
    async def section(title: str):
        await asyncio.sleep(0.1)
        print(f"\n{title}\n" + "-" * len(title) + "\n")
        await asyncio.sleep(0.1)

    # ------------------------------------------------------------------------------------------------------
    # Helper: palette preview
    # ------------------------------------------------------------------------------------------------------
    async def preview_palette(name: str, colors: list[int]):
        await asyncio.sleep(0.1)
        print(f"{name}:")
        print(CPrint.gradient("█" * 40, fg_codes=colors) + "\n")
        await asyncio.sleep(0.1)

    # ======================================================================================================
    # 0. Palette previews
    # ======================================================================================================
    await section("0. Palette previews")

    await preview_palette("Rainbow",   GradientPalette.RAINBOW)
    await preview_palette("Sunset",    GradientPalette.SUNSET)
    await preview_palette("Ocean",     GradientPalette.OCEAN)
    await preview_palette("Fire",      GradientPalette.FIRE)
    await preview_palette("Ice",       GradientPalette.ICE)
    await preview_palette("Greyscale", GradientPalette.GREYSCALE)
    await preview_palette("Forest",    GradientPalette.FOREST)
    await preview_palette("Neon",      GradientPalette.NEON)
    await preview_palette("Pastel",    GradientPalette.PASTEL)

    # ======================================================================================================
    # 1. Basic two‑color foreground gradient
    # ======================================================================================================
    await section("1. Basic two‑color foreground gradient")

    await lg.a_raw(CPrint.gradient(
        "Red → Yellow gradient",
        fg_codes=[GradientPalette.RED, GradientPalette.YELLOW],
    ))

    # ======================================================================================================
    # 2. Three‑stop foreground gradient
    # ======================================================================================================
    await section("2. Three‑stop foreground gradient")

    await lg.a_raw(CPrint.gradient(
        "Red → Green → Blue",
        fg_codes=[GradientPalette.RED, GradientPalette.GREEN, GradientPalette.BLUE],
    ))

    # ======================================================================================================
    # 3. Rainbow foreground gradient
    # ======================================================================================================
    await section("3. Rainbow foreground gradient")

    await lg.a_raw(CPrint.gradient(
        "Full rainbow gradient",
        fg_codes=GradientPalette.RAINBOW,
    ))

    # ======================================================================================================
    # 4. Vertical foreground gradient
    # ======================================================================================================
    await section("4. Vertical foreground gradient")

    await lg.a_raw(CPrint.gradient(
        "Line 1\nLine 2\nLine 3",
        fg_codes=[GradientPalette.CYAN, GradientPalette.MAGENTA, GradientPalette.DEEP_BLUE],
        direction=GradientDirection.VERTICAL,
    ))

    # ======================================================================================================
    # 5. Background gradient
    # ======================================================================================================
    await section("5. Background gradient (ICE palette)")

    await lg.a_raw(CPrint.gradient(
        "Background gradient example.",
        bg_codes=GradientPalette.ICE,
    ))

    # ======================================================================================================
    # 6. Combined FG + BG gradient
    # ======================================================================================================
    await section("6. Combined FG + BG gradient")

    await lg.a_raw(CPrint.gradient(
        "Foreground + Background gradient",
        fg_codes=[GradientPalette.RED, GradientPalette.YELLOW, GradientPalette.GREEN],
        bg_codes=[GradientPalette.DEEP_BLUE, GradientPalette.BLUE_4, GradientPalette.CYAN],
    ))

    # ======================================================================================================
    # 7. Rainbow FG + Greyscale BG
    # ======================================================================================================
    await section("7. Rainbow FG + Greyscale BG (auto‑stretch)")

    await lg.a_raw(CPrint.gradient(
        "Rainbow FG + Greyscale BG",
        fg_codes=GradientPalette.RAINBOW,
        bg_codes=GradientPalette.GREYSCALE,
    ))

    # ======================================================================================================
    # 8. Palette blending
    # ======================================================================================================
    await section("8. Blended palette: SUNSET + OCEAN → Tropical")

    tropical = blend_palettes(GradientPalette.SUNSET, GradientPalette.OCEAN)
    await preview_palette("Tropical (blended)", tropical)
    await lg.a_raw(CPrint.gradient("Tropical blended gradient", fg_codes=tropical))

    await section("9. Blended palette: NEON + FIRE → CyberFire")

    cyberfire = blend_palettes(GradientPalette.NEON, GradientPalette.FIRE, steps=12)
    await preview_palette("CyberFire (blended)", cyberfire)
    print(CPrint.gradient("CyberFire blended gradient", fg_codes=cyberfire))
    await asyncio.sleep(0.1)

    # ======================================================================================================
    # 10. Done
    # ======================================================================================================
    await section("10. Done")

    await asyncio.sleep(0.1)
    print("All gradient features demonstrated.\n")
    print("\nAsync Gradient demo complete.\n")

    # Ensure all logs are flushed
    await lg.flush()


if __name__ == "__main__":
    asyncio.run(main())
