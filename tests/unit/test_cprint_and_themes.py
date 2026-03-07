import re

from LogSmith import CPrint, SmartLogger, DARK_THEME, LevelStyle, GradientPalette

ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def test_cprint_colorize_adds_ansi_and_strip_removes():
    text = "Hello"
    colored = CPrint.colorize(text, fg=CPrint.FG.BRIGHT_GREEN, intensity=CPrint.Intensity.BOLD)
    assert text in colored
    assert ANSI_PATTERN.search(colored)

    stripped = CPrint.strip_ansi(colored)
    assert stripped == text


def test_cprint_gradient_length_preserved():
    text = "Rainbow!"
    grad = CPrint.gradient(text, fg_codes=GradientPalette.RAINBOW)
    stripped = CPrint.strip_ansi(grad)
    assert stripped == text


def test_apply_color_theme_changes_level_style(capsys):
    levels = SmartLogger.levels()
    logger = SmartLogger("theme.test", level=levels["TRACE"])

    SmartLogger.apply_color_theme(DARK_THEME)
    logger.add_console()
    logger.info("Dark theme activated!")

    out = capsys.readouterr().out
    # we don't assert specific codes, just that ANSI is present
    assert ANSI_PATTERN.search(out)


def test_custom_theme_for_dynamic_level(capsys):
    SmartLogger.register_level("NOTICE", NOTICE := 25)
    from LogSmith import CPrint as CP  # alias to avoid confusion

    MY_THEME = {
        NOTICE: LevelStyle(fg=CP.FG.BRIGHT_MAGENTA),
    }
    SmartLogger.apply_color_theme(MY_THEME)

    levels = SmartLogger.levels()
    logger = SmartLogger("theme.dynamic", level=levels["TRACE"])
    logger.add_console()

    logger.notice("Notice message")
    out = capsys.readouterr().out
    assert "Notice message" in out
    assert ANSI_PATTERN.search(out)
