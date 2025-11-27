"""Reminder command for the telegram bot."""

from django.utils import timezone
from django_telegram_app.bot import bot
from django_telegram_app.bot.base import TelegramUpdate

from apps.telegram.telegrambot.base import TelegramCommand, TelegramStep


class Command(TelegramCommand):
    """Reminder command to send hydration reminders."""

    description = "Send hydration reminders to the user."

    @property
    def steps(self):
        """Return the steps of the command."""
        return [Remind(self), ScheduleNext(self)]


class Remind(TelegramStep):
    """Step to send a reminder."""

    def handle(self, telegram_update: TelegramUpdate):
        """Handle the reminder step."""
        if not self.command.settings.is_initialized:
            # Settings not initialized; do not send reminder
            # Don't send a message either, since we don't want to spam uninitialized users.
            return

        if not self.command.settings.next_reminder_at:
            # First reminder
            self.command.settings.next_reminder_at = self.command.settings.compute_next_reminder_datetime()
            self.command.settings.save()
            return

        now = timezone.now()
        current_time = now.time()
        if self.command.settings.next_reminder_at > current_time:
            # Not time for the next reminder yet
            return

        if self.command.settings.last_reminder_sent_at:
            # Reminder already sent for the current period
            earliest_reminder = self.command.settings.last_reminder_sent_at + timezone.timedelta(
                seconds=self.command.settings.reminder_repeat_interval_seconds
            )
            if earliest_reminder > now:
                return

        data = self.get_callback_data(telegram_update)
        keyboard = [[{"text": "💧 Done", "callback_data": self.next_step_callback(data, done=True)}]]
        bot.send_message(
            self.command.settings.reminder_text,
            self.command.settings.chat_id,
            reply_markup={"inline_keyboard": keyboard},
            message_id=telegram_update.message_id,
        )
        self.command.settings.last_reminder_sent_at = now
        self.command.settings.save()


class ScheduleNext(TelegramStep):
    """Step to schedule the next reminder."""

    def handle(self, telegram_update: TelegramUpdate):
        """Handle scheduling the next reminder."""
        now = timezone.now()
        from_time = now.time()
        self.command.settings.consumed_today_ml += self.command.settings.consumption_size_ml
        next_reminder_at = self.command.settings.compute_next_reminder_datetime(from_time)

        self.command.settings.last_reminder_sent_at = None
        self.command.settings.next_reminder_at = next_reminder_at
        self.command.settings.save()
        bot.send_message(
            f"Next reminder scheduled at {next_reminder_at.isoformat(timespec='seconds')} UTC.",
            self.command.settings.chat_id,
            message_id=telegram_update.message_id,
        )
        self.command.next_step(self.name, telegram_update)
