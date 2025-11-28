"""Tests for the telegram app."""

from datetime import datetime, time
from unittest.mock import patch

from django.utils import timezone
from django_telegram_app.bot.testing.testcases import TelegramBotTestCase

from apps.telegram.models import TelegramSettings


class StartCommandTests(TelegramBotTestCase):
    """Start command test case."""

    def test_start_command_flow(self):
        """Test the full flow of the start command."""
        self.send_text("/start")
        self.send_text("2500")  # daily_goal
        self.send_text("invalid time")  # reminder_window_start
        self.assertIn("Invalid input for first reminder", self.last_bot_message)
        self.send_text("09:00")  # reminder_window_start
        self.send_text("21:00")  # reminder_window_end
        self.assertTrue(self.last_bot_message.startswith("Please provide your consumption size (ml)."))
        self.send_text("300")  # consumption_size
        self.send_text("60")  # minimum_interval
        self.click_on_text("Use default (Time to hydrate!)")  # reminder_text
        self.click_on_text("✅ Yes")  # confirmation

        # Verify that the settings were created/updated correctly
        chat_id = self.fake_bot_post.call_args[1]["payload"]["chat_id"]
        settings = TelegramSettings.objects.get(chat_id=chat_id)
        self.assertEqual(settings.daily_goal_ml, 2500)
        self.assertEqual(settings.reminder_window_start.strftime("%H:%M"), "09:00")
        self.assertEqual(settings.reminder_window_end.strftime("%H:%M"), "21:00")
        self.assertEqual(settings.consumption_size_ml, 300)
        self.assertEqual(settings.minimum_interval_seconds, 60)
        self.assertEqual(settings.reminder_text, "Time to hydrate!")
        self.assertTrue(settings.is_initialized)
        self.assertIsNotNone(settings.next_reminder_at)


class ReminderCommandTests(TelegramBotTestCase):
    """Reminder command test case."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.telegramsettings = TelegramSettings.objects.create(
            chat_id=123456789,
            daily_goal_ml=2000,
            consumption_size_ml=250,
            reminder_text="Time to hydrate!",
            reminder_window_start="08:00:00",
            reminder_window_end="22:00:00",
            minimum_interval_seconds=300,
            is_initialized=True,
        )

    def test_reminder_command(self):
        """Test the reminder command.

        Goal: 2000 ml
        Glass size: 250 ml → 8 glasses total
        First reminder at 08:00 is "Done"
        At 08:00 you've already consumed at least one 250 ml (or your consumed_ml starts non-zero)
        So at 08:00, the remaining looks like this, for example:

        If consumed_ml is 250 at 08:00:
        remaining_ml = 1750
        remaining_reminders = ceil(1750 / 250) = 7
        remaining window: 08:00 → 22:00 = 14h = 50400s
        ideal_interval = 50400 / 7 ≈ 7200s = 2h
        """
        fake_datetime = timezone.now().replace(hour=7, minute=0, second=0, microsecond=0)
        self.assertIsNone(self.telegramsettings.next_reminder_at)
        self._remind_only(fake_datetime)
        self.assertEqual(self.telegramsettings.next_reminder_at, time(8, 0))
        fake_datetime = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)
        for _ in range(7):
            next_reminder_time = self._remind_and_done(fake_datetime)
            # Call remind half an hour later to ensure nothing it sent before next_reminder_at
            self._remind_only(fake_datetime + timezone.timedelta(minutes=30))
            fake_datetime = fake_datetime.replace(
                hour=next_reminder_time.hour, minute=next_reminder_time.minute, second=next_reminder_time.second
            )

        # Final reminder should be sent at 22, expected next reminder is after window
        self.assertEqual(fake_datetime.time(), time(22))
        expected_time = self.telegramsettings.reminder_window_start
        self._remind_and_done(fake_datetime, expected_time=expected_time)
        self.assertEqual(self.telegramsettings.consumed_today_ml, self.telegramsettings.daily_goal_ml)

    def _remind_only(self, fake_datetime: datetime):
        with patch("apps.telegram.telegrambot.commands.reminder.timezone.now", return_value=fake_datetime):
            self.send_text("/reminder")
        self.telegramsettings.refresh_from_db()

    def _remind_and_done(self, fake_datetime: datetime, expected_time: time | None = None):
        with patch("apps.telegram.telegrambot.commands.reminder.timezone.now", return_value=fake_datetime):
            self.send_text("/reminder")
            self.click_on_text("💧 Done")
            self.telegramsettings.refresh_from_db()
        if not expected_time:
            expected_time = (fake_datetime + timezone.timedelta(hours=2)).time()
        self.assertEqual(self.telegramsettings.next_reminder_at, expected_time)
        return expected_time


class HydrateCommandTests(TelegramBotTestCase):
    """Hydrate command test case."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.telegramsettings = TelegramSettings.objects.create(
            chat_id=123456789,
            daily_goal_ml=2000,
            consumption_size_ml=250,
            reminder_text="Time to hydrate!",
            reminder_window_start="08:00:00",
            reminder_window_end="22:00:00",
            minimum_interval_seconds=300,
            is_initialized=True,
        )

    def test_hydrate_command(self):
        """Test the hydrate command flow."""
        self.assertEqual(self.telegramsettings.consumed_today_ml, 0)
        self.send_text("/hydrate")
        self.assertTrue(self.last_bot_message.startswith("Please provide your consumption size (ml)"))
        self.send_text("invalid input")
        self.assertIn("Invalid input for", self.last_bot_message)
        self.send_text("300")

        # Verify that the consumption was logged correctly
        self.telegramsettings.refresh_from_db()
        self.assertEqual(self.telegramsettings.consumed_today_ml, 300)
        self.assertIsNotNone(self.telegramsettings.next_reminder_at)
