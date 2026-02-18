# smartlogger/rotation.py

import errno
import os
import time
import logging
from dataclasses import dataclass
from enum import Enum
from logging.handlers import BaseRotatingHandler
from datetime import datetime, timedelta
from typing import Optional, IO

try:
    import fcntl  # type: ignore[attr-defined]
    _HAS_FCNTL = True
except ImportError:  # Windows
    fcntl = None
    _HAS_FCNTL = False

try:
    import msvcrt  # type: ignore[attr-defined]
    _HAS_MSVCRT = True
except ImportError:
    msvcrt = None
    _HAS_MSVCRT = False


class When(Enum):
    """
    Time-based rotation granularity.
    """
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"
    EVERYDAY = "everyday"


@dataclass
class RotationTimestamp:
    """
    Time-of-day for time-based rotation.
    """
    hour: int = 0
    minute: int = 0
    second: int = 0

    def to_seconds(self) -> int:
        return self.hour * 3600 + self.minute * 60 + self.second


class ExpirationScale(Enum):
    Seconds = "S"
    Minutes = "M"
    Hours = "H"
    Days = "D"
    MonthDay = "MD"


@dataclass
class ExpirationRule:
    scale: ExpirationScale
    interval: int  # ignored if scale == ExpirationScale.MonthDay


class RotationLogic:
    """
    Describes how log file rotation and retention should behave, and produces a
    ConcurrentTimedSizedRotatingFileHandler accordingly.

    RotationLogic supports three independent concerns:

    1. Size-based rotation
       Triggered when the active log file exceeds `maxBytes`.

    2. Time-based rotation
       Triggered according to:
           - When.SECOND, When.MINUTE, When.HOUR
             (simple periodic rotation)
           - When.MONDAY ... When.SUNDAY
             (weekly rotation at a specific time-of-day)
           - When.EVERYDAY
             (daily rotation at a specific time-of-day)

       The `interval` parameter controls the period for SECOND/MINUTE/HOUR.
       The `timestamp` parameter defines the time-of-day anchor for DAILY/WEEKLY.

    3. Retention (expiration)
       Controlled by `expiration_rule`. This determines when *old rotated files*
       should be deleted, independent of rotation triggers.

    Rotation triggers are implicitly combined:
        - If only `maxBytes` is set → size-based rotation.
        - If only `when` is set → time-based rotation.
        - If both are set → rotation occurs when *either* condition is met.

    All rotation logic is handled by ConcurrentTimedSizedRotatingFileHandler,
    which provides concurrency-safe, cross-process-safe rollover and atomic
    renames.

    Parameters
    ----------
    when : When | None
        Time-based rotation mode. If None, no time-based rotation is used.

    interval : int | None
        Interval for SECOND/MINUTE/HOUR rotation. Ignored for DAILY/WEEKLY.

    timestamp : RotationTimestamp | None
        Time-of-day anchor for DAILY/WEEKLY rotation. Defaults to 00:00:00.

    maxBytes : int | None
        Enables size-based rotation when set to a positive value.

    backupCount : int
        Number of rotated files to retain (count-based retention).

    expiration_rule : ExpirationRule | None
        Optional time-based retention policy for deleting old rotated files.

    append_filename_timestamp : bool
        If True, inserts a timestamp into the base filename before rotation
        logic is applied.
    """

    def __init__(
            self,
            when:                      When | None              = None,
            interval:                  int | None               = None,
            timestamp:                 RotationTimestamp | None = None,
            maxBytes:                  int | None               = None,
            backupCount:               int                      = 5,
            expiration_rule:           ExpirationRule | None    = None,
            append_filename_pid:       bool                     = False,
            append_filename_timestamp: bool                     = False,
    ):
        if interval is not None and interval < 0:
            raise ValueError("Negative interval is illegal")

        if maxBytes is not None and maxBytes < 0:
            raise ValueError("Negative maxBytes is illegal")

        if backupCount < 0:
            raise ValueError("Negative backupCount is illegal")

        self.when = when
        self.interval                  = interval
        self.timestamp                 = timestamp
        self.maxBytes                  = maxBytes
        self.backupCount               = backupCount
        self.expiration_rule           = expiration_rule
        self.append_filename_pid       = append_filename_pid
        self.append_filename_timestamp = append_filename_timestamp

    def _apply_timestamp_suffix(self, file_path: str) -> str:
        """
        Insert a timestamp before the file extension.
        Example:
            "logs/app.log" → "logs/app_20240210_2130.log"
        """
        if not self.append_filename_timestamp:
            return file_path

        import datetime, os

        base, ext = os.path.splitext(file_path)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base}_{stamp}{ext}"

    def _apply_pid_suffix(self, file_path: str) -> str:
        if not self.append_filename_pid:
            return file_path

        import os
        pid = os.getpid()

        base, ext = os.path.splitext(file_path)
        return f"{base}.{pid}{ext}"

    def create_handler(self, file_path: str) -> logging.Handler:
        # Apply timestamp/pid if requested
        file_path = self._apply_pid_suffix(file_path)
        file_path = self._apply_timestamp_suffix(file_path)

        # If any rotation is requested → use our custom handler
        if self.maxBytes is not None or self.when is not None:
            return ConcurrentTimedSizedRotatingFileHandler(
                filename=file_path,
                when=self.when,
                interval=self.interval or 1,
                timestamp=self.timestamp,
                max_bytes=self.maxBytes or 0,
                backup_count=self.backupCount,
                expiration_rule=self.expiration_rule,
                encoding="utf-8",
            )

        # No rotation → plain file handler
        return logging.FileHandler(file_path, encoding="utf-8")


class ConcurrentTimedSizedRotatingFileHandler (BaseRotatingHandler):
    """
    ConcurrentTimedSizedRotatingFileHandler

    - Extends BaseRotatingHandler
    - Supports:
        * size-based rotation (max_bytes)
        * time-based rotation (When + interval + Timestamp)
        * concurrent, cross-process safe rotation using OS-level locks
        * atomic renames
        * backup file management

    Filename scheme:
        base.log
        base.log.1
        base.log.2
        ...
    """

    def __init__(
        self,
        filename: str,
        *,
        when:            Optional[When] = None,
        interval:        int = 1,
        timestamp:       Optional[RotationTimestamp] = None,
        max_bytes:       int = 0,
        backup_count:    int = 7,
        expiration_rule: ExpirationRule | None = None,
        encoding: Optional[str] = "utf-8",
    ):
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

        # BaseRotatingHandler -> FileHandler
        BaseRotatingHandler.__init__(self, filename, mode="a", encoding=encoding, delay=False)

        # Tell PyCharm the truth: stream can be None
        self.stream: Optional[IO[str]] = self.stream

        self.when            = when
        self.interval        = max(1, interval)
        self.timestamp       = timestamp
        self.max_bytes       = max_bytes
        self.backupCount     = backup_count
        self.expiration_rule = expiration_rule

        # lock file for cross-process safety
        self._lock_file = None
        self._lock_file_path = self.baseFilename + ".lock"

        # time-based rollover scheduling
        self._rollover_at: Optional[float] = None
        if self.when is not None:
            self._rollover_at = self._compute_initial_rollover()

            # noinspection PyBroadException
            try:
                if os.path.exists(self.baseFilename):
                    file_modify_time = os.path.getmtime(self.baseFilename)

                    # If the file is older than the last scheduled rollover moment,
                    # force rollover immediately.
                    if file_modify_time < (self._rollover_at - self._rollover_interval_seconds()):
                        # Force rollover on first emit
                        self._rollover_at = 0
            except Exception:
                pass

    def _rollover_interval_seconds(self) -> float:
        if self.when == When.SECOND:
            return self.interval
        if self.when == When.MINUTE:
            return self.interval * 60
        if self.when == When.HOUR:
            return self.interval * 3600
        if self.when == When.EVERYDAY:
            return 24 * 3600
        # weekly
        return 7 * 24 * 3600

    # ------------------------------------------------------------------
    # LOCKING
    # ------------------------------------------------------------------

    def _open_lock_file(self) -> None:
        if self._lock_file is None:
            self._lock_file = open(self._lock_file_path, "a+b")

    def _acquire_lock(self) -> None:
        self._open_lock_file()
        f = self._lock_file

        if _HAS_FCNTL:
            while True:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    break
                except OSError as e:
                    if e.errno != errno.EINTR:
                        raise
        elif _HAS_MSVCRT:
            # lock 1 byte; enough to serialize access
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        else:
            # no-op fallback (not ideal, but keeps API usable)
            pass

    def _release_lock(self) -> None:
        if self._lock_file is None:
            return
        f = self._lock_file

        if _HAS_FCNTL:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        elif _HAS_MSVCRT:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            pass

    # ------------------------------------------------------------------
    # TIME-BASED ROLLOVER CALCULATION
    # ------------------------------------------------------------------

    def _compute_initial_rollover(self) -> float:
        now = time.time()
        return self._compute_next_rollover(now)

    def _compute_next_rollover(self, current: float) -> float:
        """
        Compute the next rollover time after 'current' (epoch seconds),
        based on When + interval + Timestamp.
        """
        if self.when is None:
            return float("inf")

        # simple periodic rotation
        if self.when in (When.SECOND, When.MINUTE, When.HOUR):
            if self.when == When.SECOND:
                delta = self.interval
            elif self.when == When.MINUTE:
                delta = self.interval * 60
            else:  # HOUR
                delta = self.interval * 3600
            return current + delta

        # daily / weekly rotation at a specific time-of-day
        ts = self.timestamp or RotationTimestamp(hour=0, minute=0, second=0)

        now_dt = datetime.fromtimestamp(current)
        target = now_dt.replace(
            hour=ts.hour,
            minute=ts.minute,
            second=ts.second,
            microsecond=0,
        )

        if self.when == When.EVERYDAY:
            if target <= now_dt:
                target = target + timedelta(days=1)
            return target.timestamp()

        # weekday-based: Monday=0 ... Sunday=6
        weekday_map = {
            When.MONDAY: 0,
            When.TUESDAY: 1,
            When.WEDNESDAY: 2,
            When.THURSDAY: 3,
            When.FRIDAY: 4,
            When.SATURDAY: 5,
            When.SUNDAY: 6,
        }
        target_weekday = weekday_map[self.when]
        days_ahead = (target_weekday - now_dt.weekday()) % 7
        if days_ahead == 0 and target <= now_dt:
            days_ahead = 7
        target = target + timedelta(days=days_ahead)
        return target.timestamp()

    # ------------------------------------------------------------------
    # ROLLOVER DECISION
    # ------------------------------------------------------------------

    def shouldRollover(self, record: logging.LogRecord) -> bool:
        """
        Decide if rollover should occur (size and/or time).
        """
        if self.stream is None:
            self.stream = self._open()

        # size-based
        if self.max_bytes > 0:
            msg = f"{self.format(record)}\n"
            self.stream.seek(0, os.SEEK_END)
            current_size = self.stream.tell()
            projected = current_size + len(msg.encode(self.encoding or "utf-8"))
            if projected >= self.max_bytes:
                return True

        # time-based
        if self._rollover_at is not None:
            now = time.time()
            if now >= self._rollover_at:
                return True

        return False

    # ------------------------------------------------------------------
    # EMIT WITH CONCURRENCY
    # ------------------------------------------------------------------

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record with concurrency-safe rollover.
        """
        try:
            self._acquire_lock()

            # emit only records that are to be actually logged
            if not self.filter(record):
                return

            if self.shouldRollover(record):
                self._doRollover()
                self._apply_expiration_policy()
            # BaseRotatingHandler inherits FileHandler; use its emit
            logging.FileHandler.emit(self, record)
        finally:
            self._release_lock()

    # ------------------------------------------------------------------
    # ROLLOVER IMPLEMENTATION
    # ------------------------------------------------------------------

    def _doRollover(self) -> None:
        """
        Perform rollover:
            - close current file
            - rotate backups
            - reopen base file
            - compute next rollover time
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        # rotate backups
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = f"{self.baseFilename}.{i}"
                dfn = f"{self.baseFilename}.{i + 1}"
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.replace(sfn, dfn)

            dfn = f"{self.baseFilename}.1"
            if os.path.exists(dfn):
                os.remove(dfn)
            if os.path.exists(self.baseFilename):
                os.replace(self.baseFilename, dfn)

        # reopen base file
        self.stream = self._open()

        # compute next rollover time
        if self.when is not None:
            now = time.time()
            self._rollover_at = self._compute_next_rollover(now)
        else:
            self._rollover_at = None

    def _apply_expiration_policy(self):
        rule = self.expiration_rule
        if rule is None:
            return

        now = datetime.now()

        # Compute cutoff time
        if rule.scale == ExpirationScale.Seconds:
            cutoff = now - timedelta(seconds=rule.interval)
        elif rule.scale == ExpirationScale.Minutes:
            cutoff = now - timedelta(minutes=rule.interval)
        elif rule.scale == ExpirationScale.Hours:
            cutoff = now - timedelta(hours=rule.interval)
        elif rule.scale == ExpirationScale.Days:
            cutoff = now - timedelta(days=rule.interval)
        elif rule.scale == ExpirationScale.MonthDay:
            # Delete files from previous calendar days
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return

        # Delete rotated files older than cutoff
        for path in self._list_rotated_files():
            if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
                try:
                    os.remove(path)
                except OSError:
                    pass

    def _list_rotated_files(self):
        base = self.baseFilename
        dir_name = os.path.dirname(base)
        prefix = os.path.basename(base)

        return [
            os.path.join(dir_name, f)
            for f in os.listdir(dir_name)
            if f.startswith(prefix)
        ]
