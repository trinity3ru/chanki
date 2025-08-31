"""
Модуль планировщика задач для автоматической проверки сайтов
Запускает проверку каждые 6 часов и отправляет уведомления в Telegram
"""
import schedule
import time
import threading
from datetime import datetime
import logging
from typing import Dict, List
import config
from database import SitesDatabase
from site_monitor import SiteMonitor
from telegram_bot import SiteMonitorBot
import asyncio

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
        self.running = False
        
        # Настройка логирования
        self.logger = logging.getLogger(__name__)
        
        # Словарь для отслеживания последних уведомлений об ошибках
        self.last_error_notifications = {}
    
    def start_scheduler(self):
        """Запускает планировщик задач"""
        if self.running:
            self.logger.warning("Планировщик уже запущен!")
            return
        
        self.running = True
        self.logger.info("Запускаю планировщик мониторинга...")
        
        # Планируем задачу каждые 6 часов
        schedule.every(config.CHECK_INTERVAL_HOURS).hours.do(self.run_monitoring_check)
        
        # Запускаем планировщик в отдельном потоке
        scheduler_thread = threading.Thread(target=self._run_scheduler_loop, daemon=True)
        scheduler_thread.start()
        
        self.logger.info(f"Планировщик запущен. Следующая проверка через {config.CHECK_INTERVAL_HOURS} часов")
    
    def stop_scheduler(self):
        """Останавливает планировщик задач"""
        self.running = False
        schedule.clear()
        self.logger.info("Планировщик остановлен")
    
    def _run_scheduler_loop(self):
        """Основной цикл планировщика"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Проверяем каждую минуту
    
    def run_monitoring_check(self):
        """
        Выполняет проверку всех активных сайтов
        Эта функция вызывается планировщиком каждые 6 часов
        """
        try:
            self.logger.info("Запускаю плановую проверку сайтов...")
            
            # Получаем все активные сайты
            active_sites = self.database.get_active_sites()
            
            if not active_sites:
                self.logger.info("Нет активных сайтов для проверки")
                return
            
            # Группируем сайты по пользователям для отправки уведомлений
            sites_by_user = {}
            for site in active_sites:
                user_id = site.get('user_id')
                if user_id:
                    if user_id not in sites_by_user:
                        sites_by_user[user_id] = []
                    sites_by_user[user_id].append(site)
            
            # Проверяем все сайты
            results = self.monitor.check_all_sites()
            
            # Отправляем уведомления пользователям
            self._send_notifications_to_users(sites_by_user, results)
            
            self.logger.info(f"Плановая проверка завершена. Результаты: OK={len(results['ok'])}, Errors={len(results['error'])}, Changed={len(results['changed'])}")
            
        except Exception as e:
            self.logger.error(f"Ошибка при плановой проверке: {str(e)}")
    
    def _send_notifications_to_users(self, sites_by_user: Dict[int, List], results: Dict[str, List]):
        """
        Отправляет уведомления пользователям о результатах проверки
        
        Args:
            sites_by_user (Dict[int, List]): Сайты, сгруппированные по пользователям
            results (Dict[str, List]): Результаты проверки
        """
        for user_id, user_sites in sites_by_user.items():
            try:
                # Фильтруем результаты для конкретного пользователя
                user_results = {
                    'ok': [r for r in results['ok'] if r['site']['user_id'] == user_id],
                    'error': [r for r in results['error'] if r['site']['user_id'] == user_id],
                    'changed': [r for r in results['changed'] if r['site']['user_id'] == user_id]
                }
                
                # Формируем уведомление для пользователя
                notification = self._format_user_notification(user_results)
                
                # Отправляем уведомление
                if notification:
                    self._send_telegram_notification(user_id, notification)
                
            except Exception as e:
                self.logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {str(e)}")
    
    def _format_user_notification(self, user_results: Dict[str, List]) -> str:
        """
        Формирует текст уведомления для пользователя
        
        Args:
            user_results (Dict[str, List]): Результаты проверки для пользователя
            
        Returns:
            str: Текст уведомления или пустая строка если нечего уведомлять
        """
        total_sites = sum(len(sites) for sites in user_results.values())
        
        if total_sites == 0:
            return ""
        
        notification = f"🔔 Результаты проверки сайтов ({total_sites}):\n\n"
        
        # Добавляем информацию об ошибках
        if user_results['error']:
            notification += "❌ Проблемы с сайтами:\n"
            for result in user_results['error']:
                site = result['site']
                notification += f"  • {site['name']}: {result['message']}\n"
            notification += "\n"
        
        # Добавляем информацию об изменениях
        if user_results['changed']:
            notification += "🔄 Сайты с изменениями:\n"
            for result in user_results['changed']:
                site = result['site']
                notification += f"  • {site['name']}: {result['message']}\n"
            notification += "\n"
        
        # Добавляем общую статистику
        working_sites = len(user_results['ok'])
        if working_sites > 0:
            notification += f"✅ Работают нормально: {working_sites} сайтов\n"
        
        notification += f"\n🕐 Следующая проверка через {config.CHECK_INTERVAL_HOURS} часов"
        
        return notification
    
    def _send_telegram_notification(self, user_id: int, message: str):
        """
        Отправляет уведомление в Telegram пользователю
        
        Args:
            user_id (int): ID пользователя в Telegram
            message (str): Текст уведомления
        """
        try:
            # Используем бота для отправки сообщения
            if self.bot.application:
                asyncio.run(self.bot.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                ))
                self.logger.info(f"Уведомление отправлено пользователю {user_id}")
            else:
                self.logger.warning("Бот не инициализирован, не могу отправить уведомление")
                
        except Exception as e:
            self.logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {str(e)}")
    
    def run_manual_check(self):
        """
        Запускает проверку вручную (для тестирования)
        """
        self.logger.info("Запускаю ручную проверку...")
        self.run_monitoring_check()
    
    def get_next_check_time(self) -> str:
        """
        Возвращает время следующей запланированной проверки
        
        Returns:
            str: Время следующей проверки в читаемом формате
        """
        next_run = schedule.next_run()
        if next_run:
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return "Не запланировано"
    
    def get_scheduler_status(self) -> Dict:
        """
        Возвращает статус планировщика
        
        Returns:
            Dict: Информация о статусе планировщика
        """
        return {
            'running': self.running,
            'next_check': self.get_next_check_time(),
            'check_interval_hours': config.CHECK_INTERVAL_HOURS,
            'active_sites_count': len(self.database.get_active_sites())
        }

