# smartlogger/colors.py

import os
import sys
from typing import Iterable, Sequence, Union
from enum import Enum
import re


Code = Union[int, str]


def terminal_supports_color() -> bool:
    if sys.platform == "win32":
        return True

    # Windows: check if ANSI is enabled
    return os.getenv("ANSICON") or os.getenv("WT_SESSION") or sys.stdout.isatty()


class GradientDirection(Enum):
    """
    Direction for 256-color gradients.

    HORIZONTAL          left → right
    HORIZONTAL_REVERSE  right → left
    VERTICAL            top → bottom (multi-line)
    VERTICAL_REVERSE    bottom → top
    AUTO                horizontal for 1 line, vertical for multi-line
    """

    HORIZONTAL = "horizontal"
    HORIZONTAL_REVERSE = "horizontal-reverse"
    VERTICAL = "vertical"
    VERTICAL_REVERSE = "vertical-reverse"
    AUTO = "auto"


class CPrint:
    """
    CPrint: A semantic ANSI color engine.

    Responsibilities:
        - Provide structured foreground/background color groups
        - Provide intensity and style groups
        - Provide solid colorization via `colorize()`
        - Provide gradient colorization via `gradient()`
        - Provide reverse-video color swapping via `reverse()`
    """

    class FG:
        BLACK: Code = 30
        RED: Code = 31
        GREEN: Code = 32
        YELLOW: Code = 33
        BLUE: Code = 34
        MAGENTA: Code = 35
        CYAN: Code = 36
        WHITE: Code = 37

        BRIGHT_BLACK: Code = 90
        BRIGHT_RED: Code = 91
        BRIGHT_GREEN: Code = 92
        BRIGHT_YELLOW: Code = 93
        BRIGHT_BLUE: Code = 94
        BRIGHT_MAGENTA: Code = 95
        BRIGHT_CYAN: Code = 96
        BRIGHT_WHITE: Code = 97

        ORANGE: Code = "38;5;208"
        SOFT_PURPLE: Code = "38;5;141"
        GREY: Code = "38;5;244"
        DIM_GREY: Code = "38;5;240"
        BRIGHT_GREY: Code = "38;5;248"
        TRUE_WHITE: Code = "38;2;255;255;255"
        CONSOLE_DEFAULT: Code = "38;2;188;188;188"

        NEON_CYAN: Code = "38;5;51"
        NEON_MAGENTA: Code = "38;5;201"
        NEON_GREEN: Code = "38;5;46"
        NEON_YELLOW: Code = "38;5;226"
        NEON_RED: Code = "38;5;196"

        # Yellow‑Green / Chartreuse
        CHARTREUSE = "38;5;190"
        CHARTREUSE_GREEN = "38;5;154"
        CHARTREUSE_YELLOW = "38;5;191"

        # Green‑Cyan Hybrids
        SPRING_GREEN = "38;5;48"
        MINT_GREEN = "38;5;49"
        AQUA_GREEN = "38;5;50"

        # Cyan‑Blue Hybrids
        SKY_BLUE = "38;5;117"
        ICE_BLUE = "38;5;123"
        SOFT_AZURE = "38;5;159"

        # Blue‑Magenta Hybrids
        PERIWINKLE = "38;5;104"
        LAVENDER = "38;5;147"
        SOFT_VIOLET = "38;5;183"

        # Magenta‑Red Hybrids
        HOT_PINK = "38;5;205"
        ROSE = "38;5;212"
        CORAL_PINK = "38;5;211"

        # Orange Family
        LIGHT_ORANGE = "38;5;215"
        SOFT_ORANGE = "38;5;216"
        PEACH = "38;5;223"

        # Neutral Hybrids
        BLUE_GREY = "38;5;67"
        GREEN_GREY = "38;5;65"
        PURPLE_GREY = "38;5;103"

    class BG:
        BLACK: Code = 40
        RED: Code = 41
        GREEN: Code = 42
        YELLOW: Code = 43
        BLUE: Code = 44
        MAGENTA: Code = 45
        CYAN: Code = 46
        WHITE: Code = 47

        BRIGHT_BLACK: Code = 100
        BRIGHT_RED: Code = 101
        BRIGHT_GREEN: Code = 102
        BRIGHT_YELLOW: Code = 103
        BRIGHT_BLUE: Code = 104
        BRIGHT_MAGENTA: Code = 105
        BRIGHT_CYAN: Code = 106
        BRIGHT_WHITE: Code = 107

        ORANGE: Code = "48;5;208"
        SOFT_PURPLE: Code = "48;5;141"

        NEON_CYAN: Code = "48;5;51"
        NEON_MAGENTA: Code = "48;5;201"
        NEON_GREEN: Code = "48;5;46"
        NEON_YELLOW: Code = "48;5;226"
        NEON_RED: Code = "48;5;196"

        # Yellow‑Green / Chartreuse
        CHARTREUSE: Code = "48;5;190"
        CHARTREUSE_GREEN: Code = "48;5;154"
        CHARTREUSE_YELLOW: Code = "48;5;191"

        # Green‑Cyan Hybrids
        SPRING_GREEN: Code = "48;5;48"
        MINT_GREEN: Code = "48;5;49"
        AQUA_GREEN: Code = "48;5;50"

        # Cyan‑Blue Hybrids
        SKY_BLUE: Code = "48;5;117"
        ICE_BLUE: Code = "48;5;123"
        SOFT_AZURE: Code = "48;5;159"

        # Blue‑Magenta Hybrids
        PERIWINKLE: Code = "48;5;104"
        LAVENDER: Code = "48;5;147"
        SOFT_VIOLET: Code = "48;5;183"

        # Magenta‑Red Hybrids
        HOT_PINK: Code = "48;5;205"
        ROSE: Code = "48;5;212"
        CORAL_PINK: Code = "48;5;211"

        # Orange Family
        LIGHT_ORANGE: Code = "48;5;215"
        SOFT_ORANGE: Code = "48;5;216"
        PEACH: Code = "48;5;223"

        # Neutral Hybrids
        BLUE_GREY: Code = "48;5;67"
        GREEN_GREY: Code = "48;5;65"
        PURPLE_GREY: Code = "48;5;103"

    class Intensity:
        NORMAL: Code = 22
        BOLD: Code = 1
        DIM: Code = 2

    class Style:
        ITALIC: Code = 3
        UNDERLINE: Code = 4
        STRIKE: Code = 9
        _REVERSE: Code = 7

    _RESET = "\033[0m"

    _ANSI_RE = re.compile(r"\033\[([0-9;]+)m")

    _NO_COLOR = not terminal_supports_color()

    @classmethod
    def _join_codes(cls, codes: Iterable[Code]) -> str:
        parts: list[str] = []
        for c in codes:
            if isinstance(c, int):
                parts.append(str(c))
            elif isinstance(c, str):
                parts.append(c)
        if not parts:
            return ""
        return f"\033[{';'.join(parts)}m"

    @classmethod
    def colorize(
        cls,
        text: str,
        *,
        fg: Code | None = None,
        bg: Code | None = None,
        intensity: Code | None = None,
        styles: Sequence[Code] | None = None,
    ) -> str:
        """
        Solid colorization method.
        """

        if cls._NO_COLOR:
            return text

        codes: list[Code] = []
        if intensity is not None:
            codes.append(intensity)
        if fg is not None:
            codes.append(fg)
        if bg is not None:
            codes.append(bg)
        if styles:
            codes.extend(styles)

        prefix = cls._join_codes(codes)
        if not prefix:
            return text
        return f"{prefix}{text}{cls._RESET}"

    @classmethod
    def gradient(
            cls,
            text: str,
            *,
            fg_codes: Sequence[int] | None = None,
            bg_codes: Sequence[int] | None = None,  # ← NEW
            direction: GradientDirection = GradientDirection.HORIZONTAL,
            intensity: Code | None = None,
            styles: Sequence[Code] | None = None,
    ) -> str:
        """
        Apply a 256-color gradient across the text.
        """

        if cls._NO_COLOR:
            return text

        if not text or not fg_codes:
            return text

        lines = text.split("\n")
        multi = len(lines) > 1

        # --- AUTO-STRETCH FG/BG LISTS TO MATCH LENGTH ---
        def stretch(stops: list[int], target_len: int) -> list[int]:
            if len(stops) == target_len:
                return stops
            if len(stops) == 1:
                return stops * target_len  # repeat single color
            stretched = []
            for i in range(target_len):
                idx = int(i * (len(stops) - 1) / (target_len - 1))
                stretched.append(stops[idx])
            return stretched

        # Normalize fg_codes / bg_codes
        if fg_codes:
            fg_codes = stretch(list(fg_codes), max(len(fg_codes), len(bg_codes or fg_codes)))
        if bg_codes:
            bg_codes = stretch(list(bg_codes), max(len(bg_codes), len(fg_codes or bg_codes)))

        if direction == GradientDirection.AUTO:
            direction = GradientDirection.VERTICAL if multi else GradientDirection.HORIZONTAL

        if direction in (GradientDirection.HORIZONTAL, GradientDirection.HORIZONTAL_REVERSE):
            out_lines: list[str] = []
            for line in lines:
                chars = list(line)
                n = len(chars)
                m = len(fg_codes)

                if n == 0:
                    out_lines.append("")
                    continue

                codes = list(fg_codes)
                if direction == GradientDirection.HORIZONTAL_REVERSE:
                    codes.reverse()

                if n == 1:
                    code = f"38;5;{codes[0]}"
                    out_lines.append(cls.colorize(chars[0], fg=code, intensity=intensity, styles=styles))
                    continue

                out: list[str] = []
                for i, ch in enumerate(chars):
                    idx = int(i * (m - 1) / (n - 1))
                    # code = f"38;5;{codes[idx]}"
                    # out.append(cls.colorize(ch, fg=code, intensity=intensity, styles=styles))
                    fg = f"38;5;{fg_codes[idx]}" if fg_codes else None
                    bg = f"48;5;{bg_codes[idx]}" if bg_codes else None

                    out.append(cls.colorize(
                        ch,
                        fg=fg,
                        bg=bg,
                        intensity=intensity,
                        styles=styles,
                    ))
                out_lines.append("".join(out))

            return "\n".join(out_lines)

        if direction in (GradientDirection.VERTICAL, GradientDirection.VERTICAL_REVERSE):
            m = len(fg_codes)
            L = len(lines)

            codes = list(fg_codes)
            if direction == GradientDirection.VERTICAL_REVERSE:
                codes.reverse()

            out_lines: list[str] = []
            for i, line in enumerate(lines):
                idx = int(i * (m - 1) / (L - 1)) if L > 1 else 0
                code = f"38;5;{codes[idx]}"
                out_lines.append(cls.colorize(line, fg=code, intensity=intensity, styles=styles))

            return "\n".join(out_lines)

        return text

    @classmethod
    def reverse(cls, colored_text: str) -> str:
        """
        Flip FG and BG of an already-colored string.
        """

        if cls._NO_COLOR:
            return colored_text

        matches = cls._ANSI_RE.findall(colored_text)
        if not matches:
            return colored_text

        codes_raw: list[str] = []
        for m in matches:
            codes_raw.extend(m.split(";"))

        fg: Code | None = None
        bg: Code | None = None
        others: list[Code] = []

        for c in codes_raw:
            if c.startswith("38;5"):
                fg = c
            elif c.startswith("48;5"):
                bg = c
            elif c.isdigit():
                num = int(c)
                if 30 <= num <= 37 or 90 <= num <= 97:
                    fg = num
                elif 40 <= num <= 47 or 100 <= num <= 107:
                    bg = num
                else:
                    others.append(num)
            else:
                others.append(c)

        new_fg = bg
        new_bg = fg

        new_codes: list[Code] = []
        if new_fg is not None:
            new_codes.append(new_fg)
        if new_bg is not None:
            new_codes.append(new_bg)
        new_codes.extend(others)

        prefix = cls._join_codes(new_codes)
        stripped = cls._ANSI_RE.sub("", colored_text)
        return f"{prefix}{stripped}{cls._RESET}"

    @classmethod
    def strip_ansi(cls, text: str) -> str:
        return cls._ANSI_RE.sub("", text)

    @staticmethod
    def escape_ansi_for_display(text: str) -> str:
        """
        Escape only ANSI color/style sequences in the given string so they appear as
        literal text, while leaving all other control sequences untouched.

        This function targets:
        - foreground color codes
        - background color codes
        - bold / italic / underline
        - reset codes

        It does *not* escape:
        - cursor movement
        - erase screen / erase line commands
        - OSC sequences
        - other non-color control sequences

        Use this when:
        - you want to display ANSI color codes literally for debugging or documentation
        - you want to preserve the behavior of non-color control sequences
        - you only need to neutralize color styling, not full terminal control

        Returns:
            A string where ANSI color/style codes are escaped, but other control
            sequences remain functional.
        """
        result = []
        for ch in text:
            if ch == "\x1b":  # ESC byte
                result.append("\\x1b")
            else:
                result.append(ch)
        return "".join(result)

    @staticmethod
    def escape_control_chars(text: str) -> str:
        """
        Escape *all* ANSI control sequences in the given string so they become visible
        literal text instead of being interpreted by the terminal.

        This function neutralizes every form of terminal control sequence, including:
        - color and style codes (e.g., "\x1b[31m")
        - background colors
        - cursor movement (e.g., "\x1b[2A", "\x1b[5C")
        - erase screen / erase line commands (e.g., "\x1b[2J")
        - OSC sequences (e.g., terminal title changes)
        - BEL / control characters
        - any escape sequence beginning with ESC (0x1B)

        Use this when:
        - logging untrusted input that may contain terminal control codes
        - debugging raw ANSI output
        - preventing terminal injection attacks
        - showing escape sequences literally in logs or documentation

        Returns:
            A string where all ANSI control sequences are escaped (e.g., "\x1b" → "\\x1b"),
            ensuring the terminal displays them as plain text.
        """
        out = []
        for ch in text:
            if ord(ch) < 32 or ord(ch) == 127:
                out.append(f"\\x{ord(ch):02x}")
            else:
                out.append(ch)
        return "".join(out)


class GradientPalette:
    """
    Named 256‑color palette indices for gradients.
    These map directly to 38;5;X and 48;5;X.
    """

    # Basic colors
    BLACK = 16
    RED = 196
    ORANGE = 208
    YELLOW = 226
    GREEN = 46
    CYAN = 51
    BLUE = 21
    PURPLE = 93
    MAGENTA = 201
    WHITE = 255

    # Blues (smooth ramp)
    DEEP_BLUE = 18
    BLUE_1 = 19
    BLUE_2 = 20
    BLUE_3 = 21
    BLUE_4 = 27
    BLUE_5 = 33
    BLUE_6 = 39
    BLUE_7 = 45
    BLUE_8 = 51

    # Greyscale ramp
    GREY_0 = 232
    GREY_1 = 235
    GREY_2 = 239
    GREY_3 = 244
    GREY_4 = 250

    # Reds (smooth ramp)
    DARK_RED = 52
    RED_2 = 88
    RED_3 = 124
    RED_4 = 160
    BRIGHT_RED = 196

    # Classic rainbow
    RAINBOW = [196, 208, 226, 46, 21, 93]

    # Smooth sunset
    SUNSET = [196, 202, 208, 214, 220, 226]

    # Ocean blue
    OCEAN = [18, 19, 20, 21, 27, 33, 39, 45, 51]

    # Fire (deep red → bright yellow)
    FIRE = [52, 88, 124, 160, 196, 202, 226]

    # Ice (blue → cyan → white)
    ICE = [21, 27, 33, 39, 51, 87, 231]

    # Greyscale ramp
    GREYSCALE = [232, 235, 239, 244, 250, 255]

    # Forest (greens)
    FOREST = [22, 28, 34, 40, 46, 82, 118]

    # Neon (bright cyberpunk)
    NEON = [201, 93, 51, 87, 123, 159, 195]

    # Pastel (soft tones)
    PASTEL = [224, 225, 189, 151, 146, 182, 218]


def blend_palettes(p1: list[int], p2: list[int], *, steps: int | None = None) -> list[int]:
    """
    Blend two palettes by interpolating their indices.
    Produces a smooth transition from palette p1 to palette p2.

    Parameters
    ----------
    p1 : list[int]
        First palette (start)
    p2 : list[int]
        Second palette (end)
    steps : int | None
        Number of output colors. If None, uses max(len(p1), len(p2)).

    Returns
    -------
    list[int]
        A blended palette of xterm-256 indices.
    """

    if steps is None:
        steps = max(len(p1), len(p2))

    # Stretch both palettes to equal length
    def stretch(stops: list[int], target: int) -> list[int]:
        if len(stops) == target:
            return stops
        if len(stops) == 1:
            return stops * target
        out = []
        for i in range(target):
            idx = int(i * (len(stops) - 1) / (target - 1))
            out.append(stops[idx])
        return out

    p1s = stretch(p1, steps)
    p2s = stretch(p2, steps)

    # Linear interpolation in index space
    blended = []
    for a, b in zip(p1s, p2s):
        mid = int((a + b) / 2)
        blended.append(mid)

    return blended
