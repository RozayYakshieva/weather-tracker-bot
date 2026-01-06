# tests/unit/bot/test_bot.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

# Импортируем твои обработчики
from app.bot.handlers import (
    start,
    weather_command,
    handle_city_message,
    subscribe_command,
    mysubs_command,
    unsubscribe_command
)


@pytest.fixture
def mock_update():
    """Создаём mock-объект Update для тестов"""
    update = MagicMock(spec=Update)
    update.effective_user = User(id=12345, is_bot=False, first_name="TestUser", username="testuser")
    update.message = MagicMock(spec=Message)
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat.id = 67890
    update.message.reply_text = AsyncMock()
    update.message.reply_chat_action = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Создаём mock-объект Context"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context


# === Тесты ===

@pytest.mark.asyncio
@patch("app.bot.handlers.db.add_user")
async def test_start_command(mock_add_user, mock_update, mock_context):
    await start(mock_update, mock_context)

    mock_add_user.assert_called_once_with(
        telegram_id=12345,
        username="testuser",
        first_name="TestUser"
    )
    mock_update.message.reply_text.assert_awaited()
    assert "Привет, TestUser!" in mock_update.message.reply_text.await_args[0][0]


@pytest.mark.asyncio
@patch("app.bot.handlers.WeatherAPI")
async def test_weather_command_success(mock_weather_api, mock_update, mock_context):
    mock_context.args = ["Москва"]
    mock_api_instance = mock_weather_api.return_value
    mock_api_instance.get_current_weather.return_value = {
        "city": "Москва",
        "country": "RU",
        "temperature": 15.5,
        "feels_like": 14.2,
        "humidity": 60,
        "wind_speed": 3.5,
        "weather": "Пасмурно"
    }

    await weather_command(mock_update, mock_context)

    mock_api_instance.get_current_weather.assert_called_once_with("Москва")
    mock_update.message.reply_chat_action.assert_awaited()
    mock_update.message.reply_text.assert_awaited()
    text = mock_update.message.reply_text.await_args[0][0]
    assert "Москва" in text
    assert "15.5°C" in text


@pytest.mark.asyncio
async def test_weather_command_no_args(mock_update, mock_context):
    await weather_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_awaited()
    text = mock_update.message.reply_text.await_args[0][0]
    assert "Укажите город после команды" in text


@pytest.mark.asyncio
@patch("app.bot.handlers.WeatherAPI")
async def test_handle_city_message_success(mock_weather_api, mock_update, mock_context):
    mock_update.message.text = "Санкт-Петербург"
    mock_api_instance = mock_weather_api.return_value
    mock_api_instance.get_current_weather.return_value = {
        "city": "Санкт-Петербург",
        "country": "RU",
        "temperature": 10.0,
        "feels_like": 9.5,
        "humidity": 70,
        "wind_speed": 4.0,
        "weather": "Дождь"
    }

    await handle_city_message(mock_update, mock_context)

    mock_api_instance.get_current_weather.assert_called_once_with("Санкт-Петербург")
    mock_update.message.reply_text.assert_awaited()
    text = mock_update.message.reply_text.await_args[0][0]
    assert "Санкт-Петербург" in text


@pytest.mark.asyncio
@patch("app.bot.handlers.WeatherAPI")
@patch("app.bot.handlers.db.add_subscription")
async def test_subscribe_command_success(mock_add_sub, mock_weather_api, mock_update, mock_context):
    mock_context.args = ["Москва", "08:30"]
    mock_weather_api.return_value.get_current_weather.return_value = {"city": "Москва"}
    mock_add_sub.return_value = 999

    await subscribe_command(mock_update, mock_context)

    mock_add_sub.assert_called_once_with(12345, "Москва", "08:30")
    mock_update.message.reply_text.assert_awaited()
    text = mock_update.message.reply_text.await_args[0][0]
    assert "✅ *Подписка создана!*" in text
    assert "`999`" in text


@pytest.mark.asyncio
@patch("app.bot.handlers.db.get_user_subscriptions")
async def test_mysubs_command(mock_get_subs, mock_update, mock_context):
    mock_get_subs.return_value = [(1, "Москва", "08:30"), (2, "СПб", "19:00")]

    await mysubs_command(mock_update, mock_context)

    mock_get_subs.assert_called_once_with(12345)
    mock_update.message.reply_text.assert_awaited()
    text = mock_update.message.reply_text.await_args[0][0]
    assert "Москва" in text
    assert "СПб" in text


@pytest.mark.asyncio
@patch("app.bot.handlers.db.delete_subscription")
async def test_unsubscribe_command_success(mock_delete, mock_update, mock_context):
    mock_context.args = ["1"]
    mock_delete.return_value = True

    await unsubscribe_command(mock_update, mock_context)

    mock_delete.assert_called_once_with(1)
    mock_update.message.reply_text.assert_awaited()
    text = mock_update.message.reply_text.await_args[0][0]
    assert "удалена" in text