#!/usr/bin/env python3
"""
Скрипт для исправления отсутствующего метода check_site_availability
"""

def main():
    print("🔧 Исправление отсутствующего метода check_site_availability")
    print("=" * 60)
    print()
    
    print("📋 Команды для выполнения на сервере:")
    print("=" * 60)
    print()
    
    print("1. Проверьте, есть ли метод в site_monitor.py:")
    print("   grep -n 'check_site_availability' site_monitor.py")
    print()
    
    print("2. Если метода нет, посмотрим на структуру site_monitor.py:")
    print("   grep -n 'def ' site_monitor.py")
    print()
    
    print("3. Проверьте, есть ли метод в GitHub версии:")
    print("   git show HEAD:site_monitor.py | grep -n 'check_site_availability'")
    print()
    
    print("=" * 60)
    print("🚨 Проблема:")
    print("=" * 60)
    print()
    print("telegram_bot.py вызывает self.monitor.check_site_availability(url)")
    print("но этого метода нет в site_monitor.py на сервере")
    print()
    
    print("💡 Решение:")
    print("=" * 60)
    print()
    print("1. Обновите site_monitor.py на сервере:")
    print("   git pull origin master")
    print()
    print("2. Если не помогает, скопируйте файл вручную:")
    print("   scp site_monitor.py root@your-server:/home/chanki/")
    print()
    print("3. Перезапустите контейнер:")
    print("   docker-compose restart")
    print()
    
    print("=" * 60)
    print("🎯 Альтернативное решение:")
    print("=" * 60)
    print()
    print("Если метод действительно отсутствует, можно временно отключить проверку:")
    print()
    print("1. Отредактируйте telegram_bot.py на сервере:")
    print("   nano telegram_bot.py")
    print()
    print("2. Найдите строку 113 и закомментируйте её:")
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
