"""Start reminder command for the users app."""

from django_telegram_app.management.base import BaseTelegramCommand

from apps.telegram.telegrambot.commands.reminder import Command as ReminderCommand


class Command(BaseTelegramCommand):
    """Start the reminder command for all active users."""

    command = ReminderCommand
