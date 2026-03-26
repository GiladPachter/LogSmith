import os
import time
from pathlib import Path
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import ExpirationRule, ExpirationScale


def test_expiration_seconds(tmp_path):
    base = Path(tmp_path) / "exp.log"

    # Create rotated files
    old = tmp_path / "exp.log.1"
    new = tmp_path / "exp.log.2"

    old.write_text("old")
    new.write_text("new")

    # Make one file old enough to expire
    old_mtime = time.time() - 10
    os.utime(old, (old_mtime, old_mtime))

    # New file is fresh
    new_mtime = time.time()
    os.utime(new, (new_mtime, new_mtime))

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        expiration_rule=ExpirationRule(ExpirationScale.Seconds, interval=5),
    )

    # Trigger expiration
    # noinspection PyUnresolvedReferences
    handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    # Old file should be deleted
    assert not old.exists()
    # New file should remain
    assert new.exists()


def test_expiration_days(tmp_path):
    base = Path(tmp_path) / "exp2.log"

    f1 = tmp_path / "exp2.log.1"
    f2 = tmp_path / "exp2.log.2"

    f1.write_text("old")
    f2.write_text("new")

    # f1 is 3 days old
    old_mtime = time.time() - (3 * 24 * 3600)
    os.utime(f1, (old_mtime, old_mtime))

    # f2 is fresh
    new_mtime = time.time()
    os.utime(f2, (new_mtime, new_mtime))

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        expiration_rule=ExpirationRule(ExpirationScale.Days, interval=2),
    )

    # noinspection PyUnresolvedReferences
    handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    assert not f1.exists()
    assert f2.exists()


from datetime import datetime

def test_expiration_monthday(tmp_path):
    base = Path(tmp_path) / "exp3.log"

    f1 = tmp_path / "exp3.log.1"
    f2 = tmp_path / "exp3.log.2"

    f1.write_text("yesterday")
    f2.write_text("today")

    # f1 is yesterday
    yesterday = datetime.now().timestamp() - 86400
    os.utime(f1, (yesterday, yesterday))

    # f2 is today
    today = datetime.now().timestamp()
    os.utime(f2, (today, today))

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        expiration_rule=ExpirationRule(ExpirationScale.MonthDay, interval=0),
    )

    # noinspection PyUnresolvedReferences
    handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    assert not f1.exists()
    assert f2.exists()


