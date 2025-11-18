"""Reminder command for the telegram bot."""

from django.utils import timezone
from django_telegram_app.bot import bot
from django_telegram_app.bot.base import TelegramUpdate

from apps.telegram.models import TelegramSettings
from apps.telegram.telegrambot.base import TelegramCommand, TelegramStep


class Command(TelegramCommand):
    """Reminder command to send hydration reminders."""

    description = "Send hydration reminders to the user."
    settings: TelegramSettings

    @property
    def steps(self):
        """Return the steps of the command."""
        return [Remind(self), ScheduleNext(self)]


class Remind(TelegramStep):
    """Step to send a reminder."""

    def handle(self, telegram_update: TelegramUpdate):
        """Handle the reminder step."""
        if self.command.settings.next_reminder_at and self.command.settings.next_reminder_at > timezone.now():
            # Not time for the next reminder yet
            return

        # If there is no next_reminder_at, check if we are within the reminder window
        if not self.command.settings.next_reminder_at:
            # Set next_reminder_at to the next first reminder
            next_day = timezone.now()
            if timezone.now().time() > self.command.settings.reminder_window_end:
                next_day += timezone.timedelta(days=1)
            next_reminder_at = next_day.replace(
                hour=self.command.settings.reminder_window_start.hour,
                minute=self.command.settings.reminder_window_start.minute,
                second=self.command.settings.reminder_window_start.second,
                microsecond=0,
            )
            self.command.settings.next_reminder_at = next_reminder_at
            self.command.settings.save()
            return
        now_time = timezone.now().time()
        if not (self.command.settings.reminder_window_start <= now_time <= self.command.settings.reminder_window_end):
            # Set next_reminder_at to the next first reminder
            # if we are past midnight, schedule for the same day
            next_day = timezone.now()
            if now_time > self.command.settings.reminder_window_end:
                next_day += timezone.timedelta(days=1)
            next_reminder_at = next_day.replace(
                hour=self.command.settings.reminder_window_start.hour,
                minute=self.command.settings.reminder_window_start.minute,
                second=self.command.settings.reminder_window_start.second,
                microsecond=0,
            )
            self.command.settings.next_reminder_at = next_reminder_at
            self.command.settings.save()
            return

        data = self.get_callback_data(telegram_update)
        reminder_text = self.command.settings.reminder_text
        keyboard = [
            [{"text": "💧 Done", "callback_data": self.next_step_callback(**data, done=True)}],
            [{"text": "⏰ Postpone", "callback_data": self.next_step_callback(**data, done=False)}],
        ]
        bot.send_message(
            reminder_text,
            self.command.settings.chat_id,
            reply_markup={"inline_keyboard": keyboard},
            message_id=telegram_update.message_id,
        )


class ScheduleNext(TelegramStep):
    """Step to schedule the next reminder."""

    def handle(self, telegram_update: TelegramUpdate):
        """Handle scheduling the next reminder."""
        data = self.get_callback_data(telegram_update)
        done = data.get("done")
        if done:
            # User has consumed water, schedule next reminder
            interval_seconds = (
                self.command.settings.compute_next_reminder_datetime().timestamp() - timezone.now().timestamp()
            )
        else:
            # User postponed, use default postpone time
            interval_seconds = self.command.settings.default_postpone_seconds
        next_reminder_at = timezone.now() + timezone.timedelta(seconds=interval_seconds)
        # Check if next_reminder_at is within reminder window
        reminder_first = self.command.settings.reminder_window_start
        reminder_last = self.command.settings.reminder_window_end
        if not (reminder_first <= next_reminder_at.time() <= reminder_last):
            # Set next_reminder_at to the next first reminder
            # if we are past midnight, schedule for the same day
            next_day = timezone.now()
            if next_reminder_at.time() > reminder_last:
                next_day += timezone.timedelta(days=1)
            next_reminder_at = next_day.replace(
                hour=reminder_first.hour,
                minute=reminder_first.minute,
                second=reminder_first.second,
                microsecond=0,
            )
        self.command.settings.next_reminder_at = next_reminder_at
        self.command.settings.save()
        bot.send_message(
            f"Next reminder scheduled at {next_reminder_at.strftime('%H:%M:%S')}.",
            self.command.settings.chat_id,
            message_id=telegram_update.message_id,
        )
        self.command.next_step(self.name, telegram_update)
