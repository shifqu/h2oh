"""Overview command for Telegram bot."""

from django_telegram_app.bot import bot
from django_telegram_app.bot.base import TelegramUpdate

from apps.telegram.telegrambot.base import TelegramCommand, TelegramStep


class Command(TelegramCommand):
    """Overview command to display today's water consumption."""

    description = "Show an overview of today's water consumption."

    @property
    def steps(self):
        """Return the steps of the command."""
        return [ShowOverview(self)]


class ShowOverview(TelegramStep):
    """Step to show today's water consumption overview."""

    def handle(self, telegram_update: TelegramUpdate):
        """Handle showing the overview."""
        if not self.command.settings.is_initialized:
            self.send_not_initialized_message(telegram_update)
            return

        consumed = self.command.settings.consumed_today_ml
        goal = self.command.settings.daily_goal_ml
        msg = (
            f"💧 Today's Water Consumption Overview:\n\n"
            f"You have consumed {consumed}ml out of your daily goal of {goal}ml."
        )
        if consumed >= goal:
            msg += "\n\n🎉 Congratulations! You've met your daily hydration goal!"
        elif consumed >= 0.8 * goal:
            msg += "\n\n👍 You've **almost** met your daily hydration goal!"
        else:
            msg += "\n\n🚰 Keep drinking water to reach your goal!"

        bot.send_message(
            msg,
            self.command.settings.chat_id,
            message_id=telegram_update.message_id,
        )
        self.command.next_step(self.name, telegram_update)
