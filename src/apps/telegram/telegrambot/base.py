"""Base classes."""

from abc import ABC

from django_telegram_app.bot import bot
from django_telegram_app.bot.base import BaseBotCommand, Step, TelegramUpdate

from apps.telegram.models import TelegramSettings


class TelegramCommand(BaseBotCommand, ABC):
    """Base class for telegram commands."""

    settings: TelegramSettings


class TelegramStep(Step, ABC):
    """Base class for telegram command steps."""

    command: TelegramCommand

    def send_not_initialized_message(self, telegram_update: TelegramUpdate):
        """Send a message instructing the user to complete the setup if the chat is not initialized."""
        if not self.command.settings.is_initialized:
            bot.send_message(
                "Please complete the setup first by using the /start command.",
                self.command.settings.chat_id,
                message_id=telegram_update.message_id,
            )
            return
