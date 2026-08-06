"""
Главный файл приложения для мониторинга сайтов
Объединяет все модули и запускает систему мониторинга
"""
import os
import sys
import logging
from datetime import datetime
from telegram.error import NetworkError
import config
from telegram_bot import SiteMonitorBot
from scheduler import MonitoringScheduler

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class RedactingFormatter(logging.Formatter):
    """
    Форматтер, вырезающий секреты из сообщений и трейсбеков

    Библиотеки охотно печатают в тексте ошибок и токен бота, и URL прокси
    вместе с паролем. В логах, которые потом копируют в переписку, им не место.
    """

    def __init__(self, fmt: str, secrets):
        """
        Args:
            fmt (str): Формат строки лога
            secrets: Строки, которые нужно скрыть
        """
        super().__init__(fmt)
        # Длинные вперед: иначе короткий секрет испортит вхождение длинного
        self._secrets = sorted(
            {s for s in secrets if s and len(s) > 3}, key=len, reverse=True
        )

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for secret in self._secrets:
            message = message.replace(secret, '***')
        return message


def collect_secrets():
    """
    Собирает строки, которые нельзя показывать в логах

    Returns:
        list: Токен бота, URL прокси и его учетные данные
    """
    secrets = [config.TELEGRAM_BOT_TOKEN]

    if config.TELEGRAM_PROXY_URL:
        secrets.append(config.TELEGRAM_PROXY_URL)

        # Отдельно логин:пароль и сам пароль - они могут всплыть без URL
        userinfo = config.TELEGRAM_PROXY_URL.partition('://')[2].rpartition('@')[0]
        if userinfo:
            secrets.append(userinfo)
            if ':' in userinfo:
                secrets.append(userinfo.split(':', 1)[1])

    return secrets


class SiteMonitoringApp:
    """
    Главный класс приложения для мониторинга сайтов
    """

    def __init__(self):
        """Инициализация приложения"""
        self.setup_logging()
        self.logger = logging.getLogger(__name__)

        self.logger.info("Инициализация приложения мониторинга сайтов...")

        # Инициализируем компоненты. База и монитор живут внутри бота,
        # планировщик переиспользует их же экземпляры
        try:
            self.bot = SiteMonitorBot()
            self.scheduler = MonitoringScheduler(self.bot)

            self.logger.info("Все компоненты успешно инициализированы")

        except Exception as e:
            self.logger.error(f"Ошибка при инициализации: {str(e)}")
            sys.exit(1)

    def setup_logging(self):
        """Настройка системы логирования"""
        # Создаем директорию для логов если её нет
        log_dir = os.path.dirname(config.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except PermissionError:
                # Если не можем создать директорию, используем текущую
                pass

        # Пытаемся создать FileHandler, если не получается - используем только консоль
        handlers = [logging.StreamHandler(sys.stdout)]

        try:
            handlers.append(logging.FileHandler(config.LOG_FILE, encoding='utf-8'))
        except (PermissionError, FileNotFoundError):
            # Если не можем записать в файл, продолжаем только с консольным выводом
            print(f"⚠️ Не удалось создать лог-файл {config.LOG_FILE}, используем только консольный вывод")

        # Формат ставим до basicConfig: он не трогает handlers, у которых
        # форматтер уже задан
        formatter = RedactingFormatter(LOG_FORMAT, collect_secrets())
        for handler in handlers:
            handler.setFormatter(formatter)

        logging.basicConfig(level=logging.INFO, handlers=handlers)

    def startup(self):
        """Запуск приложения"""
        try:
            self.logger.info("Запуск приложения мониторинга сайтов...")

            # Проверяем конфигурацию
            if not config.TELEGRAM_BOT_TOKEN:
                raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле")

            # Сначала собираем приложение бота, затем вешаем на него
            # периодическую задачу - job_queue живет внутри приложения
            application = self.bot.build()
            self.scheduler.register(application)

            # run_polling блокирует поток до сигнала остановки и сам
            # корректно гасит бота вместе с планировщиком
            self.logger.info("Запуск телеграм бота...")
            self.bot.run()

            self.logger.info("Приложение корректно завершено")

        except NetworkError as e:
            # Самая частая причина - Telegram недоступен с этого сервера
            self.logger.error(
                f"Не удалось связаться с Telegram ({type(e).__name__}: {e}). "
                f"Проверьте доступность API с сервера: "
                f"curl -sS --max-time 15 https://api.telegram.org "
                f"Если он блокируется, задайте TELEGRAM_PROXY_URL в .env"
            )
            sys.exit(1)

        except Exception as e:
            # Полный трейсбек: без типа исключения причину не отличить
            self.logger.exception(f"Ошибка при запуске: {type(e).__name__}: {e}")
            sys.exit(1)

def main():
    """Главная функция приложения"""
    print("🚀 Запуск приложения мониторинга сайтов...")
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ Интервал проверки: каждые {config.CHECK_INTERVAL_HOURS} часов")
    print(f"📁 База данных: {config.SITES_DATABASE_FILE}")
    print(f"📝 Логи: {config.LOG_FILE}")
    print("=" * 60)

    # Создаем и запускаем приложение
    app = SiteMonitoringApp()
    app.startup()

if __name__ == "__main__":
    main()
