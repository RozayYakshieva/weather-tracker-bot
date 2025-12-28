import logging
import asyncio
from datetime import datetime
from app.api.weather import WeatherAPI
from app.database.db import get_db_connection

logger = logging.getLogger(__name__)


class JobQueueNotifier:
    def __init__(self):
        self.weather_api = WeatherAPI()
        logger.info("JobQueueNotifier инициализирован")

    async def send_weather_notification(self, bot, chat_id: int, city: str):
        try:
            weather_data = self.weather_api.get_current_weather(city)
            if weather_data:
                message = (
                    f"⏰ *{weather_data['city']}, {weather_data.get('country', '')}*\n\n"
                    f"🌡️ Температура: *{weather_data['temperature']:.1f}°C*\n"
                    f"🤏 Ощущается как: *{weather_data['feels_like']:.1f}°C*\n"
                    f"💧 Влажность: *{weather_data['humidity']}%*\n"
                    f"💨 Ветер: *{weather_data['wind_speed']} м/с*\n"
                    f"📝 *{weather_data['weather']}*\n\n"
                    f"Хорошего дня! ☀"
                )

                await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )

                logger.info(f"Уведомление отправлено в {chat_id} для {city}")
                return True

        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
            return False

    async def check_and_send_notifications(self, context):
        try:
            current_time = datetime.now().strftime("%H:%M")
            logger.debug(f"Проверка уведомления для времени {current_time}")

            conn = get_db_connection()
            if not conn:
                return

            cur = conn.cursor()
            cur.execute("""
                SELECT u.telegram_id, s.city, s.notification_time
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                WHERE s.notification_time = %s
            """, (current_time,))

            subscriptions = cur.fetchall()
            cur.close()
            conn.close()

            if not subscriptions:
                logger.debug(f"Нет подписок на время {current_time}")
                return

            logger.info(f"Найдено {len(subscriptions)} подписок на {current_time}")

            for telegram_id, city, _ in subscriptions:
                await self.send_weather_notification(context.bot, telegram_id, city)
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Ошибка проверки уведомлений: {e}")

    def start(self, application):
        if not application.job_queue:
            logger.error("JobQueue не доступен")
            return False

        application.job_queue.run_repeating(
            callback=self.check_and_send_notifications,
            interval=60,
            first=10
        )

        logger.info("JobQueueNotifier запущен")
        return True


_notifier = JobQueueNotifier()


def get_notifier():
    return _notifier


def start_notifier(application):
    return _notifier.start(application)