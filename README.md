# Weather Tracker Bot

Telegram bot for weather tracking with personal settings.

## Team
- Роза Якшиева, группа 5130904/30104
- Лопатина Софья, группа 5130904/30104
- Воробьева Алена, группа 5130904/30104

## Technology Stack
- Python + FastAPI
- PostgreSQL
- Telegram Bot
- OpenWeatherMap API

## Сборка и запуск

> **Требования**: установленные **Docker** и **docker-compose**.
# 1. Сборка проекта
```bash
docker-compose build

# 2. Unit-тесты
docker-compose run --rm bot pytest tests/unit

# 3. Интеграционные тесты
docker-compose run --rm bot pytest tests/integration

# 4. Запуск приложения
docker-compose up bot
