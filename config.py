"""
Конфигурация приложения для мониторинга сайтов
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки Telegram бота
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Настройки мониторинга
CHECK_INTERVAL_HOURS = 6  # Интервал проверки в часах
REQUEST_TIMEOUT = 10  # Таймаут HTTP запроса в секундах
MAX_RETRIES = 3  # Максимальное количество попыток при ошибке

# Настройки детекции изменений
CONTENT_HASH_ALGORITHM = 'sha256'  # Алгоритм хеширования для детекции изменений
MIN_CONTENT_LENGTH = 100  # Минимальная длина контента для валидации

# Пути к файлам
SITES_DATABASE_FILE = 'sites.json'  # Файл с базой сайтов
LOG_FILE = 'monitor.log'  # Файл логов

# Настройки уведомлений
NOTIFICATION_RETRY_DELAY = 300  # Задержка между повторными уведомлениями в секундах (5 минут)

