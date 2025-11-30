"""Start command for Telegram bot."""

import zoneinfo

from django.core.exceptions import ValidationError
from django_telegram_app.bot import bot
from django_telegram_app.bot.base import TelegramUpdate

from apps.telegram.telegrambot import timezoneinfo
from apps.telegram.telegrambot.base import TelegramCommand, TelegramStep


class Command(TelegramCommand):
    """Start command to welcome the user and initialize settings.

    Greet the user and ask them a series of questions to set up their TelegramSettings.
    """

    description = "Start command to welcome the user and initialize settings."

    @property
    def steps(self):
        """Return the steps of the command."""
        return [
            WelcomeStep(self),
            AskTimezoneRegion(self),
            ValidateTimezone(self, unique_id="validate_timezone_region"),
            AskTimezone(self),
            ValidateTimezone(self, unique_id="validate_timezone"),
            AskTelegramSettingsField(self, "daily_goal_ml", unique_id="ask_daily_goal_ml"),
            ValidateFieldInput(self, "daily_goal_ml", unique_id="validate_daily_goal_ml"),
            AskTelegramSettingsField(self, "reminder_window_start", unique_id="ask_reminder_window_start"),
            ValidateFieldInput(self, "reminder_window_start", unique_id="validate_reminder_window_start"),
            AskTelegramSettingsField(self, "reminder_window_end", unique_id="ask_reminder_window_end"),
            ValidateFieldInput(self, "reminder_window_end", unique_id="validate_reminder_window_end"),
            AskTelegramSettingsField(self, "consumption_size_ml", unique_id="ask_consumption_size_ml"),
            ValidateFieldInput(self, "consumption_size_ml", unique_id="validate_consumption_size_ml"),
            AskTelegramSettingsField(self, "minimum_interval_seconds", unique_id="ask_minimum_interval_seconds"),
            ValidateFieldInput(self, "minimum_interval_seconds", unique_id="validate_minimum_interval_seconds"),
            AskTelegramSettingsField(self, "reminder_text", unique_id="ask_reminder_text"),
            ValidateFieldInput(self, "reminder_text", unique_id="validate_reminder_text"),
            AskConfirmation(self),
            ConfirmStart(self),
        ]


class WelcomeStep(TelegramStep):
    """Step to welcome the user."""

    def handle(self, telegram_update: TelegramUpdate):
        """Greet the user and advance to the next step."""
        greeting = (
            "Welcome to H2Oh! I am here to help you track and maintain your daily water intake. "
            "Let's get started with setting up your preferences."
        )
        bot.send_message(greeting, self.command.settings.chat_id, message_id=telegram_update.message_id)
        self.command.next_step(self.name, telegram_update)


class AskTimezoneRegion(TelegramStep):
    """Step to ask the user for their timezone region."""

    def handle(self, telegram_update: TelegramUpdate):
        """Ask the user for their timezone region."""
        data = self.get_callback_data(telegram_update)
        prompt = (
            "Please choose your timezone region, or send your timezone name directly.\n"
            "For example: Europe/Brussels, America/New_York, Asia/Tokyo.\n\n"
            "If you're not sure, just pick the region where you live."
        )
        if "_error" in data:
            prompt = f"{data.pop('_error')}\n\n{prompt}"
        self.add_waiting_for("timezone", data)
        keyboard = []
        for region in timezoneinfo.COMMON_TIMEZONES:
            callback_data = self.next_step_callback(data, timezone_region=region)
            keyboard.append([{"text": region, "callback_data": callback_data}])
        reply_markup = {"inline_keyboard": keyboard}
        bot.send_message(
            prompt,
            self.command.settings.chat_id,
            reply_markup=reply_markup,
            message_id=telegram_update.message_id,
        )


class ValidateTimezone(TelegramStep):
    """Step to validate the user's timezone input."""

    def handle(self, telegram_update: TelegramUpdate):
        """Validate the user's timezone input."""
        data = self.get_callback_data(telegram_update)
        timezone_input = data.get("timezone", "")
        normalized_tz = timezoneinfo.normalize_timezone(timezone_input)
        if "timezone" in data and normalized_tz not in timezoneinfo.ALL_TIMEZONES:
            error_message = (
                f"The timezone '{timezone_input}' (normalized as '{normalized_tz}') is not valid. Please try again."
            )
            data.pop("timezone")
            telegram_update.callback_data = self.previous_step_callback(1, data, _error=error_message)
            self.command.previous_step(self.name, telegram_update)
            return

        self.command.next_step(self.name, telegram_update)


class AskTimezone(TelegramStep):
    """Step to ask the user for their timezone."""

    def handle(self, telegram_update: TelegramUpdate):
        """Ask the user for their timezone."""
        data = self.get_callback_data(telegram_update)
        if "timezone" in data:
            # Timezone was provided directly, skip this step
            self.command.next_step(self.name, telegram_update)
            return

        prompt = "Please click on your timezone. To change region or manually enter your timezone, click '⬅️ Back'."
        region = data["timezone_region"]
        keyboard = []
        for tz in timezoneinfo.COMMON_TIMEZONES[region]:
            callback_data = self.next_step_callback(self.get_callback_data(telegram_update), timezone=tz)
            keyboard.append([{"text": tz, "callback_data": callback_data}])

        data.pop("timezone_region", None)
        data.pop("timezone", None)
        step_back_data = self.previous_step_callback(2, data)
        keyboard.append([{"text": "⬅️ Back", "callback_data": step_back_data}])

        reply_markup = {"inline_keyboard": keyboard}
        bot.send_message(
            prompt,
            self.command.settings.chat_id,
            reply_markup=reply_markup,
            message_id=telegram_update.message_id,
        )


class AskTelegramSettingsField(TelegramStep):
    """Step to ask the user for a value for a TelegramSettings field."""

    def __init__(self, command, field_name: str, unique_id=None):
        """Initialize the AskUserData step."""
        super().__init__(command, unique_id=unique_id)
        self.field_name = field_name
        self.field = self.command.settings._meta.get_field(self.field_name)
        self.prompt = f"Please provide your {self.field.verbose_name}.\n{self.field.help_text}"

    def handle(self, telegram_update: TelegramUpdate):
        """Prepare any data needed for the Ask step."""
        data = self.get_callback_data(telegram_update)
        if "_error" in data:
            self.prompt = f"{data.pop('_error')}\n\n{self.prompt}"
        self.add_waiting_for(self.field_name, data)
        reply_markup = None
        current_value = getattr(self.command.settings, self.field_name)
        if self.field.blank or current_value:
            skip_value = current_value or self.field.get_default()
            self.prompt += f"\nOr you can skip by clicking the button below to use the current value: {skip_value}."
            skip_options = {self.field_name: skip_value}
            next_callback = self.next_step_callback(data, **skip_options)
            keyboard = [[{"text": f"Use default ({skip_value})", "callback_data": next_callback}]]
            reply_markup = {"inline_keyboard": keyboard}
        bot.send_message(
            self.prompt,
            self.command.settings.chat_id,
            reply_markup=reply_markup,
            message_id=telegram_update.message_id,
        )


class ValidateFieldInput(TelegramStep):
    """Step to validate user input for a TelegramSettings field."""

    def __init__(self, command, field_name: str, unique_id=None):
        """Initialize the ValidateFieldInput step."""
        super().__init__(command, unique_id=unique_id)
        self.field_name = field_name
        self.field = self.command.settings._meta.get_field(self.field_name)

    def handle(self, telegram_update: TelegramUpdate):
        """Validate the user input for the specified field."""
        data = self.get_callback_data(telegram_update)
        user_input = data.get(self.field_name)
        try:
            self.field.clean(user_input, model_instance=self.command.settings)
        except ValidationError as e:
            error_message = f"Invalid input for {self.field.verbose_name}: {e}."
            telegram_update.callback_data = self.previous_step_callback(1, data, _error=error_message)
            self.command.previous_step(self.name, telegram_update)
            return

        self.command.next_step(self.name, telegram_update)


class AskConfirmation(TelegramStep):
    """Step to ask the user for confirmation."""

    def handle(self, telegram_update: TelegramUpdate):
        """Prepare any data needed for the Ask step."""
        data = self.get_callback_data(telegram_update)
        keyboard = [
            [
                {"text": "✅ Yes", "callback_data": self.next_step_callback(data, confirmation="yes")},
                {"text": "⛔️ No", "callback_data": self.cancel_callback(data, confirmation="no")},
            ]
        ]
        reply_markup = {"inline_keyboard": keyboard}

        timezone = timezoneinfo.normalize_timezone(data.get("timezone", ""))
        daily_goal_ml = data.get("daily_goal_ml")
        reminder_window_start = data.get("reminder_window_start")
        reminder_window_end = data.get("reminder_window_end")
        consumption_size_ml = data.get("consumption_size_ml")
        minimum_interval_seconds = data.get("minimum_interval_seconds")
        reminder_text = data.get("reminder_text")
        prompt = (
            "Are these settings correct?\n"
            f" - Timezone: {timezone}\n"
            f" - Daily goal (ml): {daily_goal_ml}\n"
            f" - Reminder window start: {reminder_window_start}\n"
            f" - Reminder window end: {reminder_window_end}\n"
            f" - Consumption size (ml): {consumption_size_ml}\n"
            f" - Minimum interval (seconds): {minimum_interval_seconds}\n"
            f" - Reminder text: {reminder_text}"
        )
        bot.send_message(
            prompt,
            self.command.settings.chat_id,
            reply_markup=reply_markup,
            message_id=telegram_update.message_id,
        )


class ConfirmStart(TelegramStep):
    """Final confirmation step to complete the start command."""

    def handle(self, telegram_update: TelegramUpdate):
        """Confirm the setup is complete and send a final message."""
        data = self.get_callback_data(telegram_update)
        keys = [
            "timezone",
            "daily_goal_ml",
            "reminder_window_start",
            "reminder_window_end",
            "consumption_size_ml",
            "minimum_interval_seconds",
            "reminder_text",
        ]
        cmd_settings = self.command.settings
        for key in keys:
            key_data = data.get(key)
            if not key_data:
                continue
            setattr(cmd_settings, key, key_data)
        cmd_settings.is_initialized = True
        cmd_settings.full_clean()
        cmd_settings.timezone = zoneinfo.ZoneInfo(cmd_settings.timezone).key
        cmd_settings.reminder_window_start = cmd_settings.convert_time_to_utc(cmd_settings.reminder_window_start)
        cmd_settings.reminder_window_end = cmd_settings.convert_time_to_utc(cmd_settings.reminder_window_end)
        cmd_settings.next_reminder_at = cmd_settings.compute_next_reminder_datetime()
        cmd_settings.save()
        confirmation_message = (
            "Thank you! Your setup is now complete. You will start receiving hydration reminders based on your preferences. "
            "Stay hydrated!"
        )
        bot.send_message(confirmation_message, self.command.settings.chat_id, message_id=telegram_update.message_id)
        self.command.finish(self.name, telegram_update)
