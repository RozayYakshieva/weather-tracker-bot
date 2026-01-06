import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

from app.bot.handlers import start, subscribe_command, mysubs_command


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = User(id=12345, is_bot=False, first_name="Alice", username="alice")
    update.message = MagicMock(spec=Message)
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat.id = 67890
    update.message.reply_text = AsyncMock()
    update.message.text = ""
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context


@pytest.mark.asyncio
@patch("app.bot.handlers.db.add_user")
@patch("app.bot.handlers.db.add_subscription")
@patch("app.bot.handlers.WeatherAPI")
async def test_full_user_subscription_flow(
    mock_weather_api,
    mock_add_subscription,
    mock_add_user,
    mock_update,
    mock_context
):
    """
    Пользовательский сценарий:
    1. /start — регистрация
    2. /subscribe Москва 08:30 — создание подписки
    3. /mysubs — проверка, что подписка отображается
    """
    # === Шаг 1: /start ===
    await start(mock_update, mock_context)
    mock_add_user.assert_called_once_with(telegram_id=12345, username="alice", first_name="Alice")

    # === Шаг 2: /subscribe Москва 08:30 ===
    mock_context.args = ["Москва", "08:30"]
    mock_weather_api.return_value.get_current_weather.return_value = {"city": "Москва"}
    mock_add_subscription.return_value = 101

    await subscribe_command(mock_update, mock_context)

    mock_add_subscription.assert_called_once_with(12345, "Москва", "08:30")
    reply_text = mock_update.message.reply_text.await_args[0][0]
    assert "✅ *Подписка создана!*" in reply_text
    assert "`101`" in reply_text

    # === Шаг 3: /mysubs ===
    mock_context.args = []
    with patch("app.bot.handlers.db.get_user_subscriptions") as mock_get_subs:
        mock_get_subs.return_value = [(101, "Москва", "08:30")]

        await mysubs_command(mock_update, mock_context)

        mock_get_subs.assert_called_once_with(12345)
        reply_text = mock_update.message.reply_text.await_args[0][0]
        assert "Москва" in reply_text
        assert "08:30" in reply_text
        assert "`101`" in reply_text