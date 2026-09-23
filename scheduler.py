"""
Модуль планировщика задач для автоматической проверки сайтов
Запускает проверку каждые CHECK_INTERVAL_HOURS часов и отправляет уведомления в Telegram

Планировщик работает на job_queue из python-telegram-bot, то есть в том же
event loop, что и сам бот. Отдельный поток не нужен, и отправка уведомлений
не упирается в чужой event loop.
"""
import asyncio
import logging
from typing import Dict, List, Optional
from telegram.ext import Application, ContextTypes
import config
from telegram_bot import SiteMonitorBot, split_message

JOB_NAME = 'site-monitoring'

class MonitoringScheduler:
    """
    Планировщик задач для автоматического мониторинга сайтов
    """

    def __init__(self, bot: SiteMonitorBot):
        """
        Инициализация планировщика

        Args:
            bot (SiteMonitorBot): Экземпляр телеграм бота для отправки уведомлений
        """
        self.bot = bot
        self.database = bot.database
        self.monitor = bot.monitor

        # Настройка логирования
        self.logger = logging.getLogger(__name__)

    def register(self, application: Application):
        """
        Регистрирует периодическую проверку в job_queue приложения

        Args:
            application (Application): Приложение python-telegram-bot

        Raises:
            RuntimeError: Если job_queue недоступен
        """
        if application.job_queue is None:
            raise RuntimeError(
                "job_queue недоступен. Установите зависимости: "
                "python-telegram-bot[job-queue]"
            )

        application.job_queue.run_repeating(
            self.run_monitoring_check,
            interval=config.CHECK_INTERVAL_HOURS * 3600,
            first=config.FIRST_CHECK_DELAY_SECONDS,
            name=JOB_NAME
        )

        self.logger.info(
            f"Планировщик зарегистрирован: интервал {config.CHECK_INTERVAL_HOURS} ч, "
            f"первая проверка через {config.FIRST_CHECK_DELAY_SECONDS} с"
        )

    async def run_monitoring_check(self, context: ContextTypes.DEFAULT_TYPE):
        """
        Выполняет проверку всех активных сайтов

        Вызывается job_queue по расписанию.

        Args:
            context (ContextTypes.DEFAULT_TYPE): Контекст задачи
        """
        try:
            self.logger.info("Запускаю плановую проверку сайтов...")

            active_sites = self.database.get_active_sites()

            if not active_sites:
                self.logger.info("Нет активных сайтов для проверки")
                return

            # Проверки блокирующие, поэтому уводим их из event loop в поток
            results = await asyncio.to_thread(self.monitor.check_all_sites)

            # Отправляем уведомления пользователям
            await self._send_notifications(context, results)

            self.logger.info(
                f"Плановая проверка завершена. Результаты: OK={len(results['ok'])}, "
                f"Errors={len(results['error'])}, Changed={len(results['changed'])}"
            )

        except Exception as e:
            self.logger.error(f"Ошибка при плановой проверке: {str(e)}")

    async def _send_notifications(self, context: ContextTypes.DEFAULT_TYPE,
                                  results: Dict[str, List]):
        """
        Отправляет уведомления пользователям о результатах проверки

        Args:
            context (ContextTypes.DEFAULT_TYPE): Контекст задачи
            results (Dict[str, List]): Результаты проверки
        """
        # Раскладываем по владельцам только события - смену состояния сайта.
        # Сайт, который как работал, так и работает (или как лежал, так и
        # лежит), повторно не упоминаем, иначе уведомления превращаются в спам
        results_by_user = {}

        for status, entries in results.items():
            for entry in entries:
                user_id = entry['site'].get('user_id')
                if user_id is None:
                    continue

                event = self._detect_event(status, entry['site'].get('last_status'))
                if event is None:
                    continue

                user_results = results_by_user.setdefault(
                    user_id, {'down': [], 'recovered': [], 'changed': []}
                )
                user_results[event].append(entry)

        for user_id, user_results in results_by_user.items():
            notification = self._format_user_notification(user_results)

            if not notification:
                continue

            try:
                for part in split_message(notification):
                    await context.bot.send_message(chat_id=user_id, text=part)
                self.logger.info(f"Уведомление отправлено пользователю {user_id}")
            except Exception as e:
                self.logger.error(
                    f"Ошибка при отправке уведомления пользователю {user_id}: {str(e)}"
                )

    @staticmethod
    def _detect_event(status: str, previous_status: Optional[str]) -> Optional[str]:
        """
        Определяет, о каком событии стоит сообщить владельцу сайта

        Args:
            status (str): Результат текущей проверки ('ok', 'error', 'changed')
            previous_status (str): Статус из базы до проверки (или None)

        Returns:
            str: 'down', 'recovered', 'changed' или None, если сообщать не о чем
        """
        if status == 'error':
            return 'down' if previous_status != 'error' else None

        if status == 'changed':
            return 'changed'

        return 'recovered' if previous_status == 'error' else None

    def _format_user_notification(self, user_results: Dict[str, List]) -> str:
        """
        Формирует текст уведомления для пользователя

        Args:
            user_results (Dict[str, List]): События пользователя по типам

        Returns:
            str: Текст уведомления или пустая строка если нечего уведомлять
        """
        sections = [
            ('down', "❌ Сайт перестал работать:", True),
            ('recovered', "✅ Сайт снова работает:", False),
            ('changed', "🔄 Изменился контент:", True),
        ]

        notification = ""

        for event, title, with_message in sections:
            if not user_results[event]:
                continue

            notification += f"{title}\n"
            for result in user_results[event]:
                site = result['site']
                line = f"  • {site['name']}"
                if with_message:
                    line += f": {result['message']}"
                notification += f"{line}\n"
            notification += "\n"

        if not notification:
            return ""

        return "🔔 Мониторинг сайтов\n\n" + notification.rstrip()
