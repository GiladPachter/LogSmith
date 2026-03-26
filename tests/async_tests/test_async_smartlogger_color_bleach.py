from LogSmith.async_smartlogger import AsyncSmartLogger


# Helper to call the private method
def bleach(text):
    return AsyncSmartLogger._AsyncSmartLogger__bleach_non_colored_text(text)


# ------------------------------------------------------------
# 1. Plain text (no ANSI)
# ------------------------------------------------------------
def test_bleach_plain_text():
    out = bleach("hello world")
    # Should recolor plain text with CONSOLE_DEFAULT
    assert "hello world" in out
    assert "\x1b[" in out  # recoloring applied


# ------------------------------------------------------------
# 2. Single ANSI sequence
# ------------------------------------------------------------
def test_bleach_single_ansi():
    text = "\x1b[31mRED\x1b[0m"
    out = bleach(text)
    # ANSI preserved
    assert "\x1b[31m" in out
    assert "RED" in out


# ------------------------------------------------------------
# 3. Mixed ANSI + plain
# ------------------------------------------------------------
def test_bleach_mixed():
    text = "plain \x1b[32mGREEN\x1b[0m plain2"
    out = bleach(text)

    # GREEN preserved
    assert "\x1b[32mGREEN\x1b[0m" in out

    # plain segments recolored
    assert "plain" in out
    assert "\x1b[" in out  # recoloring applied


# ------------------------------------------------------------
# 4. Adjacent ANSI sequences
# ------------------------------------------------------------
def test_bleach_adjacent_ansi():
    text = "\x1b[31mRED\x1b[0m\x1b[32mGREEN\x1b[0m"
    out = bleach(text)

    assert "\x1b[31mRED\x1b[0m" in out
    assert "\x1b[32mGREEN\x1b[0m" in out


# ------------------------------------------------------------
# 5. ANSI active at end of string
# ------------------------------------------------------------
def test_bleach_color_active_at_end():
    text = "\x1b[35mMAGENTA"
    out = bleach(text)

    # ANSI preserved
    assert "\x1b[35mMAGENTA" in out


# ------------------------------------------------------------
# 6. Plain text after reset
# ------------------------------------------------------------
def test_bleach_plain_after_reset():
    text = "\x1b[31mRED\x1b[0m then plain"
    out = bleach(text)

    assert "RED" in out
    assert "then plain" in out
    # plain recolored
    assert "\x1b[" in out


# ------------------------------------------------------------
# 7. Empty plain buffer (edge case)
# ------------------------------------------------------------
def test_bleach_empty_plain_buffer():
    text = "\x1b[31mR\x1b[0m"
    out = bleach(text)

    assert "R" in out
    assert "\x1b[31m" in out


# ------------------------------------------------------------
# 8. Multiple toggles of color_active
# ------------------------------------------------------------
def test_bleach_multiple_toggles():
    text = "A \x1b[31mB\x1b[0m C \x1b[32mD\x1b[0m E"
    out = bleach(text)

    assert "A" in out
    assert "B" in out
    assert "C" in out
    assert "D" in out
    assert "E" in out


# ------------------------------------------------------------
# 9. Whitespace-only plain segments
# ------------------------------------------------------------
def test_bleach_whitespace_plain():
    text = "   \x1b[31mRED\x1b[0m   "
    out = bleach(text)

    assert "RED" in out
    # whitespace preserved but not recolored
    assert out.startswith("   ")
    assert out.endswith("   ")
