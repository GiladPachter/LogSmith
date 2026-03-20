import sys
import pytest
from LogSmith.colors import CPrint, GradientDirection, terminal_supports_color


# ============================================================
# 1. strip_ansi
# ============================================================

def test_strip_ansi_basic():
    text = "\x1b[31mRED\x1b[0m plain"
    out = CPrint.strip_ansi(text)
    assert out == "RED plain"


# ============================================================
# 2. escape_ansi_for_display
# ============================================================

def test_escape_ansi_for_display():
    text = "\x1b[31mRED\x1b[0m"
    out = CPrint.escape_ansi_for_display(text)
    assert "\\x1b" in out
    assert "RED" in out


# ============================================================
# 3. escape_control_chars
# ============================================================

def test_escape_control_chars():
    text = "A\x1b[31mB\x07C"
    out = CPrint.escape_control_chars(text)
    # ESC (0x1B) and BEL (0x07) must be escaped
    assert "\\x1b" in out
    assert "\\x07" in out
    assert "A" in out and "B" in out and "C" in out


# ============================================================
# 4. colorize() — fg, bg, intensity, styles
# ============================================================

def test_colorize_fg_bg_intensity_styles():
    out = CPrint.colorize(
        "X",
        fg=CPrint.FG.RED,
        bg=CPrint.BG.BLUE,
        intensity=CPrint.Intensity.BOLD,
        styles=[CPrint.Style.UNDERLINE],
    )
    assert "\x1b[" in out
    assert "31" in out or "38;" in out  # fg
    assert "44" in out or "48;" in out  # bg
    assert "1" in out  # bold
    assert "4" in out  # underline
    assert out.endswith("\x1b[0m")


# ============================================================
# 5. reverse() — 8‑color and 256‑color
# ============================================================

def test_reverse_basic_8color():
    colored = CPrint.colorize("X", fg=31, bg=44)
    rev = CPrint.reverse(colored)
    # fg and bg swapped
    assert "44" in rev or "48;" in rev
    assert "31" in rev or "38;" in rev


def test_reverse_256color():
    colored = CPrint.colorize("X", fg="38;5;200", bg="48;5;100")
    rev = CPrint.reverse(colored)

    # The reversed FG becomes "100" (bright background code interpreted as FG)
    assert "100" in rev
    # The reversed BG becomes "38;5;200"
    assert "38;5;200" in rev


def test_reverse_no_ansi():
    assert CPrint.reverse("plain") == "plain"


# ============================================================
# 6. terminal_supports_color() — monkeypatch
# ============================================================

def test_terminal_supports_color(monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert terminal_supports_color() is True


# ============================================================
# 7. gradient() — minimal branch coverage
# ============================================================

def test_gradient_horizontal():
    out = CPrint.gradient("ABC", fg_codes=[196, 46, 21],
                          direction=GradientDirection.HORIZONTAL)
    assert "\x1b[" in out
    assert "38;5;196" in out
    assert "38;5;46" in out
    assert "38;5;21" in out


def test_gradient_horizontal_reverse():
    out = CPrint.gradient("ABC", fg_codes=[196, 46, 21],
                          direction=GradientDirection.HORIZONTAL_REVERSE)
    # reversed order
    assert "38;5;21" in out.split("\n")[0]


def test_gradient_vertical():
    text = "A\nB\nC"
    out = CPrint.gradient(text, fg_codes=[196, 46, 21],
                          direction=GradientDirection.VERTICAL)
    assert "38;5;196" in out
    assert "38;5;46" in out
    assert "38;5;21" in out


def test_gradient_vertical_reverse():
    text = "A\nB\nC"
    out = CPrint.gradient(text, fg_codes=[196, 46, 21],
                          direction=GradientDirection.VERTICAL_REVERSE)
    # reversed order
    assert "38;5;21" in out.split("\n")[0]


def test_gradient_auto_single_line():
    out = CPrint.gradient("XYZ", fg_codes=[1, 2, 3],
                          direction=GradientDirection.AUTO)
    # AUTO + single line → horizontal
    assert "38;5;1" in out


def test_gradient_auto_multi_line():
    out = CPrint.gradient("A\nB", fg_codes=[1, 2],
                          direction=GradientDirection.AUTO)
    # AUTO + multi-line → vertical
    assert "38;5;1" in out.split("\n")[0]


def test_gradient_bg_only():
    out = CPrint.gradient("XYZ", fg_codes=[1, 2, 3],
                          bg_codes=[100, 101, 102],
                          direction=GradientDirection.HORIZONTAL)
    assert "48;5;100" in out
    assert "48;5;101" in out
    assert "48;5;102" in out


def test_gradient_empty_text():
    assert CPrint.gradient("", fg_codes=[1, 2]) == ""


def test_gradient_no_fg_codes():
    assert CPrint.gradient("ABC", fg_codes=None) == "ABC"
