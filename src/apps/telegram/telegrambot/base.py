"""Base classes."""

from abc import ABC

from django_telegram_app.bot.base import BaseBotCommand, Step

from apps.telegram.models import TelegramSettings


class TelegramCommand(BaseBotCommand, ABC):
    """Base class for telegram commands."""

    settings: TelegramSettings


class TelegramStep(Step, ABC):
    """Base class for telegram command steps."""

    command: TelegramCommand
