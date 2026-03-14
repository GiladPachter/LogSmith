import pytest

from LogSmith import SmartLogger


def test_smartlogger_rejects_non_normalized_path(tmp_path):
    log = SmartLogger("x")

    bad = str(tmp_path) + "/../" + tmp_path.name
    with pytest.raises(ValueError):
        log.add_file(bad, "x.log")
