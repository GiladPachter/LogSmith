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
            append_filename_pid: bool = False,
            append_filename_timestamp: bool = False,
            audit_mode: bool = False
    ) -> None:

        # Initialize the base class (FileHandler + parameter storage)
        super().__init__(
            filename,
            when = when,
            interval = interval,
            timestamp = timestamp,
            max_bytes = max_bytes,
            backup_count = backup_count,
            expiration_rule = expiration_rule,
            encoding = encoding,
            large_entry_behavior = large_entry_behavior,
            append_filename_pid = append_filename_pid,
            append_filename_timestamp = append_filename_timestamp,
        )
        self.audit_mode = audit_mode

        self.__last_rotation_check = 0.0

        # Tell PyCharm the truth: stream can be None
        self.stream: Optional[IO[str]] = self.stream

        # For debugging / introspection
        self.resolved_path = str(Path(self.baseFilename).resolve())

        self.__rotation_scheduled = False

        self.write_lock = threading.Lock()

        self.__rollover_at = None
        if self.when is not None:
            self.__rollover_at = self.__compute_initial_rollover()

    # ------------------------------------------------------------------
    #  EMIT (detect rotation, schedule async rotation)
    # ------------------------------------------------------------------
    class __AsyncLargeEntryDecision(Enum):
        WRITE = auto()  # write normally
        DROP = auto()  # drop entry entirely
        ROTATE_THEN_WRITE = auto()  # schedule rotation, then write

    def __async_large_entry_decision(self, formatted: str) -> __AsyncLargeEntryDecision:
        leb = self.large_entry_behavior
        if leb is None:
            return self.__AsyncLargeEntryDecision.WRITE

        entry_size = len(formatted.encode(self.encoding or "utf-8"))
        if self.max_bytes <= 0 or entry_size < self.max_bytes:
            return self.__AsyncLargeEntryDecision.WRITE

        # DROP
        if leb is LargeLogEntryBehavior.DumpSilently:
            return self.__AsyncLargeEntryDecision.DROP

        # CRASH
        if leb is LargeLogEntryBehavior.Crash:
            raise ValueError(
                f"Log entry of size {entry_size} exceeds max_bytes={self.max_bytes}"
            )

        # ROTATE FIRST
        if leb is LargeLogEntryBehavior.RotateFirst:
            return self.__AsyncLargeEntryDecision.ROTATE_THEN_WRITE

        # EXCEED_IF_EMPTY
        if leb is LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty:
            # Ensure stream exists
            if self.stream is None or getattr(self.stream, "closed", False):
                self.stream = self._open()

            empty = False
            try:
                self.stream.seek(0, os.SEEK_END)
                empty = (self.stream.tell() == 0)
            except OSError:
                # FD is broken: close best-effort and reopen, treat as empty
                try:
                    if self.stream is not None:
                        self.stream.close()
                except Exception:
                    pass
                self.stream = self._open()
                empty = True

            if empty:
                return self.__AsyncLargeEntryDecision.WRITE
            return self.__AsyncLargeEntryDecision.ROTATE_THEN_WRITE

        return self.__AsyncLargeEntryDecision.WRITE

    def __size_would_exceed(self, formatted: str) -> bool:
        """
        Fast size‑based rotation check.
        Uses the already‑formatted string instead of re‑formatting the record.
        """
        if self.max_bytes <= 0:
            return False

        # Ensure file is open
        if self.stream is None:
            self.stream = self._open()

        # Compute projected size
        msg = formatted + "\n"
        self.stream.seek(0, os.SEEK_END)
        current_size = self.stream.tell()
        projected = current_size + len(msg.encode(self.encoding or "utf-8"))

        return projected >= self.max_bytes

    def _ensure_stream_open(self):
        if self.stream is None:
            self.stream = self._open()
            return

        try:
            # harmless check that fails if FD is invalid
            self.stream.tell()
        except Exception:
            # FD is broken → reopen
            try:
                self.stream.close()
            except Exception:
                pass
            self.stream = self._open()

    def emit(self, record) -> None:
        # ------------------------------------------------------
        # 1. Special case: preformatted string (cross-thread test)
        # ------------------------------------------------------
        if not isinstance(record, logging.LogRecord):
            formatted = str(record)
            msg = formatted + "\n"

            try:
                # Ensure stream is open
                if self.stream is None or getattr(self.stream, "closed", False):
                    self.stream = self._open()

                # Size-based rotation only
                try:
                    self.stream.seek(0, os.SEEK_END)
                    current = self.stream.tell()
                except OSError:
                    # FD broken → reopen and treat as empty
                    try:
                        if self.stream:
                            self.stream.close()
                    except Exception:
                        pass
                    self.stream = self._open()
                    current = 0

                projected = current + len(msg.encode(self.encoding or "utf-8"))
                if self.max_bytes and self.max_bytes > 0 and projected >= self.max_bytes:
                    self.__schedule_rotation()

                # Write
                with self.write_lock:
                    if self.stream is None or getattr(self.stream, "closed", False):
                        self.stream = self._open()
                    self.stream.write(msg)
                    self.stream.flush()

            except OSError:
                # I/O-level failure: treat as logging error
                self.handleError(record)

            return

        try:
            # Ensure stream is open / healthy for I/O-related errors
            if self.stream is None or getattr(self.stream, "closed", False):
                self.stream = self._open()

            formatted = self.format(record)  # BadFormatter will raise here

            if self.audit_mode:
                formatted = f"{record.name} : {formatted}"

            msg = formatted + "\n"

            decision = self.__async_large_entry_decision(formatted)

            if decision is self.__AsyncLargeEntryDecision.DROP:
                self.__schedule_rotation()
                return

            if decision is self.__AsyncLargeEntryDecision.ROTATE_THEN_WRITE:
                self.__schedule_rotation()
            elif self.__should_rotate(record):
                self.__rotation_scheduled = False  # allow immediate re-scheduling
                self.__schedule_rotation()

            with self.write_lock:
                if self.stream is None or getattr(self.stream, "closed", False):
                    self.stream = self._open()
                self.stream.write(msg)
                self.stream.flush()

        except ValueError:
            # LargeEntryBehavior.Crash: propagate
            raise
        except OSError:
            # Stream-level I/O failure: treat as logging error
            self.handleError(record)

    def __schedule_rotation(self) -> None:
        """
        Helper: schedule async rotation exactly once per need.
        """
        if self.rotation_callback and not self.__rotation_scheduled:
            self.__rotation_scheduled = True
            # AsyncSmartLogger.__enqueue_rotation will enqueue ROTATE
            self.rotation_callback(self)

    def _rotation_suffix(self) -> str:
        parts = []
        if self.append_filename_pid:
            parts.append(str(os.getpid()))
        if self.append_filename_timestamp:
            parts.append(datetime.now().strftime("%Y%m%d_%H%M%S"))
        return ".".join(parts)

    def perform_rotation(self) -> None:
        """
        Executed inside AsyncSmartLogger's worker thread.
        Mirrors ConcurrentTimedSizedRotatingFileHandler._doRollover().
        """
        self.__rotation_scheduled = False

        self.acquire()
        try:
            # Close current file
            if self.stream:
                self.stream.close()
                self.stream = None  # type: ignore[assignment]

            # Rotate backups
            if self.backup_count > 0:
                for i in range(self.backup_count - 1, 0, -1):

                    # sfn = f"{self.baseFilename}.{i}"
                    # dfn = f"{self.baseFilename}.{i + 1}"
                    suffix = self._rotation_suffix()
                    if suffix:
                        sfn = f"{self.baseFilename}.{suffix}.{i}"
                        dfn = f"{self.baseFilename}.{suffix}.{i + 1}"
                    else:
                        sfn = f"{self.baseFilename}.{i}"
                        dfn = f"{self.baseFilename}.{i + 1}"

                    if os.path.exists(sfn):
                        if os.path.exists(dfn):
                            os.remove(dfn)
                        orig_mtime = os.path.getmtime(sfn)
                        os.replace(sfn, dfn)
                        os.utime(dfn, (orig_mtime, orig_mtime))

                # dfn = f"{self.baseFilename}.1"
                suffix = self._rotation_suffix()
                if suffix:
                    dfn = f"{self.baseFilename}.{suffix}.1"
                else:
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
                self.__rollover_at = self.__compute_next_rollover(now)
            else:
                self.__rollover_at = None

            # Apply retention
            self.__apply_expiration_policy()

        finally:
            self.release()
            self.__rotation_scheduled = False

    def __should_rotate(self, record: logging.LogRecord) -> bool:
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
        if self.__rollover_at is not None:
            now = time.time()
            if now >= self.__rollover_at:
                return True

        return False

    def __rollover_interval_seconds(self) -> float:
        if self.when == When.SECOND:
            return self.interval
        if self.when == When.MINUTE:
            return self.interval * 60
        if self.when == When.HOUR:
            return self.interval * 3600
        if self.when == When.EVERYDAY:
            return 24 * 3600
        return 7 * 24 * 3600  # weekly

    def __compute_initial_rollover(self) -> float:
        now = time.time()
        return self.__compute_next_rollover(now)

    def __compute_next_rollover(self, current: float) -> float:
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

    def __apply_expiration_policy(self) -> None:
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

        for path in self.__list_rotated_files():
            try:
                if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
                    os.remove(path)
            except OSError:
                pass    # pragma: no cover

    def __list_rotated_files(self) -> list[str]:
        base = self.baseFilename
        dir_name = os.path.dirname(base)
        prefix = os.path.basename(base)

        return [
            os.path.join(dir_name, f)
            for f in os.listdir(dir_name)
            if f.startswith(prefix)
               and not f.endswith(".lock")
        ]
