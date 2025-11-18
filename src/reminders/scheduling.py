"""Module that is the brain for scheduling reminders."""

import math
from dataclasses import dataclass
from datetime import datetime, time, timedelta


@dataclass(kw_only=True)
class HydrationSchedule:
    """Class to compute reminder scheduling."""

    goal_ml: int
    consumed_ml: int
    consumption_size_ml: int
    window_start: time
    window_end: time
    minimum_interval_seconds: float

    @property
    def remaining_ml(self):
        """Return the remaining ml to consume for the day."""
        return max(0, self.goal_ml - self.consumed_ml)

    @property
    def remaining_reminders(self):
        """Return the remaining reminders for the day."""
        return math.ceil(self.remaining_ml / self.consumption_size_ml)

    def get_remaining_window_seconds(self, now: datetime, end: time) -> int:
        """Return the remaining seconds in the reminder window for the day."""
        now_seconds = now.hour * 3600 + now.minute * 60 + now.second
        end_seconds = end.hour * 3600 + end.minute * 60 + end.second
        remaining_seconds = end_seconds - now_seconds
        return max(0, remaining_seconds)

    def get_ideal_interval_seconds(self, now: datetime):
        """Return the interval in seconds between reminders."""
        remaining_reminders = self.remaining_reminders
        if remaining_reminders <= 0:
            return None
        remaining_window_seconds = self.get_remaining_window_seconds(now, self.window_end)
        if remaining_window_seconds <= 0:
            return None
        return remaining_window_seconds / remaining_reminders

    def get_interval_seconds(self, now: datetime):
        """Return the interval in seconds between reminders, respecting the minimum interval."""
        ideal_interval = self.get_ideal_interval_seconds(now)
        if ideal_interval is None:
            return None
        if ideal_interval < self.minimum_interval_seconds:
            return self.minimum_interval_seconds
        return ideal_interval

    def goal_reachable(self, now: datetime) -> bool:
        """Return whether the daily goal is still reachable."""
        ideal_interval_seconds = self.get_ideal_interval_seconds(now)
        if ideal_interval_seconds is None:
            return False
        return ideal_interval_seconds >= self.minimum_interval_seconds

    def compute_next_reminder_datetime(self, from_time: datetime) -> datetime:
        """Compute the next reminder time based on the current time and interval."""
        interval_seconds = self.get_interval_seconds(from_time)
        window_start = self.window_start
        window_end = self.window_end

        if interval_seconds is None:
            next_reminder_dt = from_time.replace(
                hour=window_start.hour,
                minute=window_start.minute,
                second=window_start.second,
                microsecond=0,
            )
            if next_reminder_dt <= from_time:
                next_reminder_dt += timedelta(days=1)
            return next_reminder_dt

        candidate = from_time + timedelta(seconds=interval_seconds)
        candidate_time = candidate.time()

        if candidate_time < window_start:
            candidate = candidate.replace(
                hour=window_start.hour,
                minute=window_start.minute,
                second=window_start.second,
                microsecond=0,
            )
            candidate_time = candidate.time()

        if candidate_time > window_end:
            candidate = candidate.replace(
                hour=window_start.hour,
                minute=window_start.minute,
                second=window_start.second,
                microsecond=0,
            ) + timedelta(days=1)

        return candidate
