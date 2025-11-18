"""Start command for Telegram bot."""

from django.contrib.auth import get_user_model
from django_telegram_app import get_telegram_settings_model
from django_telegram_app.bot import bot
from django_telegram_app.bot.base import TelegramUpdate

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
            AskUserField(self, "username", unique_id="ask_username"),
            AskUserField(self, "first_name", unique_id="ask_first_name"),
            AskUserField(self, "last_name", unique_id="ask_last_name"),
            AskUserField(self, "email", unique_id="ask_email"),
            AskTelegramSettingsField(self, "daily_goal", unique_id="ask_daily_goal"),
            AskTelegramSettingsField(self, "reminder_window_start", unique_id="ask_reminder_window_start"),
            AskTelegramSettingsField(self, "reminder_window_end", unique_id="ask_reminder_window_end"),
            AskTelegramSettingsField(self, "consumption_size", unique_id="ask_consumption_size"),
            AskTelegramSettingsField(self, "default_postpone", unique_id="ask_default_postpone"),
            AskTelegramSettingsField(self, "minimum_interval", unique_id="ask_minimum_interval"),
            AskTelegramSettingsField(self, "reminder_text", unique_id="ask_reminder_text"),
            ConfirmStart(self, unique_id="confirm_start"),
        ]


class WelcomeStep(TelegramStep):
    """Step to welcome the user."""

    def handle(self, telegram_update: TelegramUpdate):
        """Greet the user and advance to the next step."""
        # Check if telegram settings already exist
        TelegramSettingsModel = get_telegram_settings_model()
        existing_settings = TelegramSettingsModel.objects.filter(chat_id=telegram_update.chat_id).exists()
        if existing_settings:
            bot.send_message(
                "You have already completed the setup. Use /help to see available commands.",
                self.command.settings.chat_id,
                message_id=telegram_update.message_id,
            )
            self.command.finish(self.name, telegram_update)
            return
        greeting = (
            "Welcome to H2Oh! I am here to help you track and maintain your daily water intake. "
            "Let's get started with setting up your preferences."
        )
        bot.send_message(greeting, self.command.settings.chat_id, message_id=telegram_update.message_id)
        self.command.next_step(self.name, telegram_update)


class AskModelField(TelegramStep):
    """Step to ask the user a value for a model field."""

    def __init__(self, command, field_name: str, steps_back=0, unique_id=None):
        """Initialize the AskUserData step."""
        UserModel = get_user_model()
        self.field_name = field_name
        self.field = UserModel._meta.get_field(self.field_name)
        self.prompt = f"Please provide your {self.field.verbose_name}.\n{self.field.help_text}"
        super().__init__(command, steps_back=steps_back, unique_id=unique_id)

    def handle(self, telegram_update: TelegramUpdate):
        """Prepare any data needed for the Ask step."""
        data = self.get_callback_data(telegram_update)
        self.add_waiting_for(self.field_name, data)
        reply_markup = None
        if self.field.blank:
            skip_options = {**data, self.field_name: ""}
            keyboard = [[{"text": "Skip", "callback_data": self.next_step_callback(**skip_options)}]]
            reply_markup = {"inline_keyboard": keyboard}
        bot.send_message(
            self.prompt,
            self.command.settings.chat_id,
            reply_markup=reply_markup,
            message_id=telegram_update.message_id,
        )

    def get_model(self):
        """Return the model class for the field."""
        raise NotImplementedError("Subclasses must implement get_model method.")


class AskUserField(AskModelField):
    """Step to ask the user for a User model field."""

    def get_model(self):
        """Return the User model class."""
        return get_user_model()


class AskTelegramSettingsField(AskModelField):
    """Step to ask the user for a TelegramSettings field."""

    def get_model(self):
        """Return the TelegramSettings model class."""
        return get_telegram_settings_model()


class AskConfirmation(TelegramStep):
    """Step to ask the user for confirmation."""

    def handle(self, telegram_update: TelegramUpdate):
        """Prepare any data needed for the Ask step."""
        data = self.get_callback_data(telegram_update)
        keyboard = [
            [
                {"text": "✅ Yes", "callback_data": self.next_step_callback(**{**data, "confirmation": "yes"})},
                {"text": "⛔️ No", "callback_data": self.cancel_callback(**{**data, "confirmation": "no"})},
            ]
        ]
        reply_markup = {"inline_keyboard": keyboard}

        username = data.get("username")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        daily_goal = data.get("daily_goal")
        reminder_window_start = data.get("reminder_window_start")
        reminder_window_end = data.get("reminder_window_end")
        consumption_size = data.get("consumption_size")
        default_postpone = data.get("default_postpone")
        minimum_interval = data.get("minimum_interval")
        reminder_text = data.get("reminder_text")
        prompt = (
            "Are these settings correct?\n"
            f" - Username: {username}\n"
            f" - First name: {first_name}\n"
            f" - Last name: {last_name}\n"
            f" - Email: {email}\n"
            f" - Daily goal (ml): {daily_goal}\n"
            f" - Reminder window start: {reminder_window_start}\n"
            f" - Reminder window end: {reminder_window_end}\n"
            f" - Consumption size (ml): {consumption_size}\n"
            f" - Default postpone (seconds): {default_postpone}\n"
            f" - Minimum interval (seconds): {minimum_interval}\n"
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
        confirmation_message = (
            "Thank you! Your setup is now complete. You will start receiving hydration reminders based on your preferences. "
            "Stay hydrated!"
        )
        bot.send_message(confirmation_message, self.command.settings.chat_id, message_id=telegram_update.message_id)
        self.command.finish(self.name, telegram_update)
