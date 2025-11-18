"""Reset reminder state command."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.telegram.models import TelegramSettings


class Command(BaseCommand):
    """Reset reminder state for all users."""

    help = "Reset reminder state for all users."

    def handle(self, *_args, **_options):
        """Reset reminder state for all users."""
        if not TelegramSettings.objects.exists():
            self.stdout.write(self.style.NOTICE("No TelegramSettings found. Nothing to do."))
            return

        with transaction.atomic():
            for telegram_settings in TelegramSettings.objects.all():
                telegram_settings.consumed_today_ml = 0
                telegram_settings.save()
        self.stdout.write(self.style.SUCCESS("Successfully reset reminder state for all users."))
