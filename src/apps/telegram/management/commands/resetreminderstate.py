"""Reset reminder state command."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.telegram.models import TelegramSettings


class Command(BaseCommand):
    """Reset reminder state for all telegram settings."""

    help = "Reset reminder state for all telegram settings."

    def handle(self, *_args, **_options):
        """Reset reminder state for all telegram settings."""
        if not TelegramSettings.objects.exists():
            self.stdout.write(self.style.NOTICE("No TelegramSettings found. Nothing to do."))
            return

        with transaction.atomic():
            for telegram_settings in TelegramSettings.objects.all():
                telegram_settings.consumed_today_ml = 0
                telegram_settings.next_reminder_at = telegram_settings.reminder_window_start
                telegram_settings.last_reminder_sent_at = None
                telegram_settings.save()
        self.stdout.write(self.style.SUCCESS("Successfully reset reminder state for all users."))
