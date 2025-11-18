"""Base classes."""

from abc import ABC

from django_telegram_app.bot.base import BaseCommand, Step

from apps.telegram.models import TelegramSettings


class TelegramCommand(BaseCommand, ABC):
    """Base class for telegram commands."""

    settings: TelegramSettings


class TelegramStep(Step, ABC):
    """Base class for telegram command steps."""

    command: TelegramCommand
