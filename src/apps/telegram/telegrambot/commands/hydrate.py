"""Hydrate command for Telegram bot."""

from django.utils.translation import gettext as _
from django_telegram_app.bot import bot
from django_telegram_app.bot.base import TelegramUpdate

from apps.telegram.telegrambot.base import TelegramCommand, TelegramStep


class Command(TelegramCommand):
    """Hydrate command to log water consumption."""

    description = _("Log water consumption for the user.")

    @property
    def steps(self):
        """Return the steps of the command."""
        return [AskConsumptionSize(self), LogConsumption(self)]


class AskConsumptionSize(TelegramStep):
    """Step to ask for water consumption size."""

    def handle(self, telegram_update: TelegramUpdate):
        """Handle asking for water consumption size."""
        if not self.command.settings.is_initialized:
            self.send_not_initialized_message(telegram_update)
            return

        data = self.get_callback_data(telegram_update)
        prompt = _("Please provide your consumption size (ml) or click the button to use the default.")
        if "_error" in data:
            prompt = f"{data.pop('_error')}\n\n{prompt}"

        self.add_waiting_for("consumption_size_ml", data)

        default_callback = self.next_step_callback(data, consumption_size_ml=self.command.settings.consumption_size_ml)
        keyboard = [[{"text": f"{self.command.settings.consumption_size_ml}ml", "callback_data": default_callback}]]

        bot.send_message(
            prompt,
            self.command.settings.chat_id,
            reply_markup={"inline_keyboard": keyboard},
            message_id=telegram_update.message_id,
        )


class LogConsumption(TelegramStep):
    """Step to log water consumption."""

    def handle(self, telegram_update: TelegramUpdate):
        """Handle logging the water consumption."""
        data = self.get_callback_data(telegram_update)
        consumption_size = data["consumption_size_ml"]
        try:
            consumption_size_ml = int(consumption_size)
        except (TypeError, ValueError) as exc:
            error_message = _("Invalid input for {consumption_size}: {error}.").format(
                consumption_size=consumption_size, error=exc
            )

            telegram_update.callback_data = self.previous_step_callback(1, data, _error=error_message)
            self.command.previous_step(self.name, telegram_update)
            return

        self.command.settings.consumed_today_ml += consumption_size_ml
        self.command.settings.next_reminder_at = self.command.settings.compute_next_reminder_datetime()
        self.command.settings.save()
        data = self.get_callback_data(telegram_update)
        msg = _(
            "Logged {consumption_size_ml}ml of water! 💧\n\n"
            "Total consumed today: {consumed_today_ml}ml/{daily_goal_ml}ml.\n\n"
            "Next reminder scheduled at {next_reminder_at} local time."
        ).format(
            consumption_size_ml=consumption_size_ml,
            consumed_today_ml=self.command.settings.consumed_today_ml,
            daily_goal_ml=self.command.settings.daily_goal_ml,
            next_reminder_at=self.command.settings.get_next_reminder_at_display(),
        )
        bot.send_message(
            msg,
            self.command.settings.chat_id,
            message_id=telegram_update.message_id,
        )
        self.command.next_step(self.name, telegram_update)
