"""Models for the Telegram app."""

from datetime import time

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_telegram_app.models import AbstractTelegramSettings

from reminders.scheduling import HydrationSchedule


class TelegramSettings(AbstractTelegramSettings):
    """Extend the default Telegram settings model."""

    daily_goal_ml = models.IntegerField(
        verbose_name=_("daily goal (ml)"),
        default=3000,
        help_text=_(
            "Your total water goal for the day (in milliliters). "
            "The bot will help you reach this amount before the end of your reminder window. Default is 3000 ml."
        ),
    )
    reminder_window_start = models.TimeField(
        verbose_name=_("first reminder"),
        default=time.fromisoformat("08:00"),
        help_text=_("The time of day when your reminders should begin. Default is 08:00."),
    )
    reminder_window_end = models.TimeField(
        verbose_name=_("last reminder"),
        default=time.fromisoformat("22:00"),
        help_text=_(
            "The time of day when your reminders should stop. The final reminder will never be sent after this time. "
            "Default is 22:00."
        ),
    )
    consumption_size_ml = models.IntegerField(
        verbose_name=_("consumption size (ml)"),
        default=250,
        help_text=_(
            "How much water you usually drink per reminder (in milliliters). This must be between 100 and 500 ml. "
            "The bot uses this to plan how many reminders you need each day. Default is 250 ml."
        ),
        validators=[MinValueValidator(100), MaxValueValidator(500)],
    )
    reminder_repeat_interval_seconds = models.IntegerField(
        verbose_name=_("reminder repeat interval (seconds)"),
        default=900,
        help_text=_(
            "How long the bot should wait before repeating a reminder if you haven't logged your drink (in seconds). "
            "Default is 15 minutes (900 seconds). "
        ),
    )
    minimum_interval_seconds = models.FloatField(
        verbose_name=_("minimum interval (seconds)"),
        default=1200.0,
        help_text=_(
            "The shortest allowed time between reminders (in seconds). "
            "This prevents the bot from sending reminders too close together. Default is 20 minutes (1200 seconds)."
        ),
    )
    reminder_text = models.CharField(
        verbose_name=_("reminder text"),
        default=_("Time to hydrate!"),
        help_text=_("The message you want the bot to send you for each reminder. Default is 'Time to hydrate!'."),
    )
    next_reminder_at = models.TimeField(
        verbose_name=_("next reminder at"), null=True, blank=True, help_text=_("when the next reminder is scheduled")
    )
    consumed_today_ml = models.IntegerField(
        verbose_name=_("consumed today (ml)"),
        default=0,
        help_text=_("amount of water consumed today (ml), resets at midnight"),
    )
    is_initialized = models.BooleanField(
        verbose_name=_("is initialized"),
        default=False,
        help_text=_("whether the initial setup has been completed"),
    )
    last_reminder_sent_at = models.DateTimeField(
        verbose_name=_("last reminder sent at"),
        null=True,
        blank=True,
        help_text=_("timestamp of the last reminder sent"),
    )

    @property
    def hydration_schedule(self) -> HydrationSchedule:
        """Get the hydration schedule for the user."""
        return HydrationSchedule(
            goal_ml=self.daily_goal_ml,
            consumed_ml=self.consumed_today_ml,
            consumption_size_ml=self.consumption_size_ml,
            window_start=self.reminder_window_start,
            window_end=self.reminder_window_end,
            minimum_interval_seconds=self.minimum_interval_seconds,
        )

    def in_reminder_window(self, time_: time | None = None) -> bool:
        """Check if the current time is within the reminder window."""
        if time_ is None:
            time_ = timezone.now().time()
        return self.hydration_schedule.in_reminder_window(time_)

    def compute_next_reminder_datetime(self, from_time: time | None = None):
        """Compute the next reminder datetime."""
        if from_time is None:
            from_time = timezone.now().time()
        return self.hydration_schedule.compute_next_reminder(from_time)
