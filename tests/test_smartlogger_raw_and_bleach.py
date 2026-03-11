import logging
from LogSmith import SmartLogger, CPrint
from LogSmith.formatter import PassthroughFormatter


def test_raw_output_and_bleaching(tmp_path):
    logger = SmartLogger("bleach", logging.INFO)
    logger.add_file(str(tmp_path), "b.log")

    colored = CPrint.colorize("HELLO", fg=CPrint.FG.RED)
    logger.raw(colored)

    text = (tmp_path / "b.log").read_text()
    assert "HELLO" in text
    assert "\x1b" not in text  # stripped

def test_passthrough_formatter(tmp_path):
    logger = SmartLogger("pass", logging.INFO)
    logger.add_file(str(tmp_path), "p.log", do_not_sanitize_colors_from_string=True)

    colored = CPrint.colorize("HELLO", fg=CPrint.FG.GREEN)
    logger.raw(colored)

    text = (tmp_path / "p.log").read_text()
    assert "\x1b" in text  # ANSI preserved
