"""Module that is the brain for scheduling reminders."""

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


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

    def get_remaining_window_seconds(self, start: time, end: time) -> int:
        """Return the remaining seconds in the reminder window for the day."""
        now_seconds = start.hour * 3600 + start.minute * 60 + start.second
        end_seconds = end.hour * 3600 + end.minute * 60 + end.second
        remaining_seconds = end_seconds - now_seconds
        return max(0, remaining_seconds)

    def get_ideal_interval_seconds(self, from_time: time):
        """Return the interval in seconds between reminders."""
        remaining_reminders = self.remaining_reminders
        if remaining_reminders <= 0:
            return None
        remaining_window_seconds = self.get_remaining_window_seconds(from_time, self.window_end)
        if remaining_window_seconds <= 0:
            return None
        return remaining_window_seconds / remaining_reminders

    def get_interval_seconds(self, from_time: time):
        """Return the interval in seconds between reminders, respecting the minimum interval."""
        ideal_interval = self.get_ideal_interval_seconds(from_time)
        if ideal_interval is None:
            return None
        return max(ideal_interval, self.minimum_interval_seconds)

    def compute_next_reminder(self, from_time: time) -> time:
        """Compute the next reminder time based on the from_time and interval."""
        if not self.in_reminder_window(from_time):
            return self.window_start

        # If nothing was consumed yet, schedule the first reminder immediately
        if not self.consumed_ml:
            return from_time

        interval_seconds = self.get_interval_seconds(from_time)

        if interval_seconds is None:  # No more reminders can be scheduled today
            return self.window_start

        from_datetime = datetime.combine(date.today(), from_time)
        candidate = from_datetime + timedelta(seconds=interval_seconds)
        candidate_time = candidate.time()

        if not self.in_reminder_window(candidate_time):
            return self.window_start

        return candidate_time

    def in_reminder_window(self, time_: time) -> bool:
        """Check if the given time is within the reminder window."""
        return self.window_start <= time_ <= self.window_end
