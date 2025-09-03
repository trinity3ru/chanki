"""
Telegram бот для управления мониторингом сайтов
Предоставляет интерфейс для добавления, удаления и просмотра сайтов
"""
import logging
import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from typing import Dict, List
import config
from database import SitesDatabase
from site_monitor import SiteMonitor

class SiteMonitorBot:
    """
    Telegram бот для управления мониторингом сайтов
    """
    
    def __init__(self):
        """Инициализация бота"""
        self.database = SitesDatabase()
        self.monitor = SiteMonitor(self.database)
        self.application = None
        
        # Настройка логирования
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /start
        
        Args:
            update (Update): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or "Пользователь"
        
        welcome_text = f"👋 Привет, {username}!\n\n"
        welcome_text += "🤖 Я бот для мониторинга сайтов.\n"
        welcome_text += "Я буду проверять доступность ваших сайтов каждые 6 часов.\n\n"
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
        help_text += "💡 Сайты проверяются автоматически каждые 6 часов"
        
        await update.message.reply_text(help_text)
    
    async def add_site(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /add для добавления сайта
        Проверяет доступность сайта перед добавлением в базу данных
        
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
        
        # Отправляем сообщение о начале проверки
        checking_msg = await update.message.reply_text(
            f"🔍 Проверяю доступность сайта...\n"
            f"🌐 {name}\n"
            f"🔗 {url}\n\n"
            f"⏳ Пожалуйста, подождите..."
        )
        
        try:
            # Проверяем доступность сайта перед добавлением
            is_available, availability_message, content = self.monitor.check_site_availability(url)
            
            if not is_available:
                # Сайт недоступен - не добавляем и показываем ошибку
                await checking_msg.edit_text(
                    f"❌ Сайт недоступен!\n\n"
                    f"🌐 Название: {name}\n"
                    f"🔗 URL: {url}\n\n"
                    f"🚨 Ошибка: {availability_message}\n\n"
                    f"💡 Проверьте URL и попробуйте снова"
                )
                return
            
            # Сайт доступен - показываем результат и даем выбор
            if "⚠️ Мало контента" in availability_message:
                # Мало контента - показываем пользователю и даем выбор
                content_preview = content[:200] + "..." if len(content) > 200 else content
                
                message_text = (
                    f"⚠️ Сайт доступен, но контент небольшой!\n\n"
                    f"🌐 Название: {name}\n"
                    f"🔗 URL: {url}\n\n"
                    f"📝 Контент ({len(content)} символов):\n"
                    f"\"{content_preview}\"\n\n"
                    f"💡 Хотите добавить этот сайт?\n"
                    f"• Да - сайт будет добавлен и отслеживаться\n"
                    f"• Нет - попробуйте другой URL"
                )
                
                # Создаем кнопки для выбора
                url_encoded = base64.b64encode(url.encode()).decode()
                name_encoded = base64.b64encode(name.encode()).decode()
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Да, добавить", callback_data=f"add_confirm_{url_encoded}_{name_encoded}"),
                        InlineKeyboardButton("❌ Нет, отменить", callback_data="add_cancel")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await checking_msg.edit_text(message_text, reply_markup=reply_markup)
                return
            
            # Сайт доступен с нормальным контентом - добавляем сразу
            success = self.database.add_site(url, name, user_id)
            
            if success:
                await checking_msg.edit_text(
                    f"✅ Сайт успешно добавлен!\n\n"
                    f"🌐 Название: {name}\n"
                    f"🔗 URL: {url}\n\n"
                    f"✅ Проверка доступности: {availability_message}\n\n"
                    f"📊 Сайт будет проверяться каждые 6 часов"
                )
            else:
                await checking_msg.edit_text(
                    f"❌ Ошибка! Сайт {url} уже существует в базе данных.\n\n"
                    f"💡 Используйте /list чтобы увидеть все ваши сайты"
                )
                
        except Exception as e:
            # Обработка неожиданных ошибок
            await checking_msg.edit_text(
                f"❌ Произошла ошибка при проверке сайта!\n\n"
                f"🌐 Название: {name}\n"
                f"🔗 URL: {url}\n\n"
                f"🚨 Ошибка: {str(e)}\n\n"
                f"💡 Попробуйте позже или проверьте URL"
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
        sites_by_status = {'ok': [], 'error': [], 'changed': [], 'unknown': []}
        
        for site in user_sites:
            status = site.get('last_status', 'unknown')
            if status in sites_by_status:
                sites_by_status[status].append(site)
            else:
                sites_by_status['unknown'].append(site)
        
        # Формируем сообщение
        message = f"📋 Ваши сайты ({len(user_sites)}):\n\n"
        
        for status, sites in sites_by_status.items():
            if sites:
                status_emoji = {
                    'ok': '✅',
                    'error': '❌',
                    'changed': '🔄',
                    'unknown': '❓'
                }
                status_name = {
                    'ok': 'Работают',
                    'error': 'Ошибки',
                    'changed': 'Изменения',
                    'unknown': 'Не проверялись'
                }
                
                message += f"{status_emoji[status]} {status_name[status]}:\n"
                
                for site in sites:
                    message += f"  {site['id']}. {site['name']}\n"
                    message += f"     {site['url']}\n"
                
                message += "\n"
        
        message += "💡 Используйте /status для подробной информации"
        
        # Разбиваем длинное сообщение если нужно
        if len(message) > 4096:
            parts = [message[i:i+4096] for i in range(0, len(message), 4096)]
            for i, part in enumerate(parts):
                await update.message.reply_text(f"{part}\n\nЧасть {i+1}/{len(parts)}")
        else:
            await update.message.reply_text(message)
    
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
                "📝 Используйте: /remove <ID или URL>\n"
                "💡 Примеры:\n"
                "  /remove 1\n"
                "  /remove promineral.ru\n"
                "  /remove https://example.com\n\n"
                "🔍 Используйте /list чтобы увидеть ваши сайты"
            )
            return
        
        # Получаем аргумент (может быть ID или URL)
        arg = context.args[0]
        site = None
        
        # Сначала пробуем как ID
        try:
            site_id = int(arg)
            site = self.database.get_site_by_id(site_id)
            if site and site.get('user_id') != user_id:
                site = None  # Сайт не принадлежит пользователю
        except ValueError:
            # Если не число, ищем по URL
            user_sites = self.database.get_sites_by_user(user_id)
            for s in user_sites:
                # Проверяем точное совпадение URL или домена
                if (s['url'] == arg or 
                    s['url'] == f"https://{arg}" or 
                    s['url'] == f"http://{arg}" or
                    s['name'] == arg):
                    site = s
                    break
        
        if not site:
            await update.message.reply_text(
                f"❌ Сайт '{arg}' не найден или не принадлежит вам!\n\n"
                "💡 Проверьте:\n"
                "  • Правильность ID или URL\n"
                "  • Что сайт добавлен вами\n"
                "  • Используйте /list для просмотра ваших сайтов"
            )
            return
        
        # Удаляем сайт
        success = self.database.remove_site(site['id'])
        
        if success:
            await update.message.reply_text(
                f"✅ Сайт '{site['name']}' успешно удален!"
            )
        else:
            await update.message.reply_text(
                f"❌ Ошибка при удалении сайта '{site['name']}'"
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
        
        # Разбиваем длинное сообщение если нужно
        if len(message) > 4096:
            parts = [message[i:i+4096] for i in range(0, len(message), 4096)]
            for i, part in enumerate(parts):
                await update.message.reply_text(f"{part}\n\nЧасть {i+1}/{len(parts)}")
        else:
            await update.message.reply_text(message)
    
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
            # Проверяем только сайты пользователя
            results = {'ok': [], 'error': [], 'changed': []}
            
            for site in user_sites:
                if site.get('is_active', True):
                    status, message, content_hash = self.monitor.check_site(site)
                    results[status].append({
                        'site': site,
                        'message': message,
                        'content_hash': content_hash
                    })
            
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
            
            await update.message.reply_text(report)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при проверке: {str(e)}")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик нажатий на кнопки
        
        Args:
            update (Update): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data == "add_cancel":
            # Пользователь отменил добавление
            await query.edit_message_text("❌ Добавление сайта отменено.")
            return
        
        if data.startswith("add_confirm_"):
            # Пользователь подтвердил добавление сайта с малым контентом
            try:
                # Извлекаем URL и имя из callback_data
                parts = data.split("_", 2)
                if len(parts) >= 3:
                    url_encoded = parts[2]
                    name_encoded = parts[3] if len(parts) > 3 else url_encoded
                    
                    # Декодируем URL и имя
                    url = base64.b64decode(url_encoded.encode()).decode()
                    name = base64.b64decode(name_encoded.encode()).decode()
                    
                    # Добавляем сайт в базу данных
                    success = self.database.add_site(url, name, user_id)
                    
                    if success:
                        await query.edit_message_text(
                            f"✅ Сайт успешно добавлен!\n\n"
                            f"🌐 Название: {name}\n"
                            f"🔗 URL: {url}\n\n"
                            f"⚠️ Сайт добавлен с предупреждением о малом контенте\n\n"
                            f"📊 Сайт будет проверяться каждые 6 часов"
                        )
                    else:
                        await query.edit_message_text(
                            f"❌ Ошибка! Сайт {url} уже существует в базе данных.\n\n"
                            f"💡 Используйте /list чтобы увидеть все ваши сайты"
                        )
                else:
                    await query.edit_message_text("❌ Ошибка при обработке данных.")
            except Exception as e:
                await query.edit_message_text(f"❌ Ошибка при добавлении сайта: {str(e)}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик ошибок бота
        
        Args:
            update (object): Обновление от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        self.logger.error(f"Exception while handling an update: {context.error}")
    
    def run(self):
        """Запуск бота"""
        # Создаем приложение
        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("add", self.add_site))
        self.application.add_handler(CommandHandler("list", self.list_sites))
        self.application.add_handler(CommandHandler("remove", self.remove_site))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("check", self.check_now))
        
        # Добавляем обработчик кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Добавляем обработчик ошибок
        self.application.add_error_handler(self.error_handler)
        
        # Запускаем бота
        self.logger.info("Запускаю бота...")
        self.application.run_polling()
