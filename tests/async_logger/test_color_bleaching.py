import pytest

from LogSmith import SmartLogger
from LogSmith import AsyncSmartLogger
from LogSmith.colors import CPrint


def bleach(text: str) -> str:
    """Convenience wrapper for calling the private bleaching method."""
    # noinspection PyProtectedMember
    return SmartLogger._SmartLogger__bleach_non_colored_text(text)


def a_bleach(text: str) -> str:
    """Convenience wrapper for calling the private bleaching method."""
    # noinspection PyProtectedMember
    return AsyncSmartLogger._AsyncSmartLogger__bleach_non_colored_text(text)


def test_bleach_plain_text_only():
    """
    Plain text should be recolored using the default console color.
    """
    out = bleach("hello world")
    out2 = a_bleach("hello world 2")
    assert "hello world" in out
    assert "hello world 2" in out2
    assert CPrint.FG.CONSOLE_DEFAULT in out


def test_bleach_colored_text_only():
    """
    Colored text should be preserved exactly as-is.
    """
    colored = "\x1b[31mred\x1b[0m"
    out = bleach(colored)
    assert out == colored


def test_bleach_mixed_colored_and_plain():
    """
    Mixed text should preserve colored segments and recolor plain segments.
    """
    text = "plain " + "\x1b[32mgreen\x1b[0m" + " tail"
    out = bleach(text)

    # Colored segment preserved
    assert "\x1b[32mgreen\x1b[0m" in out

    # Plain segments recolored
    assert CPrint.FG.CONSOLE_DEFAULT in out
    assert "plain" in out
    assert "tail" in out


def test_bleach_trailing_plain_text():
    """
    Trailing plain text after a colored segment should be recolored.
    """
    text = "\x1b[34mblue\x1b[0m end"
    out = bleach(text)

    assert "\x1b[34mblue\x1b[0m" in out
    assert "end" in out
    assert CPrint.FG.CONSOLE_DEFAULT in out


def test_bleach_multiple_color_segments():
    """
    Multiple colored segments should all be preserved, with plain text recolored.
    """
    text = (
        "start "
        "\x1b[31mred\x1b[0m"
        " mid "
        "\x1b[32mgreen\x1b[0m"
        " end"
    )

    out = bleach(text)

    assert "\x1b[31mred\x1b[0m" in out
    assert "\x1b[32mgreen\x1b[0m" in out
    assert CPrint.FG.CONSOLE_DEFAULT in out
    assert "start" in out
    assert "mid" in out
    assert "end" in out
