#!/usr/bin/env python3
"""
Скрипт для проверки версии telegram_bot.py на сервере
"""

def main():
    print("🔍 Проверка telegram_bot.py на сервере")
    print("=" * 60)
    print()
    
    print("📋 Команды для выполнения на сервере:")
    print("=" * 60)
    print()
    
    print("1. Проверьте, есть ли метод check_site_availability в telegram_bot.py:")
    print("   grep -n 'check_site_availability' telegram_bot.py")
    print()
    
    print("2. Проверьте, есть ли метод check_site_availability в site_monitor.py:")
    print("   grep -n 'check_site_availability' site_monitor.py")
    print()
    
    print("3. Посмотрим на метод add_site в telegram_bot.py:")
    print("   grep -A 10 -B 5 'check_site_availability' telegram_bot.py")
    print()
    
    print("4. Проверьте версию файла telegram_bot.py:")
    print("   ls -la telegram_bot.py")
    print()
    
    print("=" * 60)
    print("🚨 Проблема:")
    print("=" * 60)
    print()
    print("telegram_bot.py пытается использовать метод check_site_availability")
    print("которого нет в site_monitor.py на сервере")
    print()
    
    print("💡 Решение:")
    print("=" * 60)
    print()
    print("1. Обновите все файлы на сервере:")
    print("   git pull origin master")
    print()
    print("2. Перезапустите контейнер:")
    print("   docker-compose restart")
    print()
    print("3. Проверьте, что все файлы обновились:")
    print("   grep -n 'check_site_availability' site_monitor.py")
    print("   grep -n 'check_site_availability' telegram_bot.py")
    print()
    
    print("=" * 60)
    print("🎯 Альтернативное решение:")
    print("=" * 60)
    print()
    print("Если git pull не помогает, скопируйте файлы вручную:")
    print()
    print("1. Скопируйте site_monitor.py на сервер:")
    print("   scp site_monitor.py root@your-server:/home/chanki/")
    print()
    print("2. Скопируйте telegram_bot.py на сервер:")
    print("   scp telegram_bot.py root@your-server:/home/chanki/")
    print()
    print("3. Перезапустите контейнер:")
    print("   docker-compose restart")
    print()

if __name__ == "__main__":
    main()
