"""Reminder command for the telegram bot."""

from django.utils import timezone
from django.utils.translation import gettext as _
from django_telegram_app.bot import bot
from django_telegram_app.bot.base import TelegramUpdate

from apps.telegram.telegrambot.base import TelegramCommand, TelegramStep


class Command(TelegramCommand):
    """Reminder command to send hydration reminders."""

    description = _("Send hydration reminders to the user.")
    exclude_from_help = True

    @property
    def steps(self):
        """Return the steps of the command."""
        return [Remind(self), ScheduleNext(self)]


class Remind(TelegramStep):
    """Step to send a reminder."""

    def handle(self, telegram_update: TelegramUpdate):
        """Handle the reminder step."""
        if not self.command.settings.is_initialized:
            self.send_not_initialized_message(telegram_update)
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

        if (
            self.command.settings.last_reminder_sent_at
            and self.command.settings.last_reminder_sent_at >= self.command.settings.next_reminder_at
        ):
            # Reminder already sent at this time
            return

        if not self.command.settings.in_reminder_window(current_time):
            # Outside reminder window
            return

        data = self.get_callback_data(telegram_update)
        keyboard = [[{"text": _("💧 Done"), "callback_data": self.next_step_callback(data, done=True)}]]
        bot.send_message(
            self.command.settings.reminder_text,
            self.command.settings.chat_id,
            reply_markup={"inline_keyboard": keyboard},
            message_id=telegram_update.message_id,
        )
        self.command.settings.last_reminder_sent_at = current_time
        self.command.settings.save()


class ScheduleNext(TelegramStep):
    """Step to schedule the next reminder."""

    def handle(self, telegram_update: TelegramUpdate):
        """Handle scheduling the next reminder."""
        now = timezone.now()
        from_time = now.time()
        self.command.settings.consumed_today_ml += self.command.settings.consumption_size_ml
        self.command.settings.next_reminder_at = self.command.settings.compute_next_reminder_datetime(from_time)
        self.command.settings.save()
        msg = _("Next reminder scheduled at {next_reminder_at}.").format(
            next_reminder_at=self.command.settings.get_next_reminder_at_display()
        )
        bot.send_message(
            msg,
            self.command.settings.chat_id,
            message_id=telegram_update.message_id,
        )
        self.command.next_step(self.name, telegram_update)
