#!/usr/bin/env python3
"""
Скрипт для диагностики проблемы с инициализацией
"""

def main():
    print("🔍 Диагностика проблемы с инициализацией")
    print("=" * 60)
    print()
    
    print("📋 Команды для выполнения на сервере:")
    print("=" * 60)
    print()
    
    print("1. Проверьте логи приложения:")
    print("   docker logs --tail 20 site-monitor-bot")
    print()
    
    print("2. Проверьте, как инициализируется SiteMonitor в telegram_bot.py:")
    print("   grep -A 5 -B 5 'SiteMonitor' telegram_bot.py")
    print()
    
    print("3. Проверьте импорты в telegram_bot.py:")
    print("   head -20 telegram_bot.py")
    print()
    
    print("4. Проверьте, есть ли ошибки в коде:")
    print("   python -m py_compile telegram_bot.py")
    print("   python -m py_compile site_monitor.py")
    print()
    
    print("5. Проверьте, что метод действительно существует:")
    print("   grep -A 10 'def check_site_availability' site_monitor.py")
    print()
    
    print("=" * 60)
    print("🚨 Возможные причины:")
    print("=" * 60)
    print()
    print("1. Ошибка при инициализации SiteMonitor")
    print("2. Проблема с импортами")
    print("3. Ошибка в коде Python")
    print("4. Проблема с версиями файлов")
    print()
    
    print("💡 Решение:")
    print("=" * 60)
    print()
    print("1. Перезапустите контейнер:")
    print("   docker-compose restart")
    print()
    print("2. Проверьте логи после перезапуска:")
    print("   docker logs --tail 30 site-monitor-bot")
    print()
    print("3. Если есть ошибки, исправьте их")
    print()
    
    print("=" * 60)
    print("🎯 Альтернативное решение:")
    print("=" * 60)
    print()
    print("Если проблема не решается, временно отключите проверку:")
    print()
    print("1. Отредактируйте telegram_bot.py:")
    print("   nano telegram_bot.py")
    print()
    print("2. Найдите строку 113 и замените её:")
    print("   # is_available, availability_message = self.monitor.check_site_availability(url)")
    print("   is_available, availability_message = True, 'Проверка отключена'")
    print()
    print("3. Сохраните и перезапустите:")
    print("   docker-compose restart")
    print()

if __name__ == "__main__":
    main()
