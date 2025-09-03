#!/usr/bin/env python3
"""
Скрипт для проверки кода внутри контейнера
"""

def main():
    print("🔍 Проверка кода внутри контейнера")
    print("=" * 60)
    print()
    
    print("📋 Команды для выполнения на сервере:")
    print("=" * 60)
    print()
    
    print("1. Проверьте, есть ли метод в контейнере:")
    print("   docker exec site-monitor-bot grep -n 'check_site_availability' /app/site_monitor.py")
    print()
    
    print("2. Проверьте, как инициализируется SiteMonitor в контейнере:")
    print("   docker exec site-monitor-bot grep -A 5 -B 5 'SiteMonitor' /app/telegram_bot.py")
    print()
    
    print("3. Проверьте версии файлов в контейнере:")
    print("   docker exec site-monitor-bot ls -la /app/telegram_bot.py")
    print("   docker exec site-monitor-bot ls -la /app/site_monitor.py")
    print()
    
    print("4. Проверьте, есть ли ошибки в коде контейнера:")
    print("   docker exec site-monitor-bot python -m py_compile /app/telegram_bot.py")
    print("   docker exec site-monitor-bot python -m py_compile /app/site_monitor.py")
    print()
    
    print("=" * 60)
    print("🚨 Возможная проблема:")
    print("=" * 60)
    print()
    print("Контейнер может использовать старую версию кода")
    print("или кэшированную версию Python модулей")
    print()
    
    print("💡 Решение:")
    print("=" * 60)
    print()
    print("1. Пересоберите контейнер:")
    print("   docker-compose down")
    print("   docker-compose build --no-cache")
    print("   docker-compose up -d")
    print()
    
    print("2. Или принудительно перезапустите:")
    print("   docker-compose restart")
    print()
    
    print("3. Проверьте логи после перезапуска:")
    print("   docker logs --tail 30 site-monitor-bot")
    print()
    
    print("=" * 60)
    print("🎯 Альтернативное решение:")
    print("=" * 60)
    print()
    print("Если проблема не решается, временно отключите проверку:")
    print()
    print("1. Отредактируйте файл в контейнере:")
    print("   docker exec -it site-monitor-bot nano /app/telegram_bot.py")
    print()
    print("2. Найдите строку с check_site_availability и замените её:")
    print("   # is_available, availability_message = self.monitor.check_site_availability(url)")
    print("   is_available, availability_message = True, 'Проверка отключена'")
    print()
    print("3. Сохраните файл (Ctrl+X, Y, Enter)")
    print()
    print("4. Перезапустите контейнер:")
    print("   docker-compose restart")
    print()

if __name__ == "__main__":
    main()
