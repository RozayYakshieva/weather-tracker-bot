import os
import sys
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    print("\nОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
    sys.exit(1)
if not OPENWEATHER_API_KEY:
    print("\nОШИБКА: OPENWEATHER_API_KEY не найден!")
    sys.exit(1)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    from app.api.weather import WeatherAPI
    weather_api = WeatherAPI(api_key=OPENWEATHER_API_KEY)

except ImportError as e:
    print(f"\nОШИБКА WeatherAPI: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\nОШИБКА WeatherAPI: {e}")
    sys.exit(1)

def format_weather_message(weather_data: dict) -> str:
    """Форматировать данные о погоде"""
    if not weather_data:
        return "❌ Не удалось получить данные о погоде"

    # Эмодзи для разных типов погоды
    weather_desc = weather_data["weather"].lower()
    emoji = "🌤️"
    if "ясно" in weather_desc or "clear" in weather_desc:
        emoji = "☀"
    elif "облачно" in weather_desc or "clouds" in weather_desc:
        emoji = "☁"
    elif "дождь" in weather_desc or "rain" in weather_desc:
        emoji = "🌧️"
    elif "снег" in weather_desc or "snow" in weather_desc:
        emoji = "❄"
    elif "гроза" in weather_desc or "thunderstorm" in weather_desc:
        emoji = "⛈"
    elif "туман" in weather_desc or "mist" in weather_desc or "fog" in weather_desc:
        emoji = "🌫️"

    message = (
        f"{emoji} *{weather_data['city']}, {weather_data['country']}*\n\n"
        f"🌡️ *Температура:* {weather_data['temperature']:.1f}°C\n"
        f"🤏 *Ощущается как:* {weather_data['feels_like']:.1f}°C\n"
        f"💧 *Влажность:* {weather_data['humidity']}%\n"
        f"🎈 *Давление:* {weather_data['pressure']} гПа\n"
        f"💨 *Ветер:* {weather_data['wind_speed']} м/с, {weather_data['wind_direction']}\n"
        f"☁ *Облачность:* {weather_data['clouds']}%\n"
    )

    # Добавляем восход/закат если есть
    if weather_data.get('sunrise') and weather_data.get('sunset'):
        from datetime import datetime
        sunrise = datetime.fromtimestamp(weather_data['sunrise']).strftime('%H:%M')
        sunset = datetime.fromtimestamp(weather_data['sunset']).strftime('%H:%M')
        message += f"🌅 *Восход:* {sunrise}\n 🌇 *Закат:* {sunset}\n"

    message += f"📝 *Описание:* {weather_data['weather']}\n"

    return message


def format_forecast_message(forecast_data: dict) -> str:
    """Форматировать прогноз погоды"""
    if not forecast_data:
        return "❌ Не удалось получить прогноз погоды"

    message = f"*Прогноз погоды в {forecast_data['city']}, {forecast_data['country']}*\n\n"

    for day in forecast_data['forecast']:
        # Определяем эмодзи для погоды
        weather_desc = day['weather'].lower()
        emoji = "🌤️"
        if "ясно" in weather_desc or "clear" in weather_desc:
            emoji = "☀"
        elif "облачно" in weather_desc or "clouds" in weather_desc:
            emoji = "☁"
        elif "дождь" in weather_desc or "rain" in weather_desc:
            emoji = "🌧️"
        elif "снег" in weather_desc or "snow" in weather_desc:
            emoji = "❄"
        elif "гроза" in weather_desc or "thunderstorm" in weather_desc:
            emoji = "⛈"
        elif "туман" in weather_desc or "mist" in weather_desc or "fog" in weather_desc:
            emoji = "🌫️"

        # Форматируем дату (дд.мм)
        date_parts = day['date'].split('-')
        formatted_date = f"{date_parts[2]}.{date_parts[1]}"

        message += (
            f"*{formatted_date} ({day['day_name']})* {emoji}\n"
            f"🌡️ {day['temp_min']:.0f}°...{day['temp_max']:.0f}°C\n"
            f"💧 Влажность: {day['humidity']}%\n"
            f"💨 Ветер: {day['wind_speed']} м/с\n"
            f"📝 {day['weather'].capitalize()}\n\n"
        )

    return message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = (
        f"Привет, {user.first_name}!\n\n"
        f"☀ *Я бот погоды*\n\n"
        f"*Что я умею:*\n"
        f"• Показывать текущую погоду в любом городе\n"
        f"• Показывать прогноз на 5 дней\n"
        f"• Отправлять уведомления об изменениях погоды\n\n"
        f"*Как использовать:*\n"
        f"1. Напишите название города (например, 'Москва')\n"
        f"2. Или используйте команды:\n"
        f"   /weather <город> - текущая погода\n"
        f"   /forecast <город> - прогноз на 5 дней\n"
        f"   /help - справка\n\n"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    logger.info(f"Пользователь {user.id} начал работу с ботом")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "🆘 *Помощь по боту погоды*\n\n"
        "📋 *Доступные команды:*\n"
        "• /start - Начать работу с ботом\n"
        "• /help - Показать справку\n"
        "• /weather <город> - Текущая погода в городе\n"
        "• /forecast <город> - Прогноз на 5 дней\n\n"
        "📍 *Примеры использования:*\n"
        "• /weather Москва\n"
        "• /forecast Санкт-Петербург\n"
        "• Просто отправьте 'Лондон' или 'London'\n\n"
        "🌍 *Поддерживаются города со всего мира!*\n"
        "Для городов с одинаковыми названиями укажите страну:\n"
        "• London,uk\n"
        "• London,ca\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /weather"""
    if not context.args:
        await update.message.reply_text(
            "📍 *Укажите город после команды:*\n\n"
            "*Пример:*\n"
            "• /weather Москва\n"
            "Или просто отправьте название города",
            parse_mode='Markdown'
        )
        return

    city = " ".join(context.args)
    await update.message.reply_chat_action(action="typing")

    logger.info(f"Запрос погоды для города: {city}")

    # Получаем данные о погоде
    weather_data = weather_api.get_current_weather(city)

    if weather_data:
        message = format_weather_message(weather_data)
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            f"❌ Не удалось получить погоду для города '{city}'.\n\n"
            f"*Возможные причины:*\n"
            f"• Неправильное написание города\n"
            f"• Город не найден в базе OpenWeatherMap\n"
            f"• Проблемы с подключением к интернету\n\n"
            f"*Попробуйте:*\n"
            f"• Проверить написание\n"
            f"• Указать страну: 'London,uk'\n"
            f"• Попробовать другой город",
            parse_mode='Markdown'
        )


async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /forecast"""
    if not context.args:
        await update.message.reply_text(
            "📍 *Укажите город после команды:*\n\n"
            "*Пример:*\n"
            "/forecast Москва",
            parse_mode='Markdown'
        )
        return

    city = " ".join(context.args)
    await update.message.reply_chat_action(action="typing")

    logger.info(f"Запрос прогноза для города: {city}")

    # Получаем прогноз погоды
    forecast_data = weather_api.get_forecast(city)

    if forecast_data:
        message = format_forecast_message(forecast_data)
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            f"❌ Не удалось получить прогноз для города '{city}'.\n"
            f"Проверьте правильность написания.",
            parse_mode='Markdown'
        )


async def handle_city_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений (названия городов)"""
    city = update.message.text.strip()

    if len(city) < 2:
        await update.message.reply_text("📍 Пожалуйста, укажите название города (минимум 2 символа)")
        return

    context.args = [city]
    await weather_command(update, context)


def main():
    """Основная функция запуска бота"""
    print("\n" + "=" * 50)
    print("ЗАПУСК ТЕЛЕГРАМ БОТА")
    print("=" * 50)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("forecast", forecast_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_message))

    print("Бот запускается...")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 50 + "\n")

    app.run_polling()


if __name__ == "__main__":
    main()