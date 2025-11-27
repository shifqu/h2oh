"""Start reminder command for all telegram settings."""

from django_telegram_app.management.base import BaseManagementCommand

from apps.telegram.telegrambot.commands.reminder import Command as ReminderCommand


class Command(BaseManagementCommand):
    """Start the reminder command for all telegram settings."""

    command = ReminderCommand

    def get_telegram_settings_filter(self):
        """Filter on initialized settings."""
        return {"is_initialized": True}
