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

        current_time = timezone.now().time()
        if self.command.settings.next_reminder_at > current_time:
            # Not time for the next reminder yet
            return

        data = self.get_callback_data(telegram_update)
        keyboard = [
            [{"text": "💧 Done", "callback_data": self.next_step_callback(data, done=True)}],
            [{"text": "⏰ Postpone", "callback_data": self.next_step_callback(data, done=False)}],
        ]
        bot.send_message(
            self.command.settings.reminder_text,
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
        now = timezone.now()
        from_time = now.time()
        if done:
            self.command.settings.consumed_today_ml += self.command.settings.consumption_size_ml

        next_reminder_at = self.command.settings.compute_next_reminder_datetime(from_time)
        if not done:
            postponed_time = (now + timezone.timedelta(seconds=self.command.settings.default_postpone_seconds)).time()
            if self.command.settings.in_reminder_window(postponed_time):
                next_reminder_at = postponed_time

        self.command.settings.next_reminder_at = next_reminder_at
        self.command.settings.save()
        bot.send_message(
            f"Next reminder scheduled at {next_reminder_at.isoformat(timespec='seconds')} UTC.",
            self.command.settings.chat_id,
            message_id=telegram_update.message_id,
        )
        self.command.next_step(self.name, telegram_update)
