"""
Конфигурация приложения для мониторинга сайтов
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки Telegram бота
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Прокси для связи с Telegram. Нужен, если api.telegram.org недоступен
# с сервера напрямую. Формат: http://host:port или socks5://user:pass@host:port
# Пусто - идем напрямую. На проверки сайтов не влияет: они всегда идут с сервера
TELEGRAM_PROXY_URL = os.getenv('TELEGRAM_PROXY_URL') or None

# Таймауты соединения с Telegram в секундах. По умолчанию библиотека дает 5 с,
# чего не хватает на медленном канале или через прокси
CONNECT_TIMEOUT = float(os.getenv('CONNECT_TIMEOUT', 20))
READ_TIMEOUT = float(os.getenv('READ_TIMEOUT', 20))

# Настройки мониторинга
CHECK_INTERVAL_HOURS = int(os.getenv('CHECK_INTERVAL_HOURS', 6))  # Интервал проверки в часах
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))  # Таймаут HTTP запроса в секундах
FIRST_CHECK_DELAY_SECONDS = int(os.getenv('FIRST_CHECK_DELAY_SECONDS', 60))  # Задержка первой проверки после старта

# Настройки детекции изменений
MIN_CONTENT_LENGTH = int(os.getenv('MIN_CONTENT_LENGTH', 100))  # Минимальная длина контента

# Настройки порога значительных изменений
SIGNIFICANT_CHANGE_THRESHOLD = float(os.getenv('SIGNIFICANT_CHANGE_THRESHOLD', 0.15))  # 15% - порог изменений
MIN_CHANGED_CHARS = int(os.getenv('MIN_CHANGED_CHARS', 50))  # Минимум измененных символов
MAX_LENGTH_CHANGE_RATIO = float(os.getenv('MAX_LENGTH_CHANGE_RATIO', 0.30))  # 30% - изменение длины

# Пути к файлам
SITES_DATABASE_FILE = os.getenv('SITES_DATABASE_FILE', 'data/sites.json')  # Файл с базой сайтов
SNAPSHOTS_DIR = os.getenv('SNAPSHOTS_DIR', 'data/snapshots')  # Снимки контента сайтов
LOG_FILE = os.getenv('LOG_FILE', 'logs/monitor.log')  # Файл логов
