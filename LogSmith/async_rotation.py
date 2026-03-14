# LogSmith/async_rotation.py

from __future__ import annotations

import os
import threading
import time
import logging
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Callable, IO

from .rotation_base import (
    When,
    RotationTimestamp,
    ExpirationScale,
    BaseTimedSizedRotatingFileHandler,
    ExpirationRule,
    LargeLogEntryBehavior
)


class Async_TimedSizedRotatingFileHandler(BaseTimedSizedRotatingFileHandler):
    """
    Async_TimedSizedRotatingFileHandler
    ===================================
    A baseline clone of ConcurrentTimedSizedRotatingFileHandler,
    adapted for async rotation scheduling.

    Key differences:
    • Rotation is NOT performed inside emit()
    • Instead, emit() calls rotation_callback(self)
    • rotation_callback is injected by AsyncSmartLogger.add_file()
    • perform_rotation() is executed by AsyncSmartLogger's worker thread
    """

    rotation_callback: Optional[Callable[[Async_TimedSizedRotatingFileHandler], None]] = None

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
            delay: bool = False,
    ) -> None:

        # Initialize the base class (FileHandler + parameter storage)
        super().__init__(
            filename,
            when=when,
            interval=interval,
            timestamp=timestamp,
            max_bytes=max_bytes,
            backup_count=backup_count,
            expiration_rule=expiration_rule,
            encoding=encoding,
            large_entry_behavior=large_entry_behavior,
            delay=delay,
        )

        self._last_rotation_check = 0.0

        # Tell PyCharm the truth: stream can be None
        self.stream: Optional[IO[str]] = self.stream

        # For debugging / introspection
        self.resolved_path = str(Path(self.baseFilename).resolve())

        self._rotation_scheduled = False

        self.write_lock = threading.Lock()

        self._rollover_at = None
        if self.when is not None:
            self._rollover_at = self._compute_initial_rollover()

    # ------------------------------------------------------------------
    #  EMIT (detect rotation, schedule async rotation)
    # ------------------------------------------------------------------
    class AsyncLargeEntryDecision(Enum):
        WRITE = auto()  # write normally
        DROP = auto()  # drop entry entirely
        ROTATE_THEN_WRITE = auto()  # schedule rotation, then write

    def _async_large_entry_decision(self, formatted: str) -> AsyncLargeEntryDecision:
        leb = self.large_entry_behavior
        if leb is None:
            return self.AsyncLargeEntryDecision.WRITE

        entry_size = len(formatted.encode(self.encoding or "utf-8"))
        if self.max_bytes <= 0 or entry_size < self.max_bytes:
            return self.AsyncLargeEntryDecision.WRITE

        # DROP
        if leb is LargeLogEntryBehavior.DumpSilently:
            return self.AsyncLargeEntryDecision.DROP

        # CRASH
        if leb is LargeLogEntryBehavior.Crash:
            raise ValueError(
                f"Log entry of size {entry_size} exceeds max_bytes={self.max_bytes}"
            )

        # ROTATE FIRST
        if leb is LargeLogEntryBehavior.RotateFirst:
            return self.AsyncLargeEntryDecision.ROTATE_THEN_WRITE

        # EXCEED_IF_EMPTY
        if leb is LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty:
            self.stream.seek(0, os.SEEK_END)
            if self.stream.tell() == 0:
                return self.AsyncLargeEntryDecision.WRITE
            return self.AsyncLargeEntryDecision.ROTATE_THEN_WRITE

        return self.AsyncLargeEntryDecision.WRITE

    def emit(self, record):
        # Ensure stream open
        if self.stream is None or getattr(self.stream, "closed", False):
            try:
                self.acquire()
                self.stream = self._open()
            finally:
                self.release()

        now = time.time()

        # 1. Size-based rotation BEFORE writing
        if self.max_bytes and self.should_rotate(record):
            if self.rotation_callback and not self._rotation_scheduled:
                self._rotation_scheduled = True
                self.rotation_callback(self)

        # 2. Large-entry behavior (async-safe)
        formatted = self.format(record)
        decision = self._async_large_entry_decision(formatted)

        if decision is self.AsyncLargeEntryDecision.DROP:
            return

        if decision is self.AsyncLargeEntryDecision.ROTATE_THEN_WRITE:
            if self.rotation_callback and not self._rotation_scheduled:
                self._rotation_scheduled = True
                self.rotation_callback(self)

        # 3. Write normally (no synchronous rotation)
        logging.FileHandler.emit(self, record)

        # 4. Time-based rotation (throttled)
        if self.when is not None:
            if now - self._last_rotation_check >= 0.25:
                self._last_rotation_check = now
                if self.should_rotate(record):
                    if self.rotation_callback and not self._rotation_scheduled:
                        self._rotation_scheduled = True
                        self.rotation_callback(self)

    # ------------------------------------------------------------------
    #  PERFORM ROTATION (executed by AsyncSmartLogger worker)
    # ------------------------------------------------------------------
    def perform_rotation(self) -> None:
        """
        Executed inside AsyncSmartLogger's worker thread.
        Mirrors ConcurrentTimedSizedRotatingFileHandler._doRollover().
        """
        self.acquire()
        try:
            # Close current file
            if self.stream:
                self.stream.close()
                self.stream = None  # type: ignore[assignment]

            # Rotate backups
            if self.backup_count > 0:
                for i in range(self.backup_count - 1, 0, -1):
                    sfn = f"{self.baseFilename}.{i}"
                    dfn = f"{self.baseFilename}.{i + 1}"
                    if os.path.exists(sfn):
                        if os.path.exists(dfn):
                            os.remove(dfn)
                        orig_mtime = os.path.getmtime(sfn)
                        os.replace(sfn, dfn)
                        os.utime(dfn, (orig_mtime, orig_mtime))

                dfn = f"{self.baseFilename}.1"
                if os.path.exists(dfn):
                    os.remove(dfn)
                if os.path.exists(self.baseFilename):
                    os.replace(self.baseFilename, dfn)

            # Reopen base file
            self.stream = self._open()

            # Compute next rollover time
            if self.when is not None:
                now = time.time()
                self._rollover_at = self._compute_next_rollover(now)
            else:
                self._rollover_at = None

            # Apply retention
            self._apply_expiration_policy()

        finally:
            self.release()
            self._rotation_scheduled = False

    def should_rotate(self, record: logging.LogRecord) -> bool:
        """
        Async equivalent of ConcurrentTimedSizedRotatingFileHandler.shouldRollover().
        Decides if rotation should occur (size and/or time).
        """
        # Ensure file is open
        if self.stream is None:
            self.stream = self._open()

        # ----------------------------------------------------------
        # SIZE-BASED ROTATION
        # ----------------------------------------------------------
        if self.max_bytes and self.max_bytes > 0:
            msg = f"{self.format(record)}\n"
            self.stream.seek(0, os.SEEK_END)
            current_size = self.stream.tell()
            projected = current_size + len(msg.encode(self.encoding or "utf-8"))
            if projected >= self.max_bytes:
                return True

        # ----------------------------------------------------------
        # TIME-BASED ROTATION
        # ----------------------------------------------------------
        if self._rollover_at is not None:
            now = time.time()
            if now >= self._rollover_at:
                return True

        return False

    def _rollover_interval_seconds(self) -> float:
        if self.when == When.SECOND:
            return self.interval
        if self.when == When.MINUTE:
            return self.interval * 60
        if self.when == When.HOUR:
            return self.interval * 3600
        if self.when == When.EVERYDAY:
            return 24 * 3600
        return 7 * 24 * 3600  # weekly

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

    def _apply_expiration_policy(self) -> None:
        rule = self.expiration_rule
        if rule is None:
            return  # pragma: no cover

        now = datetime.now()

        if rule.scale == ExpirationScale.Seconds:
            cutoff = now - timedelta(seconds=rule.interval)
        elif rule.scale == ExpirationScale.Minutes:
            cutoff = now - timedelta(minutes=rule.interval)
        elif rule.scale == ExpirationScale.Hours:
            cutoff = now - timedelta(hours=rule.interval)
        elif rule.scale == ExpirationScale.Days:
            cutoff = now - timedelta(days=rule.interval)
        elif rule.scale == ExpirationScale.MonthDay:
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return  # pragma: no cover

        for path in self._list_rotated_files():
            try:
                if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
                    os.remove(path)
            except OSError:
                pass    # pragma: no cover

    def _list_rotated_files(self) -> list[str]:
        base = self.baseFilename
        dir_name = os.path.dirname(base)
        prefix = os.path.basename(base)

        return [
            os.path.join(dir_name, f)
            for f in os.listdir(dir_name)
            if f.startswith(prefix)
               and not f.endswith(".lock")
        ]
