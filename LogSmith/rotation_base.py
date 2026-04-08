# LogSmith/rotation_base.py  (new file)

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum, auto
from logging import FileHandler
from logging.handlers import BaseRotatingHandler
from typing import Optional


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


class LargeLogEntryBehavior(Enum):
    ExceedMaxBytesIfFileIsEmpty = auto()   # default
    RotateFirst                 = auto()   # might lead to an empty log file
    DumpSilently                = auto()   # log entry is lost (unpredictable loss)
    Crash                       = auto()   # force user to adjust maxBytes (but timing is unpredictable)


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
            when:                                    When | None                  = None,
            interval:                                int | None                   = None,
            timestamp:                               RotationTimestamp | None     = None,
            maxBytes:                                int | None                   = None,
            backupCount:                             int                          = 5,
            expiration_rule:                         ExpirationRule | None        = None,
            # =====================================
            log_entry_larger_than_maxBytes_behavior: LargeLogEntryBehavior | None = None,
            # =====================================
            append_filename_pid:                     bool                         = False,
            append_filename_timestamp:               bool                         = False,
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

        self.large_entry_behavior      = (log_entry_larger_than_maxBytes_behavior
                                          or LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty
                                          )

        self.append_filename_pid       = append_filename_pid
        self.append_filename_timestamp = append_filename_timestamp


class BaseTimedSizedRotatingFileHandler(ABC, BaseRotatingHandler):
    """
    Abstract base class for both synchronous and asynchronous rotating handlers.
    This class does NOT implement rotation or writing logic.
    It only unifies constructor signature and large-entry behavior.
    """

    def __init__(
        self,
        filename: str,
        *,
        when: Optional[When] = None,
        interval: int = 1,
        timestamp: Optional[RotationTimestamp] = None,
        max_bytes: int = 0,
        backup_count: int = 7,
        expiration_rule: Optional[ExpirationRule] = None,
        encoding: Optional[str] = "utf-8",
        large_entry_behavior: Optional[LargeLogEntryBehavior] = None,
        append_filename_pid: bool = False,
        append_filename_timestamp: bool = False,
    ) -> None:

        FileHandler.__init__(self, filename, mode="a", encoding=encoding)

        # Store rotation parameters
        self.when = when
        self.interval = interval
        self.timestamp = timestamp
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.expiration_rule = expiration_rule
        self.large_entry_behavior = large_entry_behavior
        self.append_filename_pid = append_filename_pid
        self.append_filename_timestamp = append_filename_timestamp
