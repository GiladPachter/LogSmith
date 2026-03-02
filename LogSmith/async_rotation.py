# LogSmith/async_rotation.py

from __future__ import annotations

import os
import threading
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, IO

from .rotation import RotationLogic, When, RotationTimestamp, ExpirationScale


class Async_TimedSizedRotatingFileHandler(logging.FileHandler):
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

    rotation_callback: Optional[Callable[[ "Async_TimedSizedRotatingFileHandler" ], None]] = None

    def __init__(
        self,
        baseFilename: str,
        rotation_logic: RotationLogic,
        encoding: Optional[str] = "utf-8",
        delay: bool = False,
    ) -> None:

        self.rotation_logic = rotation_logic
        self.baseFilename = os.path.abspath(baseFilename)
        self._last_rotation_check = 0.0

        # FileHandler initialization
        super().__init__(self.baseFilename, mode="a", encoding=encoding, delay=delay)

        # Tell PyCharm the truth: stream can be None
        self.stream: Optional[IO[str]] = self.stream

        # For debugging / introspection
        self.resolved_path = str(Path(self.baseFilename).resolve())

        # Time-based rollover scheduling
        self.when = rotation_logic.when
        self.interval = rotation_logic.interval or 1
        self.timestamp = rotation_logic.timestamp

        self.write_lock = threading.Lock()

        self._rollover_at = None
        if self.when is not None:
            self._rollover_at = self._compute_initial_rollover()

    # ------------------------------------------------------------------
    #  EMIT (detect rotation, schedule async rotation)
    # ------------------------------------------------------------------
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)

        now = time.time()
        if now - self._last_rotation_check < 0.25:
            return

        self._last_rotation_check = now

        # FIX: correct RotationLogic API
        if self.should_rotate(record):
            if self.rotation_callback:
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
            if self.rotation_logic.backupCount > 0:
                for i in range(self.rotation_logic.backupCount - 1, 0, -1):
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
        if self.rotation_logic.maxBytes and self.rotation_logic.maxBytes > 0:
            msg = f"{self.format(record)}\n"
            self.stream.seek(0, os.SEEK_END)
            current_size = self.stream.tell()
            projected = current_size + len(msg.encode(self.encoding or "utf-8"))
            if projected >= self.rotation_logic.maxBytes:
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
        rule = self.rotation_logic.expiration_rule
        if rule is None:
            return

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
            return

        for path in self._list_rotated_files():
            try:
                if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
                    os.remove(path)
            except OSError:
                pass

    def _list_rotated_files(self) -> list[str]:
        base = self.baseFilename
        dir_name = os.path.dirname(base)
        prefix = os.path.basename(base)

        return [
            os.path.join(dir_name, f)
            for f in os.listdir(dir_name)
            if f.startswith(prefix)
        ]
