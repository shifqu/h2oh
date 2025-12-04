"""Start overview command for all telegram settings."""

from django.db.models.query_utils import Q
from django.utils import timezone
from django_telegram_app.bot.base import TelegramUpdate
from django_telegram_app.bot.bot import handle_update
from django_telegram_app.management.base import BaseManagementCommand
from django_telegram_app.models import AbstractTelegramSettings, Message

from apps.telegram.telegrambot.base import TelegramSettings
from apps.telegram.telegrambot.commands.overview import Command as OverviewCommand


class Command(BaseManagementCommand):
    """Start the overview command for all telegram settings."""

    command = OverviewCommand

    def get_telegram_settings_filter(self):
        """Filter on initialized settings."""
        return {"is_initialized": True, "next_overview_at__lte": timezone.now().time()}

    def handle_command(self, telegram_settings: AbstractTelegramSettings, command_text: str):
        """Handle the command and clear next_overview_at."""
        assert isinstance(telegram_settings, TelegramSettings)
        telegram_settings.next_reminder_at = telegram_settings.reminder_window_start
        telegram_settings.save()
        update = self._create_update(telegram_settings, command_text)
        handle_update(update=update, telegram_settings=telegram_settings)
        telegram_settings.next_overview_at = None
        telegram_settings.save()

    def _create_update(self, telegram_settings: TelegramSettings, command_text: str) -> dict:
        """Create a fake update for the given telegram settings and command text.

        If the telegram settings has a last message, use its language code.
        """
        update = {"message": {"chat": {"id": telegram_settings.chat_id}, "text": command_text}}
        last_message = self._get_last_message(telegram_settings.chat_id)
        if last_message:
            language_code = TelegramUpdate(last_message.raw_message).language_code
            update["message"]["from"] = {"id": telegram_settings.chat_id, "language_code": language_code}
        return update

    def _get_last_message(self, chat_id: int) -> Message | None:
        """Get the last message for the given chat id."""
        q_message = Q(raw_message__message__from__id=chat_id)
        q_callback_query = Q(raw_message__callback_query__from__id=chat_id)
        return Message.objects.filter(q_message | q_callback_query).order_by("-raw_message__update_id").first()
