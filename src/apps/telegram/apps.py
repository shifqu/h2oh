"""Telegram app configuration."""

from django.apps import AppConfig


class TelegramConfig(AppConfig):
    """Telegram AppConfig."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.telegram"
