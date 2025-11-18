"""Tests for the telegram app."""

from unittest.mock import patch

from django.utils import timezone
from django_telegram_app import get_telegram_settings_model
from django_telegram_app.bot.testing.testcases import TelegramBotTestCase


class TelegramCommandTests(TelegramBotTestCase):
    """Telegram command test case."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.telegramsettings = get_telegram_settings_model().objects.create(
            chat_id=123456789,
            daily_goal_ml=2000,
            consumption_size_ml=250,
            default_postpone_seconds=900,
            reminder_text="Time to hydrate!",
            reminder_first="08:00:00",
            reminder_last="22:00:00",
        )

    def test_reminder_command(self):
        """Test the reminder command."""
        # Patch time to a time within the reminder window
        mocked_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        with patch("apps.telegram.telegrambot.commands.reminder.timezone.now", return_value=mocked_time):
            self.send_text("/reminder")
            self.click_on_text("💧 Done")
