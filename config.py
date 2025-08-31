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
CHECK_INTERVAL_HOURS = 3  # Интервал проверки в часах
REQUEST_TIMEOUT = 10  # Таймаут HTTP запроса в секундах
MAX_RETRIES = 3  # Максимальное количество попыток при ошибке

# Настройки детекции изменений
CONTENT_HASH_ALGORITHM = 'sha256'  # Алгоритм хеширования для детекции изменений
MIN_CONTENT_LENGTH = 100  # Минимальная длина контента для валидации

# Настройки порога значительных изменений
SIGNIFICANT_CHANGE_THRESHOLD = 0.15  # 15% - минимальный процент изменений для уведомления
MIN_CHANGED_CHARS = 50  # Минимальное количество измененных символов
MAX_LENGTH_CHANGE_RATIO = 0.30  # 30% - максимальное изменение длины контента

# Пути к файлам
SITES_DATABASE_FILE = 'sites.json'  # Файл с базой сайтов
LOG_FILE = 'monitor.log'  # Файл логов

# Настройки уведомлений
NOTIFICATION_RETRY_DELAY = 300  # Задержка между повторными уведомлениями в секундах (5 минут)

