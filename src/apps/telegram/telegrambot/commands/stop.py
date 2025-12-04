"""Stop command for Telegram bot."""

from django.utils.translation import gettext as _
from django_telegram_app.bot import bot
from django_telegram_app.bot.base import TelegramUpdate

from apps.telegram.telegrambot.base import TelegramCommand, TelegramStep


class Command(TelegramCommand):
    """Stop command to stop the bot and clear settings.

    Confirm with the user if they want to stop the bot and clear their TelegramSettings.
    """

    description = _("Stop command to stop the bot and clear settings.")

    @property
    def steps(self):
        """Return the steps of the command."""
        return [AskConfirmation(self), ConfirmStop(self)]


class AskConfirmation(TelegramStep):
    """Step to ask the user for confirmation."""

    def handle(self, telegram_update: TelegramUpdate):
        """Prepare any data needed for the Ask step."""
        data = self.get_callback_data(telegram_update)
        keyboard = [
            [
                {"text": _("✅ Yes"), "callback_data": self.next_step_callback(data, confirmation="yes")},
                {"text": _("⛔️ No"), "callback_data": self.cancel_callback(data, confirmation="no")},
            ]
        ]
        reply_markup = {"inline_keyboard": keyboard}
        prompt = _("Are you sure you want your settings to be cleared?\nYou won't receive reminders anymore.")
        bot.send_message(
            prompt,
            self.command.settings.chat_id,
            reply_markup=reply_markup,
            message_id=telegram_update.message_id,
        )


class ConfirmStop(TelegramStep):
    """Final confirmation step to complete the stop command."""

    def handle(self, telegram_update: TelegramUpdate):
        """Remove the settings and stop the bot."""
        self.command.settings.delete()
        confirmation_message = _(
            "Your settings have been cleared. You will no longer receive hydration reminders. "
            "If you want to start again, just send the /start command."
        )
        bot.send_message(confirmation_message, self.command.settings.chat_id, message_id=telegram_update.message_id)
        self.command.finish(self.name, telegram_update)
