"""Start overview command for all telegram settings."""

from django.utils import timezone
from django_telegram_app.management.base import BaseManagementCommand
from django_telegram_app.models import AbstractTelegramSettings

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
        super().handle_command(telegram_settings, command_text)
        telegram_settings.next_overview_at = None
        telegram_settings.save()
