"""
Telegram бот для управления мониторингом сайтов
Предоставляет интерфейс для добавления, удаления и просмотра сайтов
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from typing import Dict, List
import config
from database import SitesDatabase
from site_monitor import SiteMonitor

# Telegram режет сообщения длиннее 4096 символов. Берем запас под суффикс
# "Часть N/M", который дописывается уже после нарезки
MESSAGE_CHUNK_LIMIT = 4000

# Отображение статусов последней проверки
STATUS_EMOJI = {
    'ok': '✅',
    'error': '❌',
    'changed': '🔄',
    'minor_change': '➖',
    'unknown': '❓'
}

STATUS_NAME = {
    'ok': 'Работают',
    'error': 'Ошибки',
    'changed': 'Изменения',
    'minor_change': 'Мелкие правки',
    'unknown': 'Не проверялись'
}


def split_message(text: str, limit: int = MESSAGE_CHUNK_LIMIT) -> List[str]:
    """
    Нарезает длинное сообщение на части, помещающиеся в лимит Telegram

    Args:
        text (str): Исходный текст
        limit (int): Максимальная длина одной части без суффикса

    Returns:
        List[str]: Готовые к отправке части сообщения
    """
    if len(text) <= limit:
        return [text]

    parts = [text[i:i + limit] for i in range(0, len(text), limit)]
    return [f"{part}\n\nЧасть {i}/{len(parts)}" for i, part in enumerate(parts, 1)]


class SiteMonitorBot:
    """
    Telegram бот для управления мониторингом сайтов
    """

    def __init__(self):
        """Инициализация бота"""
        self.database = SitesDatabase()
        self.monitor = SiteMonitor(self.database)
        self.application = None
        self.logger = logging.getLogger(__name__)

    async def _reply(self, update: Update, text: str):
        """
        Отправляет ответ пользователю, разбивая длинный текст на части

        Args:
            update (Update): Обновление от Telegram
            text (str): Текст ответа
        """
        for part in split_message(text):
            await update.message.reply_text(part)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /start

        Args:
            update (Update): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        username = update.effective_user.username or "Пользователь"

        welcome_text = f"👋 Привет, {username}!\n\n"
        welcome_text += "🤖 Я бот для мониторинга сайтов.\n"
        welcome_text += f"Я буду проверять доступность ваших сайтов каждые {config.CHECK_INTERVAL_HOURS} часов.\n\n"
        welcome_text += "📋 Доступные команды:\n"
        welcome_text += "/add - Добавить сайт для мониторинга\n"
        welcome_text += "/list - Показать все ваши сайты\n"
        welcome_text += "/remove - Удалить сайт\n"
        welcome_text += "/status - Статус всех сайтов\n"
        welcome_text += "/check - Запустить проверку сейчас\n"
        welcome_text += "/help - Показать справку\n\n"
        welcome_text += "💡 Чтобы добавить сайт, используйте команду /add"

        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /help

        Args:
            update (Update): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        help_text = "📚 Справка по командам:\n\n"
        help_text += "🔗 /add - Добавить сайт для мониторинга\n"
        help_text += "   Пример: /add https://example.com Название сайта\n\n"
        help_text += "📋 /list - Показать все ваши сайты\n\n"
        help_text += "🗑️ /remove - Удалить сайт по ID\n"
        help_text += "   Пример: /remove 1\n\n"
        help_text += "📊 /status - Показать статус всех сайтов\n\n"
        help_text += "🔍 /check - Запустить проверку всех сайтов сейчас\n\n"
        help_text += "❓ /help - Показать эту справку\n\n"
        help_text += f"💡 Сайты проверяются автоматически каждые {config.CHECK_INTERVAL_HOURS} часов"

        await update.message.reply_text(help_text)

    async def add_site(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /add для добавления сайта

        Args:
            update (Update): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        user_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text(
                "❌ Неверный формат команды!\n\n"
                "📝 Используйте: /add <URL> [название]\n"
                "💡 Пример: /add https://example.com Мой сайт"
            )
            return

        url = context.args[0]
        name = ' '.join(context.args[1:]) if len(context.args) > 1 else url

        # Простая валидация URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Добавляем сайт в базу данных
        success = self.database.add_site(url, name, user_id)

        if success:
            await update.message.reply_text(
                f"✅ Сайт успешно добавлен!\n\n"
                f"🌐 Название: {name}\n"
                f"🔗 URL: {url}\n\n"
                f"📊 Сайт будет проверяться каждые {config.CHECK_INTERVAL_HOURS} часов"
            )
        else:
            await update.message.reply_text(
                f"❌ Ошибка! Сайт {url} уже есть в вашем списке."
            )

    async def list_sites(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /list для показа списка сайтов

        Args:
            update (Update): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        user_id = update.effective_user.id
        user_sites = self.database.get_sites_by_user(user_id)

        if not user_sites:
            await update.message.reply_text(
                "📭 У вас пока нет добавленных сайтов.\n\n"
                "💡 Используйте команду /add чтобы добавить первый сайт!"
            )
            return

        # Группируем сайты по статусу
        sites_by_status = {status: [] for status in STATUS_NAME}

        for site in user_sites:
            status = site.get('last_status') or 'unknown'
            if status not in sites_by_status:
                status = 'unknown'
            sites_by_status[status].append(site)

        # Формируем сообщение
        message = f"📋 Ваши сайты ({len(user_sites)}):\n\n"

        for status, sites in sites_by_status.items():
            if not sites:
                continue

            message += f"{STATUS_EMOJI[status]} {STATUS_NAME[status]}:\n"

            for site in sites:
                message += f"  {site['id']}. {site['name']}\n"
                message += f"     {site['url']}\n"

            message += "\n"

        message += "💡 Используйте /status для подробной информации"

        await self._reply(update, message)

    async def remove_site(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /remove для удаления сайта

        Args:
            update (Update): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        user_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text(
                "❌ Неверный формат команды!\n\n"
                "📝 Используйте: /remove <ID>\n"
                "💡 Пример: /remove 1\n\n"
                "🔍 Используйте /list чтобы увидеть ID ваших сайтов"
            )
            return

        try:
            site_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ ID сайта должен быть числом!")
            return

        # Запоминаем название до удаления, чтобы показать его в ответе
        site = self.database.get_site_by_id(site_id)
        site_name = site['name'] if site else None

        # Удаление проверяет владельца: чужой сайт удалить нельзя
        if self.database.remove_site(site_id, user_id):
            await update.message.reply_text(
                f"✅ Сайт '{site_name}' успешно удален!"
            )
        else:
            await update.message.reply_text(
                f"❌ Сайт с ID {site_id} не найден или не принадлежит вам!"
            )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /status для показа статуса всех сайтов

        Args:
            update (Update): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        user_id = update.effective_user.id
        user_sites = self.database.get_sites_by_user(user_id)

        if not user_sites:
            await update.message.reply_text(
                "📭 У вас пока нет добавленных сайтов.\n\n"
                "💡 Используйте команду /add чтобы добавить первый сайт!"
            )
            return

        message = f"📊 Статус ваших сайтов ({len(user_sites)}):\n\n"

        for site in user_sites:
            message += self.monitor.get_site_summary(site)
            message += "\n" + "─" * 40 + "\n\n"

        await self._reply(update, message)

    def _check_user_sites(self, user_sites: List[Dict]) -> Dict[str, list]:
        """
        Синхронно проверяет сайты пользователя

        Вынесено в отдельный метод, чтобы выполняться в рабочем потоке:
        requests блокирующий, и в event loop бота ему делать нечего.

        Args:
            user_sites (List[Dict]): Сайты пользователя

        Returns:
            Dict[str, list]: Результаты проверки по категориям
        """
        results = {'ok': [], 'error': [], 'changed': []}

        for site in user_sites:
            if not site.get('is_active', True):
                continue

            status, message, content_hash = self.monitor.check_site(site)
            results[status].append({
                'site': site,
                'message': message,
                'content_hash': content_hash
            })

        return results

    async def check_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /check для запуска проверки сейчас

        Args:
            update (Update): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        user_id = update.effective_user.id
        user_sites = self.database.get_sites_by_user(user_id)

        if not user_sites:
            await update.message.reply_text(
                "📭 У вас пока нет добавленных сайтов для проверки."
            )
            return

        # Запускаем проверку
        await update.message.reply_text("🔍 Запускаю проверку ваших сайтов...")

        try:
            results = await asyncio.to_thread(self._check_user_sites, user_sites)

            # Формируем отчет
            report = f"📊 Результаты проверки ({len(user_sites)} сайтов):\n\n"
            report += f"✅ Работают: {len(results['ok'])}\n"
            report += f"❌ Ошибки: {len(results['error'])}\n"
            report += f"🔄 Изменения: {len(results['changed'])}\n\n"

            if results['error']:
                report += "❌ Сайты с ошибками:\n"
                for result in results['error']:
                    report += f"  • {result['site']['name']}: {result['message']}\n"
                report += "\n"

            if results['changed']:
                report += "🔄 Сайты с изменениями:\n"
                for result in results['changed']:
                    report += f"  • {result['site']['name']}: {result['message']}\n"
                report += "\n"

            await self._reply(update, report)

        except Exception as e:
            self.logger.error(f"Ошибка при ручной проверке: {str(e)}")
            await update.message.reply_text(f"❌ Ошибка при проверке: {str(e)}")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик ошибок бота

        Args:
            update (object): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        self.logger.error(f"Exception while handling an update: {context.error}")

    def build(self) -> Application:
        """
        Собирает приложение бота и регистрирует обработчики

        Returns:
            Application: Готовое приложение python-telegram-bot
        """
        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("add", self.add_site))
        self.application.add_handler(CommandHandler("list", self.list_sites))
        self.application.add_handler(CommandHandler("remove", self.remove_site))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("check", self.check_now))

        # Добавляем обработчик ошибок
        self.application.add_error_handler(self.error_handler)

        return self.application

    def run(self):
        """
        Запуск бота

        run_polling сам ставит обработчики SIGINT/SIGTERM и корректно
        останавливает приложение вместе с job_queue.
        """
        if self.application is None:
            self.build()

        self.logger.info("Запускаю бота...")
        self.application.run_polling()
