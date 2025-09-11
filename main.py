"""
Главный файл приложения для мониторинга сайтов
Объединяет все модули и запускает систему мониторинга
"""
import signal
import sys
import logging
from datetime import datetime
import config
from database import SitesDatabase
from site_monitor import SiteMonitor
from telegram_bot import SiteMonitorBot
from scheduler import MonitoringScheduler

class SiteMonitoringApp:
    """
    Главный класс приложения для мониторинга сайтов
    """
    
    def __init__(self):
        """Инициализация приложения"""
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Инициализация приложения мониторинга сайтов...")
        
        # Инициализируем компоненты
        try:
            self.database = SitesDatabase()
            self.monitor = SiteMonitor(self.database)
            self.bot = SiteMonitorBot()
            self.scheduler = MonitoringScheduler(self.bot)
            # Свяжем бота с планировщиком, чтобы команда /interval могла перепланировать задачи
            self.bot.scheduler = self.scheduler
            
            self.logger.info("Все компоненты успешно инициализированы")
            
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации: {str(e)}")
            sys.exit(1)
        
        # Настройка обработчиков сигналов для корректного завершения
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """Настройка системы логирования"""
        # Создаем директорию для логов если её нет
        import os
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
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
    
    def signal_handler(self, signum, frame):
        """
        Обработчик сигналов для корректного завершения приложения
        
        Args:
            signum: Номер сигнала
            frame: Текущий кадр стека
        """
        self.logger.info(f"Получен сигнал {signum}, завершаю работу...")
        self.shutdown()
        sys.exit(0)
    
    def startup(self):
        """Запуск приложения"""
        try:
            self.logger.info("Запуск приложения мониторинга сайтов...")
            
            # Проверяем конфигурацию
            if not config.TELEGRAM_BOT_TOKEN:
                raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле")
            
            # Запускаем планировщик
            self.scheduler.start_scheduler()
            self.logger.info("Планировщик запущен")
            
            # Запускаем телеграм бота
            self.logger.info("Запуск телеграм бота...")
            self.bot.run()
            
        except Exception as e:
            self.logger.error(f"Ошибка при запуске: {str(e)}")
            self.shutdown()
            sys.exit(1)
    
    def shutdown(self):
        """Корректное завершение приложения"""
        try:
            self.logger.info("Завершение работы приложения...")
            
            # Останавливаем планировщик
            if hasattr(self, 'scheduler'):
                self.scheduler.stop_scheduler()
                self.logger.info("Планировщик остановлен")
            
            # Останавливаем бота
            if hasattr(self, 'bot') and self.bot.application:
                self.bot.application.stop()
                self.logger.info("Телеграм бот остановлен")
            
            self.logger.info("Приложение корректно завершено")
            
        except Exception as e:
            self.logger.error(f"Ошибка при завершении: {str(e)}")

def main():
    """Главная функция приложения"""
    print("🚀 Запуск приложения мониторинга сайтов...")
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ Интервал проверки: каждые {config.get_check_interval_hours()} часов")
    print(f"📁 База данных: {config.SITES_DATABASE_FILE}")
    print(f"📝 Логи: {config.LOG_FILE}")
    print("=" * 60)
    
    # Создаем и запускаем приложение
    app = SiteMonitoringApp()
    
    try:
        app.startup()
    except KeyboardInterrupt:
        print("\n⚠️ Получен сигнал прерывания, завершаю работу...")
        app.shutdown()
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        app.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()

