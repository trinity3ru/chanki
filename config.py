"""
Конфигурация приложения для мониторинга сайтов

Дополнено:
- Поддержка пользовательского интервала проверки через settings.json
- Геттер/сеттер для интервала с валидацией (1..168 часов)

Обоснование изменений:
- Переменные окружения нельзя изменять в рантайме из бота, поэтому используем
  небольшой JSON-файл настроек рядом с базой (простой и надёжный способ хранить
  глобальные настройки без изменения структуры sites.json).
"""
import os
import json
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки Telegram бота
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Настройки мониторинга
# Базовое значение из окружения (используется как дефолт, если settings.json отсутствует)
CHECK_INTERVAL_HOURS = int(os.getenv('CHECK_INTERVAL_HOURS', 6))  # Интервал проверки в часах
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))  # Таймаут HTTP запроса в секундах
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))  # Максимальное количество попыток при ошибке

# Настройки детекции изменений
CONTENT_HASH_ALGORITHM = os.getenv('CONTENT_HASH_ALGORITHM', 'sha256')  # Алгоритм хеширования
MIN_CONTENT_LENGTH = int(os.getenv('MIN_CONTENT_LENGTH', 100))  # Минимальная длина контента

# Настройки порога значительных изменений
SIGNIFICANT_CHANGE_THRESHOLD = float(os.getenv('SIGNIFICANT_CHANGE_THRESHOLD', 0.15))  # 15% - порог изменений
MIN_CHANGED_CHARS = int(os.getenv('MIN_CHANGED_CHARS', 50))  # Минимум измененных символов
MAX_LENGTH_CHANGE_RATIO = float(os.getenv('MAX_LENGTH_CHANGE_RATIO', 0.30))  # 30% - изменение длины

# Пути к файлам
SITES_DATABASE_FILE = os.getenv('SITES_DATABASE_FILE', 'sites.json')  # Файл с базой сайтов
LOG_FILE = os.getenv('LOG_FILE', 'logs/monitor.log')  # Файл логов
SETTINGS_FILE = os.getenv('SETTINGS_FILE', 'settings.json')  # Файл пользовательских настроек

# Настройки уведомлений
NOTIFICATION_RETRY_DELAY = 300  # Задержка между повторными уведомлениями в секундах (5 минут)

# ------------------- Работа с settings.json -------------------
def _load_settings() -> dict:
    """
    Загружает словарь настроек из SETTINGS_FILE.

    Возвращает пустой словарь при отсутствии файла или ошибке парсинга.
    Это защищает приложение от повреждения настроек и позволяет работать
    с дефолтами без падений.
    """
    try:
        if not os.path.exists(SETTINGS_FILE) or os.path.getsize(SETTINGS_FILE) == 0:
            return {}
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except Exception:
        # Не бросаем исключение: при проблемах с файлом просто используем дефолты
        return {}


def _save_settings(settings: dict) -> None:
    """
    Безопасно сохраняет словарь настроек в SETTINGS_FILE.

    Создаёт директорию при необходимости. Пишет в UTF-8 с отступами.
    """
    try:
        settings_dir = os.path.dirname(SETTINGS_FILE)
        if settings_dir:
            os.makedirs(settings_dir, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        # Нам важно не падать в рантайме бота из-за проблем с записью настроек
        pass


def get_check_interval_hours() -> int:
    """
    Возвращает актуальный интервал проверки в часах.

    Порядок приоритета:
    1) settings.json -> "check_interval_hours" (валидные 1..168)
    2) Переменная окружения CHECK_INTERVAL_HOURS (дефолт 6)

    Returns:
        int: интервал в часах в пределах [1, 168]
    """
    settings = _load_settings()
    value = settings.get('check_interval_hours')
    try:
        value_int = int(value)
        if 1 <= value_int <= 168:
            return value_int
    except Exception:
        pass
    # Фоллбэк к модульной константе, но тоже валидируем
    try:
        env_value = int(CHECK_INTERVAL_HOURS)
        if 1 <= env_value <= 168:
            return env_value
    except Exception:
        pass
    return 6


def set_check_interval_hours(hours: int) -> bool:
    """
    Сохраняет новый интервал проверки в SETTINGS_FILE и обновляет модульную
    переменную CHECK_INTERVAL_HOURS. Предназначено для вызова из команды бота.

    Args:
        hours (int): Новый интервал в часах (1..168)

    Returns:
        bool: True если сохранение прошло успешно, False при неверном значении
              (ошибки записи игнорируются намеренно, чтобы бот не падал)
    """
    try:
        hours_int = int(hours)
    except Exception:
        return False

    if not (1 <= hours_int <= 168):
        return False

    settings = _load_settings()
    settings['check_interval_hours'] = hours_int
    _save_settings(settings)

    # Обновляем модульную переменную, чтобы новые обращения видели актуальное значение
    global CHECK_INTERVAL_HOURS
    CHECK_INTERVAL_HOURS = hours_int
    return True

